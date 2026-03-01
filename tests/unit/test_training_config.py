"""Tests for the weekend fine-tuning training configuration.

Validates VSP-LLM/src/conf/vsp-llm-avspeech-weekend.yaml.
"""

import os

import pytest
import yaml

CONFIG_PATH = "/home/ubuntu/VSP-LLM/src/conf/vsp-llm-avspeech-weekend.yaml"


@pytest.fixture(scope="module")
def config():
    """Load and parse the YAML config."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def test_yaml_parses(config):
    """Config file parses without errors."""
    assert config is not None
    assert isinstance(config, dict)


def test_single_gpu_settings(config):
    """Distributed settings configured for single GPU."""
    dist = config["distributed_training"]
    assert dist["distributed_world_size"] == 1
    assert dist["nprocs_per_node"] == 1


def test_gradient_accumulation(config):
    """Gradient accumulation set to 8 for effective batch size 8."""
    update_freq = config["optimization"]["update_freq"]
    assert update_freq == [8], f"Expected [8], got {update_freq}"


def test_max_update(config):
    """Max update set to 3000 for weekend training."""
    assert config["optimization"]["max_update"] == 3000


def test_learning_rate(config):
    """Learning rate is conservative 3e-4."""
    lr = config["optimization"]["lr"]
    assert lr == [0.0003], f"Expected [0.0003], got {lr}"


def test_encoder_frozen(config):
    """Encoder frozen throughout (freeze_finetune_updates very high)."""
    freeze = config["model"]["freeze_finetune_updates"]
    assert freeze >= 999999, f"Expected >= 999999, got {freeze}"


def test_lr_schedule_proportional(config):
    """Warmup + decay should cover max_update."""
    warmup = config["lr_scheduler"]["warmup_steps"]
    decay = config["lr_scheduler"]["decay_steps"]
    max_update = config["optimization"]["max_update"]
    assert warmup + decay == max_update, (
        f"warmup ({warmup}) + decay ({decay}) != max_update ({max_update})"
    )


def test_checkpoint_frequency(config):
    """Checkpoints saved frequently for weekend safety."""
    save_interval = config["checkpoint"]["save_interval_updates"]
    assert save_interval <= 500, f"Expected <= 500, got {save_interval}"
    keep = config["checkpoint"]["keep_interval_updates"]
    assert keep >= 5, f"Expected >= 5, got {keep}"


def test_fp16_enabled(config):
    """FP16 enabled for T4 GPU efficiency."""
    assert config["common"]["fp16"] is True


def test_required_placeholders(config):
    """All required fields that must be set via CLI are marked as ???."""
    assert config["common"]["user_dir"] == "???"
    assert config["task"]["data"] == "???"
    assert config["task"]["label_dir"] == "???"
    assert config["task"]["llm_ckpt_path"] == "???"
    assert config["model"]["w2v_path"] == "???"
    assert config["model"]["llm_ckpt_path"] == "???"


def test_batch_size(config):
    """Batch size is 1 (gradient accumulation handles effective batch)."""
    assert config["dataset"]["batch_size"] == 1


def test_valid_subset(config):
    """Validation subset matches our split naming convention."""
    assert config["dataset"]["valid_subset"] == "test"
    assert config["dataset"]["train_subset"] == "train"
