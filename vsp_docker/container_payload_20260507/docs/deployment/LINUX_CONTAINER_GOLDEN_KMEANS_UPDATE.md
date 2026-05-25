# Golden K-means Models Feature - Linux Container Deployment Guide

**Feature:** Save and reuse pre-trained k-means models across pipeline runs
**Date Added:** January 25, 2026
**EC2 Version:** Fully implemented and tested
**Linux Container:** Requires deployment (follow this guide)

---

## Overview

This feature allows users to:
1. Train k-means on a curated set of videos **once** (e.g., 500 videos)
2. Save the trained model as a "golden" model
3. Reuse that model in future runs without retraining
4. Select from multiple saved models via the web UI

**Time Savings:** 10-30 minutes per pipeline run (depending on dataset size)

---

## Architecture Summary

### Storage Structure
```
/workspace/VSP-LLM/golden_kmeans/
├── 500videos_jan25.bin          # User-saved golden model
├── english_general_v1.bin       # Another example
└── ...
```

### Three Operating Modes in UI
1. **Train fresh** - Train new k-means on current videos
2. **Use existing** - Reuse last run's model (`flat_kmeans_200.bin`)
3. **Use golden** - Load a specific saved model from dropdown

---

## Files to Deploy

### 1. Helper Scripts

**Location:** `/workspace/` (root of workspace)

**File: save_golden_kmeans.sh**
```bash
#!/usr/bin/env bash
# Save current k-means model as a golden model
# LINUX CONTAINER VERSION - Use /workspace paths
set -euo pipefail

GOLDEN_DIR="/workspace/VSP-LLM/golden_kmeans"
CURRENT_MODEL="/workspace/VSP-LLM/flat_kmeans_200.bin"

if [[ ! -f "$CURRENT_MODEL" ]]; then
  echo "ERROR: No k-means model found at $CURRENT_MODEL"
  echo "Run the pipeline with k-means training first."
  exit 1
fi

mkdir -p "$GOLDEN_DIR"

# Prompt for model name
echo "Current k-means model: $CURRENT_MODEL"
echo
read -p "Enter a name for this golden model (e.g., '500videos_jan25'): " MODEL_NAME

if [[ -z "$MODEL_NAME" ]]; then
  echo "ERROR: Model name cannot be empty"
  exit 1
fi

# Add .bin extension if not present
if [[ ! "$MODEL_NAME" =~ \.bin$ ]]; then
  MODEL_NAME="${MODEL_NAME}.bin"
fi

GOLDEN_PATH="${GOLDEN_DIR}/${MODEL_NAME}"

if [[ -f "$GOLDEN_PATH" ]]; then
  read -p "Model '$MODEL_NAME' already exists. Overwrite? (y/N): " CONFIRM
  if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
  fi
fi

cp "$CURRENT_MODEL" "$GOLDEN_PATH"
echo
echo "✓ Saved golden k-means model to: $GOLDEN_PATH"
echo "  Size: $(du -h "$GOLDEN_PATH" | cut -f1)"
echo
echo "To use this model in a pipeline run:"
echo "  export GOLDEN_KMEANS='$GOLDEN_PATH'"
echo "  /workspace/run_flat_english_pipeline.sh /path/to/videos"
```

**File: list_golden_kmeans.sh**
```bash
#!/usr/bin/env bash
# List all available golden k-means models
# LINUX CONTAINER VERSION - Use /workspace paths
set -euo pipefail

GOLDEN_DIR="/workspace/VSP-LLM/golden_kmeans"

if [[ ! -d "$GOLDEN_DIR" ]]; then
  echo "No golden models directory found."
  echo "Run save_golden_kmeans.sh first to create one."
  exit 0
fi

echo "Available golden k-means models:"
echo "================================"
echo

if ! ls -1 "$GOLDEN_DIR"/*.bin 2>/dev/null | grep -q .; then
  echo "No golden models found in $GOLDEN_DIR"
  echo
  exit 0
fi

for model in "$GOLDEN_DIR"/*.bin; do
  name=$(basename "$model")
  size=$(du -h "$model" | cut -f1)
  date=$(stat -c '%y' "$model" | cut -d' ' -f1)
  echo "  Name: $name"
  echo "  Size: $size"
  echo "  Date: $date"
  echo "  Path: $model"
  echo
done

echo "To use a golden model:"
echo "  export GOLDEN_KMEANS='/path/to/model.bin'"
echo "  /workspace/run_flat_english_pipeline.sh /path/to/videos"
```

**Deployment Commands:**
```bash
# On Linux container:
cd /workspace

# Copy the two scripts (from EC2 or create them)
chmod +x save_golden_kmeans.sh
chmod +x list_golden_kmeans.sh

# Create golden models directory
mkdir -p /workspace/VSP-LLM/golden_kmeans
```

---

### 2. Modified Pipeline Scripts

**File: /workspace/VSP-LLM/scripts/run_flat_kmeans.sh**

**Modification:** Lines 66-81 (Step 2: train k-means)

**BEFORE:**
```bash
# ---------- Step 2: train k-means (optional) ----------

if [[ "${TRAIN_KMEANS}" == "1" ]]; then
  echo
  echo ">>> [Step 2] Learning k-means (200 clusters) on ${PERCENT} of data for split: ${SPLIT}"
  python "${ROOT}/src/clustering/learn_kmeans.py" \
      "${FEAT_DIR}" \
      "${SPLIT}" \
      "${NSHARD}" \
      "${KM_PATH}" \
      200 \
      --percent "${PERCENT}"
else
  echo
  echo ">>> [Step 2] Skipping k-means training (TRAIN_KMEANS!=1)"
fi
```

**AFTER:**
```bash
# ---------- Step 2: train k-means (optional) ----------

# Check if using a golden (pre-trained) model
if [[ -n "${GOLDEN_KMEANS:-}" ]]; then
  echo
  echo ">>> [Step 2] Using golden k-means model: ${GOLDEN_KMEANS}"
  if [[ ! -f "${GOLDEN_KMEANS}" ]]; then
    echo "ERROR: Golden model not found at ${GOLDEN_KMEANS}"
    exit 1
  fi
  cp "${GOLDEN_KMEANS}" "${KM_PATH}"
  echo "    Copied to: ${KM_PATH}"
elif [[ "${TRAIN_KMEANS}" == "1" ]]; then
  echo
  echo ">>> [Step 2] Learning k-means (200 clusters) on ${PERCENT} of data for split: ${SPLIT}"
  python "${ROOT}/src/clustering/learn_kmeans.py" \
      "${FEAT_DIR}" \
      "${SPLIT}" \
      "${NSHARD}" \
      "${KM_PATH}" \
      200 \
      --percent "${PERCENT}"
else
  echo
  echo ">>> [Step 2] Skipping k-means training (TRAIN_KMEANS!=1)"
  if [[ ! -f "${KM_PATH}" ]]; then
    echo "ERROR: No k-means model found at ${KM_PATH}"
    echo "       Either train a new model (TRAIN_KMEANS=1) or provide GOLDEN_KMEANS path"
    exit 1
  fi
  echo "    Using existing model: ${KM_PATH}"
fi
```

---

### 3. Web UI Backend Changes

**File: /workspace/vsp-ui/app/server.py**

**Change 1:** Add golden models endpoint to `do_GET()` method (around line 71-78)

```python
# In do_GET() method, add this line:
elif path == "/api/golden-models":
    self.handle_list_golden_models()
```

**Full context:**
```python
# API endpoints
if path == "/api/status":
    self.handle_status()
elif path == "/api/progress":
    self.handle_progress()
elif path == "/api/logs":
    self.handle_logs(parsed.query)
elif path == "/api/golden-models":      # <-- ADD THIS
    self.handle_list_golden_models()    # <-- ADD THIS
elif path == "/api/download-output":
    self.handle_download_output()
```

**Change 2:** Add handler method (insert after `handle_validate()`, around line 197)

```python
def handle_list_golden_models(self):
    """List all available golden k-means models."""
    try:
        golden_dir = Path.home() / "VSP-LLM" / "golden_kmeans"
        models = []

        if golden_dir.exists():
            for model_file in sorted(golden_dir.glob("*.bin")):
                stat = model_file.stat()
                models.append({
                    "name": model_file.name,
                    "path": str(model_file),
                    "size": stat.st_size,
                    "created": stat.st_mtime
                })

        self.send_json({"models": models})
    except Exception as e:
        self.send_error_json(f"Error listing golden models: {e}", 500)
```

**Change 3:** Update `handle_start()` method (around line 199-212)

**BEFORE:**
```python
def handle_start(self, data: Dict[str, Any] = None):
    """Start pipeline execution."""
    runner = get_runner()

    if runner.is_running:
        self.send_error_json("Pipeline is already running", 400)
        return

    # Get options from request
    if data is None:
        data = {}
    train_kmeans = data.get('train_kmeans', True)

    success = runner.start(train_kmeans=train_kmeans)
```

**AFTER:**
```python
def handle_start(self, data: Dict[str, Any] = None):
    """Start pipeline execution."""
    runner = get_runner()

    if runner.is_running:
        self.send_error_json("Pipeline is already running", 400)
        return

    # Get options from request
    if data is None:
        data = {}
    train_kmeans = data.get('train_kmeans', True)
    golden_model = data.get('golden_model', None)  # <-- ADD THIS

    success = runner.start(train_kmeans=train_kmeans, golden_model=golden_model)  # <-- MODIFY THIS
```

---

### 4. Web UI Pipeline Runner Changes

**File: /workspace/vsp-ui/app/services/pipeline_runner.py**

**Change 1:** Add instance variable in `__init__()` (around line 28-37)

```python
def __init__(self):
    self.tracker = ProgressTracker()
    self.process: Optional[subprocess.Popen] = None
    self._cancel_requested = False
    self._lock = threading.Lock()
    self._monitor_thread: Optional[threading.Thread] = None
    self._on_progress: Optional[Callable] = None
    self._run_id: Optional[str] = None
    self._train_kmeans: bool = True
    self._golden_model: Optional[str] = None  # <-- ADD THIS
```

**Change 2:** Update `start()` method signature (around line 61-76)

**BEFORE:**
```python
def start(
    self,
    on_progress: Optional[Callable] = None,
    train_kmeans: bool = True,
) -> bool:
    """
    Start the pipeline execution.

    Args:
        on_progress: Callback function called on progress updates
        train_kmeans: Whether to train k-means model (default True)

    Returns:
        True if started successfully, False otherwise
    """
```

**AFTER:**
```python
def start(
    self,
    on_progress: Optional[Callable] = None,
    train_kmeans: bool = True,
    golden_model: Optional[str] = None,  # <-- ADD THIS
) -> bool:
    """
    Start the pipeline execution.

    Args:
        on_progress: Callback function called on progress updates
        train_kmeans: Whether to train k-means model (default True)
        golden_model: Path to golden k-means model to use (default None)  # <-- ADD THIS

    Returns:
        True if started successfully, False otherwise
    """
```

**Change 3:** Store golden_model in start() method (around line 96-102)

**BEFORE:**
```python
# Generate run ID
self._run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
self._cancel_requested = False
self._on_progress = on_progress
self._train_kmeans = train_kmeans

# Reset tracker
self.tracker.reset(self._run_id)
```

**AFTER:**
```python
# Generate run ID
self._run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
self._cancel_requested = False
self._on_progress = on_progress
self._train_kmeans = train_kmeans
self._golden_model = golden_model  # <-- ADD THIS

# Reset tracker
self.tracker.reset(self._run_id)
```

**Change 4:** Update `_get_env()` method (around line 257-264)

**BEFORE:**
```python
def _get_env(self) -> dict:
    """Get environment variables for pipeline execution."""
    env = os.environ.copy()
    # Add any necessary environment variables
    env["PYTHONUNBUFFERED"] = "1"
    # Pass k-means training option
    env["TRAIN_KMEANS"] = "1" if self._train_kmeans else "0"
    return env
```

**AFTER:**
```python
def _get_env(self) -> dict:
    """Get environment variables for pipeline execution."""
    env = os.environ.copy()
    # Add any necessary environment variables
    env["PYTHONUNBUFFERED"] = "1"

    # Pass golden k-means model path if specified
    if self._golden_model:
        env["GOLDEN_KMEANS"] = self._golden_model
        # Don't train k-means if using golden model
        env["TRAIN_KMEANS"] = "0"
    else:
        # Pass k-means training option
        env["TRAIN_KMEANS"] = "1" if self._train_kmeans else "0"

    return env
```

---

### 5. Web UI Frontend Changes

**File: /workspace/vsp-ui/app/static/index.html**

**Modification:** Replace the k-means checkbox with radio buttons (around line 85-92)

**BEFORE:**
```html
<!-- Processing Options -->
<div class="processing-options">
    <h3>Processing Options</h3>
    <label class="checkbox-label">
        <input type="checkbox" id="train-kmeans-checkbox" checked>
        <span>Train new k-means model (uncheck to use existing model if available)</span>
    </label>
</div>
```

**AFTER:**
```html
<!-- Processing Options -->
<div class="processing-options">
    <h3>K-means Model Options</h3>
    <div class="kmeans-options">
        <label class="radio-label">
            <input type="radio" name="kmeans-mode" value="train" checked>
            <span>Train fresh on current videos</span>
        </label>
        <label class="radio-label">
            <input type="radio" name="kmeans-mode" value="existing">
            <span>Use existing model (from last run)</span>
        </label>
        <label class="radio-label">
            <input type="radio" name="kmeans-mode" value="golden">
            <span>Use golden model:</span>
        </label>
        <select id="golden-model-select" class="golden-model-select" disabled>
            <option value="">No golden models available</option>
        </select>
    </div>
</div>
```

---

**File: /workspace/vsp-ui/app/static/app.js**

**Change 1:** Add `loadGoldenModels()` call in `displayValidationResults()` (around line 250-253)

```javascript
// Enable/disable start button
const startBtn = document.getElementById('btn-start');
startBtn.disabled = result.valid_videos.length === 0;

// Load golden k-means models
loadGoldenModels();  // <-- ADD THIS
```

**Change 2:** Add `loadGoldenModels()` function before `startProcessing()` (around line 299)

```javascript
// Processing Screen
async function loadGoldenModels() {
    const goldenSelect = document.getElementById('golden-model-select');

    try {
        const response = await api('golden-models', 'GET');
        const models = response.models || [];

        if (models.length === 0) {
            goldenSelect.innerHTML = '<option value="">No golden models available</option>';
            goldenSelect.disabled = true;
        } else {
            goldenSelect.innerHTML = models
                .map(m => {
                    const sizeMB = (m.size / (1024 * 1024)).toFixed(2);
                    return `<option value="${m.path}">${m.name} (${sizeMB} MB)</option>`;
                })
                .join('');
            goldenSelect.disabled = false;
        }
    } catch (error) {
        console.error('Failed to load golden models:', error);
        goldenSelect.innerHTML = '<option value="">Error loading models</option>';
        goldenSelect.disabled = true;
    }
}
```

**Change 3:** Replace `startProcessing()` function (around line 300-317)

**BEFORE:**
```javascript
async function startProcessing() {
    const btn = document.getElementById('btn-start');
    btn.disabled = true;

    // Get k-means training option
    const trainKmeans = document.getElementById('train-kmeans-checkbox').checked;

    const result = await api('start', 'POST', { train_kmeans: trainKmeans });

    if (!result.success) {
        alert(`Failed to start: ${result.errors?.join(', ') || result.message}`);
        btn.disabled = false;
        return;
    }

    showScreen('processing');
    startProgressPolling();
}
```

**AFTER:**
```javascript
async function startProcessing() {
    const btn = document.getElementById('btn-start');
    btn.disabled = true;

    // Get k-means mode
    const kmeansMode = document.querySelector('input[name="kmeans-mode"]:checked').value;

    let trainKmeans = false;
    let goldenModel = null;

    if (kmeansMode === 'train') {
        trainKmeans = true;
    } else if (kmeansMode === 'golden') {
        const goldenSelect = document.getElementById('golden-model-select');
        goldenModel = goldenSelect.value;

        if (!goldenModel) {
            alert('Please select a golden model or choose a different option');
            btn.disabled = false;
            return;
        }
    }
    // else kmeansMode === 'existing': trainKmeans=false, goldenModel=null

    const result = await api('start', 'POST', {
        train_kmeans: trainKmeans,
        golden_model: goldenModel
    });

    if (!result.success) {
        alert(`Failed to start: ${result.errors?.join(', ') || result.message}`);
        btn.disabled = false;
        return;
    }

    showScreen('processing');
    startProgressPolling();
}
```

**Change 4:** Add radio button event listeners in `DOMContentLoaded` (around line 704-708)

```javascript
// Validation screen
document.getElementById('btn-back').addEventListener('click', () => {
    showScreen('welcome');
    refreshStatus();
});
document.getElementById('btn-start').addEventListener('click', startProcessing);

// K-means mode radio buttons - enable/disable golden model select
document.querySelectorAll('input[name="kmeans-mode"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        const goldenSelect = document.getElementById('golden-model-select');
        goldenSelect.disabled = e.target.value !== 'golden';
    });
});  // <-- ADD THIS
```

---

**File: /workspace/vsp-ui/app/static/style.css**

**Modification:** Add styles for radio buttons and select dropdown (insert after `.checkbox-label` styles, around line 503)

```css
/* K-means Options */
.kmeans-options {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.radio-label {
    display: flex;
    align-items: center;
    cursor: pointer;
    font-size: 0.95rem;
}

.radio-label input[type="radio"] {
    margin-right: 10px;
    width: 18px;
    height: 18px;
    cursor: pointer;
}

.radio-label span {
    user-select: none;
}

.golden-model-select {
    margin-left: 28px;
    padding: 8px 12px;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    background: white;
    font-size: 0.9rem;
    font-family: inherit;
    min-width: 250px;
    max-width: 100%;
}

.golden-model-select:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background: var(--bg-color);
}
```

---

## Testing Checklist

After deployment, verify:

- [ ] Helper scripts exist and are executable
  ```bash
  ls -lh /workspace/save_golden_kmeans.sh
  ls -lh /workspace/list_golden_kmeans.sh
  ```

- [ ] Golden models directory created
  ```bash
  ls -ld /workspace/VSP-LLM/golden_kmeans
  ```

- [ ] Pipeline script modification applied
  ```bash
  grep -n "GOLDEN_KMEANS" /workspace/VSP-LLM/scripts/run_flat_kmeans.sh
  # Should show the new if-elif-else logic
  ```

- [ ] Web UI backend updated
  ```bash
  grep -n "handle_list_golden_models" /workspace/vsp-ui/app/server.py
  grep -n "golden_model" /workspace/vsp-ui/app/services/pipeline_runner.py
  ```

- [ ] Web UI frontend updated
  ```bash
  grep -n "kmeans-mode" /workspace/vsp-ui/app/static/index.html
  grep -n "loadGoldenModels" /workspace/vsp-ui/app/static/app.js
  grep -n "radio-label" /workspace/vsp-ui/app/static/style.css
  ```

- [ ] UI functional test:
  1. Start web UI
  2. Scan videos
  3. Verify k-means options show three radio buttons
  4. Verify golden model dropdown exists (disabled by default)
  5. Select "Use golden model" radio button
  6. Verify dropdown becomes enabled
  7. Check dropdown populates with models (if any exist)

- [ ] End-to-end test:
  1. Run pipeline with "Train fresh" mode
  2. After completion, run `./save_golden_kmeans.sh`
  3. Run `./list_golden_kmeans.sh` to verify saved
  4. Start new pipeline run with "Use golden model" selected
  5. Verify logs show "Using golden k-means model"
  6. Verify k-means training step is skipped

---

## Usage Examples

### Example 1: Save a Golden Model via Terminal

```bash
# After successful pipeline run with k-means training:
cd /workspace
./save_golden_kmeans.sh

# Enter name when prompted:
# > 500videos_english_jan25

# Verify:
./list_golden_kmeans.sh
```

### Example 2: Use Golden Model via Web UI

1. Navigate to validation screen
2. Under "K-means Model Options", select "Use golden model:"
3. Choose model from dropdown (e.g., "500videos_english_jan25.bin")
4. Click "Start Processing"
5. Pipeline will skip k-means training and use saved model

### Example 3: Use Golden Model via Terminal (Manual)

```bash
export GOLDEN_KMEANS="/workspace/VSP-LLM/golden_kmeans/500videos_english_jan25.bin"
/workspace/run_flat_english_pipeline.sh /workspace/vsp_input
```

---

## Troubleshooting

### Issue: Dropdown shows "No golden models available"

**Cause:** No `.bin` files in `/workspace/VSP-LLM/golden_kmeans/`

**Solution:**
```bash
# Train k-means first (run pipeline with "Train fresh" mode)
# Then save model:
./save_golden_kmeans.sh
```

### Issue: "Golden model not found" error during pipeline

**Cause:** Model file was deleted or moved

**Solution:**
```bash
# Verify model exists:
ls -lh /workspace/VSP-LLM/golden_kmeans/
# Re-save or select different model
```

### Issue: UI doesn't show new golden models

**Cause:** Frontend cache or models added manually

**Solution:**
- Refresh browser page (Ctrl+F5)
- Or navigate back to welcome screen and re-scan

---

## Summary of Changes

| Component | File | Change Type | Lines Modified |
|-----------|------|-------------|----------------|
| Helper Scripts | save_golden_kmeans.sh | NEW | N/A |
| Helper Scripts | list_golden_kmeans.sh | NEW | N/A |
| Pipeline | VSP-LLM/scripts/run_flat_kmeans.sh | MODIFY | 66-95 |
| Backend | vsp-ui/app/server.py | ADD | ~25 lines |
| Backend | vsp-ui/app/services/pipeline_runner.py | MODIFY | ~15 lines |
| Frontend | vsp-ui/app/static/index.html | MODIFY | ~15 lines |
| Frontend | vsp-ui/app/static/app.js | MODIFY + ADD | ~60 lines |
| Frontend | vsp-ui/app/static/style.css | ADD | ~40 lines |

**Total:** ~2 new files, 5 modified files, ~155 lines of code

---

## Related Documentation

- Main feature documentation: `GOLDEN_KMEANS_FEATURE.md`
- Pipeline documentation: `CLAUDE.md`
- Transcription feature: `LINUX_CONTAINER_UPDATES.md` (existing)
