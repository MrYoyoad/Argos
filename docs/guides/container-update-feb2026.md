# Container Update Guide (February 2026)

The client machine runs ~v1.0.32-35 (~Feb 15-17). The FINAL directory on EC2 has v1.0.39+ with all fixes including the critical NVENC silent corruption fix. The current tarball is stale (5 files updated after packing). **No code changes needed — just repack and ship.**

## Version Gap

| | Version | Date | Status |
|---|---------|------|--------|
| **Client machine** | ~v1.0.32-35 | ~Feb 15-17 | Last deployed before experiments started |
| **FINAL directory (EC2)** | v1.0.39+ | Feb 17-18 | All fixes + golden k-means + report params |
| **Current tarball** | **STALE** | Feb 17 16:55 | Missing 5 files added after packing |

## What the Client Is Missing

| Version | Fix | Impact |
|---------|-----|--------|
| v1.0.36-39 | **NVENC silent corruption fix + bash fd isolation** | **Critical: destroys 43% of videos without this** |
| v1.0.36 | ETA removal from progress display | Cosmetic |
| v1.0.37 | VLC configuration | Usability |
| post-v1.0.39 | Golden k-means baseline update (1396-video model) | Better clustering baseline |
| post-v1.0.39 | Report decode parameters feature | Reports show which decode params were used |

## Steps

**Step 1**: Fix minor bug in `scripts/build/verify_container_sync.sh` line 21
- Missing trailing `/` in glob pattern

**Step 2**: Verify FINAL directory integrity
```bash
bash scripts/build/verify_container_sync.sh
```

**Step 3**: Rebuild tarball
```bash
cd /home/ubuntu
tar czf vsp_linux_container_FINAL_20260217.tar.gz vsp_linux_container_FINAL_20260217/
sha256sum vsp_linux_container_FINAL_20260217.tar.gz > vsp_linux_container_FINAL_20260217.sha256
```

**Step 4**: Transfer `.tar.gz` and `.sha256` to client (`/home/ds/Desktop/`)

**Step 5**: On client — extract and install
```bash
cd /home/ds/Desktop/
sha256sum -c vsp_linux_container_FINAL_20260217.sha256
tar xzf vsp_linux_container_FINAL_20260217.tar.gz
# Inside Docker container:
cd /host/galaxy_export
bash ../vsp_linux_container_FINAL_20260217/INSTALL.sh
```

**Step 6**: INSTALL.sh runs verification (13 checks) and module tests (37 tests) automatically.

## Rollback
```bash
cd /home/ds/Desktop/
tar xzf galaxy_export_backup_*.tar.gz
```

## Note
- Standalone runs `do_sample=True` (stochastic); EC2 has `do_sample=False` (deterministic)
- Minor for beam=20 but should be unified eventually
