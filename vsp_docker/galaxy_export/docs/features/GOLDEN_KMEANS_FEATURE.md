# Golden K-means Models Feature

**Added:** January 25, 2026
**Purpose:** Save and reuse pre-trained k-means models across pipeline runs

## Overview

This feature allows you to:
1. Train k-means on a curated set of videos (e.g., 500 videos) **once**
2. Save the trained model to a dedicated "golden" location
3. Reuse that model in future pipeline runs without retraining
4. Maintain multiple named models for different use cases

## Architecture

### Storage Location
```
VSP-LLM/golden_kmeans/
├── 500videos_jan25.bin          # Model trained on 500 videos
├── english_general_v1.bin       # Another named model
├── spanish_v1.bin               # Language-specific model
└── ...
```

### Three Operating Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| **Train Fresh** | Train new k-means on current videos | First run, or when visual patterns changed significantly |
| **Use Existing** | Reuse `flat_kmeans_200.bin` from last run | Quick iterations on same dataset |
| **Use Golden** | Load a specific pre-trained model | Production runs with known-good model |

---

## Quick Start

### 1. Train and Save a Golden Model

**EC2:**
```bash
# Train k-means on your 500 videos (with UI checkbox CHECKED to train)
./run_flat_english_pipeline.sh ~/vsp_input

# After pipeline completes, save the model
./save_golden_kmeans.sh
# Enter name: 500videos_jan25
```

**Linux Container:**
```bash
# Train k-means on your videos
/workspace/run_flat_english_pipeline.sh /workspace/vsp_input

# Save the model
/workspace/save_golden_kmeans.sh
# Enter name: 500videos_jan25
```

### 2. List Available Golden Models

**EC2:**
```bash
./list_golden_kmeans.sh
```

**Linux Container:**
```bash
/workspace/list_golden_kmeans.sh
```

### 3. Use a Golden Model in Pipeline

**Option A: Via Environment Variable (Manual)**
```bash
export GOLDEN_KMEANS="/workspace/VSP-LLM/golden_kmeans/500videos_jan25.bin"
/workspace/run_flat_english_pipeline.sh /workspace/vsp_input
```

**Option B: Via UI (Future - see Phase 2 below)**
Select from dropdown in validation screen.

---

## Technical Implementation

### Modified Files

#### 1. `VSP-LLM/scripts/run_flat_kmeans.sh`

**Changes:**
- Added support for `GOLDEN_KMEANS` environment variable
- New priority order:
  1. If `GOLDEN_KMEANS` set → Copy golden model to `KM_PATH`
  2. Else if `TRAIN_KMEANS=1` → Train new model
  3. Else → Use existing `KM_PATH` (with error check)

**Code Location:** Lines 66-95

#### 2. Helper Scripts (New Files)

**EC2 Paths:**
- `/home/ubuntu/save_golden_kmeans.sh` - Save current model as golden
- `/home/ubuntu/list_golden_kmeans.sh` - List all golden models

**Linux Container Paths:**
- `/workspace/save_golden_kmeans.sh` - Save current model as golden
- `/workspace/list_golden_kmeans.sh` - List all golden models

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│         Pipeline Run (K-means Step)                      │
└─────────────────────────────────────────────────────────┘
                          ↓
          ┌───────────────────────────┐
          │ GOLDEN_KMEANS env set?    │
          └───────────────────────────┘
           ↓ Yes                  ↓ No
    ┌──────────────┐      ┌──────────────┐
    │ Copy golden  │      │ TRAIN_KMEANS │
    │ model to     │      │    = 1?      │
    │ KM_PATH      │      └──────────────┘
    └──────────────┘       ↓ Yes    ↓ No
                    ┌───────────┐  ┌───────────┐
                    │ Train new │  │ Use exist-│
                    │ k-means   │  │ ing model │
                    └───────────┘  └───────────┘
                          ↓              ↓
                    ┌─────────────────────┐
                    │ Save to KM_PATH     │
                    └─────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │ Extract labels      │
                    │ using KM_PATH       │
                    └─────────────────────┘
```

---

## Deployment to Linux Container

### Files to Copy/Modify

**1. Helper Scripts:**
```bash
# On Linux container:
mkdir -p /workspace/VSP-LLM/golden_kmeans

# Copy these files to /workspace/:
- save_golden_kmeans.sh  (Linux version)
- list_golden_kmeans.sh  (Linux version)

# Make executable:
chmod +x /workspace/save_golden_kmeans.sh
chmod +x /workspace/list_golden_kmeans.sh
```

**2. Modified Pipeline Script:**
```bash
# Update this file on Linux container:
/workspace/VSP-LLM/scripts/run_flat_kmeans.sh

# Apply the modification shown in section "Modified Files" above
# (Lines 66-95: Add GOLDEN_KMEANS support)
```

### Verification

```bash
# 1. Check scripts exist and are executable
ls -lh /workspace/save_golden_kmeans.sh
ls -lh /workspace/list_golden_kmeans.sh

# 2. Verify modification in run_flat_kmeans.sh
grep -A 5 "GOLDEN_KMEANS" /workspace/VSP-LLM/scripts/run_flat_kmeans.sh
# Should show the new if-elif-else logic

# 3. Create test golden model
echo "test" > /workspace/VSP-LLM/golden_kmeans/test.bin
/workspace/list_golden_kmeans.sh
# Should list test.bin
```

---

## Phase 2: UI Integration (Future Enhancement)

### Proposed UI Changes

**Validation Screen - K-means Options:**
```
┌─────────────────────────────────────────────────┐
│ K-means Training Options:                       │
│                                                  │
│ ○ Train fresh on current videos                 │
│ ○ Use existing model (flat_kmeans_200.bin)      │
│ ○ Use golden model: [Dropdown ▼]                │
│                     ├─ 500videos_jan25.bin      │
│                     ├─ english_general_v1.bin   │
│                     └─ spanish_v1.bin           │
│                                                  │
│ [✓] Save as golden after training               │
│     Name: [________________________]            │
└─────────────────────────────────────────────────┘
```

### Backend Changes Needed

**1. API Endpoint (server.py):**
```python
@app.route('/api/golden-models', methods=['GET'])
def handle_list_golden_models():
    """List all available golden k-means models"""
    golden_dir = Path.home() / "VSP-LLM" / "golden_kmeans"
    models = []
    if golden_dir.exists():
        for model_file in golden_dir.glob("*.bin"):
            models.append({
                "name": model_file.name,
                "path": str(model_file),
                "size": model_file.stat().st_size,
                "created": model_file.stat().st_mtime
            })
    return jsonify(models)
```

**2. Pipeline Runner Update (pipeline_runner.py):**
```python
def start(self, train_kmeans: bool = True, golden_model: str = None, save_as_golden: str = None):
    env = self._get_env()

    if golden_model:
        env["GOLDEN_KMEANS"] = golden_model
        env["TRAIN_KMEANS"] = "0"  # Don't train if using golden
    else:
        env["TRAIN_KMEANS"] = "1" if train_kmeans else "0"

    # ... existing code ...

    # After pipeline completes successfully:
    if save_as_golden and not golden_model:  # Only save if we trained
        self._save_as_golden(save_as_golden)
```

**3. Frontend Update (app.js):**
```javascript
async function loadGoldenModels() {
    const response = await fetch('/api/golden-models');
    const models = await response.json();

    const dropdown = document.getElementById('golden-model-select');
    dropdown.innerHTML = models.map(m =>
        `<option value="${m.path}">${m.name} (${formatSize(m.size)})</option>`
    ).join('');
}

function startPipeline() {
    const kmeansMode = document.querySelector('input[name="kmeans-mode"]:checked').value;

    const options = {
        train_kmeans: kmeansMode === 'train',
        golden_model: kmeansMode === 'golden' ?
            document.getElementById('golden-model-select').value : null,
        save_as_golden: document.getElementById('save-as-golden').checked ?
            document.getElementById('golden-name-input').value : null
    };

    fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(options)
    });
}
```

---

## Use Cases

### Use Case 1: Production Baseline
```bash
# 1. Curate 500 high-quality videos
# 2. Train k-means once
# 3. Save as "production_english_v1.bin"
# 4. All future runs use this model for consistency
```

### Use Case 2: Multi-Language Support
```bash
# Train separate models for each language:
- english_general.bin (trained on English videos)
- spanish_general.bin (trained on Spanish videos)
- french_general.bin (trained on French videos)

# Select appropriate model based on input language
```

### Use Case 3: Quick Iteration
```bash
# Day 1: Train on large dataset, save as golden
# Day 2-7: Process different videos using same golden model
# Result: Save hours of k-means training time
```

---

## Performance Impact

### Training Time Savings

| Dataset Size | K-means Training Time | Savings with Golden Model |
|--------------|----------------------|---------------------------|
| 100 videos   | ~2-5 minutes         | ~2-5 minutes              |
| 500 videos   | ~10-15 minutes       | ~10-15 minutes            |
| 1000 videos  | ~20-30 minutes       | ~20-30 minutes            |

**Note:** Feature extraction (Step 1) still runs every time - only k-means training (Step 2) is skipped.

### Storage Requirements

- Each k-means model: ~800 KB
- 10 golden models: ~8 MB
- Negligible storage impact

---

## Troubleshooting

### Error: "Golden model not found"
```bash
# Check the path:
ls -lh /workspace/VSP-LLM/golden_kmeans/

# Verify GOLDEN_KMEANS is set correctly:
echo $GOLDEN_KMEANS

# Use absolute path:
export GOLDEN_KMEANS="/workspace/VSP-LLM/golden_kmeans/your_model.bin"
```

### Error: "No k-means model found at KM_PATH"
This happens when:
- `TRAIN_KMEANS=0` (checkbox unchecked)
- No `GOLDEN_KMEANS` provided
- No existing `flat_kmeans_200.bin` from previous run

**Solution:** Either:
1. Check "Train k-means" box, OR
2. Provide a golden model, OR
3. Run pipeline once with training to create `flat_kmeans_200.bin`

### Golden model produces poor results
Possible causes:
- Model trained on different visual patterns (e.g., different camera angles, lighting)
- Model trained on different language (different mouth movements)
- Cluster count mismatch (current code assumes 200 clusters)

**Solution:** Train a new golden model on representative data for your use case.

---

## Future Enhancements

1. **Cluster count flexibility**: Support models with different cluster counts (e.g., 100, 200, 500)
2. **Model metadata**: Track training dataset, date, cluster count, language
3. **Model validation**: Automatic quality checks when loading golden models
4. **Cloud storage**: Upload/download golden models from S3 or similar
5. **Model comparison**: A/B test different golden models on same input

---

## Related Documentation

- Main pipeline: `run_flat_english_pipeline.sh`
- K-means implementation: `VSP-LLM/src/clustering/`
- CLAUDE.md section: "Changing K-means Clusters"
