"""Smoke test: load Llama 3.1 8B (base) with the same 4-bit BnB config VSP-LLM uses,
apply our pad-token guard + LoRA, and run one forward pass with a dummy visual feature.
Validates that the transformers/peft/bitsandbytes chain works end-to-end with Llama 3
in the existing vsp-llm-yoad-venv before we burn p4d budget on it."""
import sys, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model

LLM_PATH = "/home/ubuntu/Llama-3.1-8B"
print(f"=== Llama 3.1 Base load test ({LLM_PATH}) ===")
print(f"torch={torch.__version__}  cuda={torch.cuda.is_available()}  device={torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}")
print(f"VRAM budget: {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB")
print()

# Step 1: tokenizer + pad-token guard (mirrors vsp_llm_dataset.py change)
t0 = time.time()
tokenizer = AutoTokenizer.from_pretrained(LLM_PATH)
print(f"Tokenizer loaded in {time.time()-t0:.1f}s")
print(f"  pad_token (pre-guard): {tokenizer.pad_token}  pad_token_id: {tokenizer.pad_token_id}")
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.pad_token_id = tokenizer.eos_token_id
print(f"  pad_token (post-guard): {tokenizer.pad_token}  pad_token_id: {tokenizer.pad_token_id}")
print(f"  vocab_size: {tokenizer.vocab_size}")
print()

# Step 2: 4-bit BnB load (mirrors vsp_llm.py build_model)
t0 = time.time()
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)
print("Loading 4-bit Llama 3.1 base (this is the slow step)...")
model = AutoModelForCausalLM.from_pretrained(LLM_PATH, quantization_config=bnb_config)
print(f"Model loaded in {time.time()-t0:.1f}s")
print(f"  hidden_size: {model.config.hidden_size}")
print(f"  vocab_size: {model.config.vocab_size}")
print(f"  eos_token_id (config): {model.config.eos_token_id}  (type: {type(model.config.eos_token_id).__name__})")
print(f"  pad_token_id (config, pre-guard): {model.config.pad_token_id}")

# Apply our pad-token guard (mirrors vsp_llm.py)
if model.config.pad_token_id is None:
    _eos = model.config.eos_token_id
    if isinstance(_eos, (list, tuple)):
        _eos = _eos[0]
    model.config.pad_token_id = _eos
print(f"  pad_token_id (config, post-guard): {model.config.pad_token_id}")
print(f"  VRAM after load: {torch.cuda.memory_allocated()/1e9:.2f} GB")
print()

# Step 3: Wrap with LoRA (mirrors vsp_llm.py)
t0 = time.time()
lora_config = LoraConfig(
    r=16, lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj"],
    lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)
print(f"LoRA applied in {time.time()-t0:.1f}s")
model.print_trainable_parameters()
print(f"  VRAM after LoRA: {torch.cuda.memory_allocated()/1e9:.2f} GB")
print()

# Step 4: Mock VSP-LLM forward: instruction + visual features (1024->4096 projected) + label
print("Mock forward pass with projected visual features...")
device = next(model.parameters()).device
avfeat_to_llm = torch.nn.Linear(1024, 4096).to(device=device, dtype=torch.bfloat16)

# Mock visual features (B=1, T=30 visual tokens, D=1024 from AV-HuBERT)
visual_features = torch.randn(1, 30, 1024, device=device, dtype=torch.bfloat16)
projected_visual = avfeat_to_llm(visual_features)  # (1, 30, 4096)
print(f"  Projected visual shape: {projected_visual.shape}")

# Mock instruction + label tokens
instruction = tokenizer("Recognize this speech in English. Input: ", return_tensors="pt").input_ids.to(device)
label = tokenizer("hello world", return_tensors="pt").input_ids.to(device)
print(f"  Instruction tokens: {instruction.shape}, label tokens: {label.shape}")

# Embed text portions and concatenate (mirrors vsp_llm.py:333-338)
instruction_emb = model.model.model.embed_tokens(instruction)
label_emb = model.model.model.embed_tokens(label)
llm_input = torch.cat([instruction_emb, projected_visual, label_emb], dim=1)
print(f"  LLM input shape: {llm_input.shape}")

# Build labels with the same pad-mask logic as vsp_llm.py
B, T, D = projected_visual.shape
_, instruction_t, _ = instruction_emb.size()
llm_labels = label.clone()
_pad_id = model.config.pad_token_id
llm_labels[llm_labels == _pad_id] = -100
target_ids = torch.full((B, T + instruction_t), -100).long().to(device)
llm_labels = torch.cat([target_ids, llm_labels], dim=1)
print(f"  LLM labels shape: {llm_labels.shape}  (pad_id={_pad_id} masked)")

t0 = time.time()
# Wrap with autocast(bfloat16) — fairseq's fp16 system does the equivalent in production,
# so this matches the real training/decode path's dtype handling.
with torch.no_grad(), torch.autocast(device_type='cuda', dtype=torch.bfloat16):
    out = model(inputs_embeds=llm_input, labels=llm_labels, return_dict=True)
print(f"Forward in {time.time()-t0:.2f}s")
print(f"  loss: {out.loss.item():.4f}  logits: {out.logits.shape}  dtype: {out.logits.dtype}")
print(f"  VRAM at forward: {torch.cuda.memory_allocated()/1e9:.2f} GB / peak {torch.cuda.max_memory_allocated()/1e9:.2f} GB")
print()
print("=== LOAD TEST PASSED ===")
