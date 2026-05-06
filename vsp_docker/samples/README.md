# Test Fixtures

Two videos used by `checks/post_install_check.sh` to verify the image works end-to-end. **These are designed test fixtures, not arbitrary clips.**

## Required files

| File | Duration | Design intent | Used by |
|---|---|---|---|
| `smoke_12s.mp4` | ~10-15 s | Fast sanity check — proves the pipeline wires up at all. Should contain at least one **number word** (e.g. "billion", "1024", "2026") to exercise number-capping in confidence colors. | step 4 of post_install_check |
| `smoke_75s.mp4` | ~60-90 s | Exercises batching, n-best aggregation, MBR display, tier classification. Should produce **at least one Trust-tier segment AND one Salvage-tier segment** so the post-install visual sanity check covers both. | step 5 of post_install_check |
| `checksums.txt` | — | SHA256 hashes of the two MP4 files. `post_install_check.sh` verifies these to catch fixture rot — i.e. someone swapping the test videos for content that no longer exercises the same code paths. | step 3 of post_install_check |

## Why curated, not arbitrary

`post_install_check.sh` does **mechanism-checks** (does aggregated.json have all 5 hyp_* keys? does report.csv have NIV labels?), not outcome-checks. Mechanism checks pass independent of the video content. But the **manual visual inspection** during Layer-2 staging needs:

- A number word so we can confirm the orange-cap-on-numbers logic fires.
- Both Trust and Salvage tier segments so we can confirm tier classification visually.
- A segment where MBR ≠ top-1 so we can confirm the MBR-as-default-display path is firing (not silently falling back to top-1).

If the fixtures get swapped for clips that don't exercise these, the mechanism-checks still pass, but the visual sanity check stops being meaningful — silent fixture rot. The `checksums.txt` verification catches that.

## Generating checksums

After curating both files:

```bash
cd vsp_docker/samples
sha256sum smoke_12s.mp4 smoke_75s.mp4 > checksums.txt
```

## Current fixture status (initial placeholder)

The fixtures shipped in this initial build:

- `smoke_12s.mp4` — 10s, copied from `vsp_input/Ariel_numbers.mp4`. English numbers content; exercises number-cap-on-orange logic. **Good fit for design intent.**
- `smoke_75s.mp4` — 35s, ffmpeg concatenation of 7 short LRS3-style clips at 640x?, 25 fps. **Below the 60-90s target.** Replace during Layer-2 staging with a properly-curated 60-90s clip from your own content that:
  - Produces both a Trust-tier segment AND a Salvage-tier segment (mean per-word prob ≥ 0.82 AND between 0.65-0.82)
  - Has at least one segment where MBR hypothesis differs from the top-1 hypothesis
  - Contains at least one numeric word (number-cap exercise)

After updating, regenerate `checksums.txt`:

```bash
cd vsp_docker/samples
sha256sum smoke_12s.mp4 smoke_75s.mp4 > checksums.txt
```

## When to update

When the build pipeline ships new feature behavior that the existing fixtures don't exercise (e.g. a new aggregation method, a new column in report.csv), update the fixtures and update `checksums.txt`. Bump `client-build-NNN` accordingly.

## Where they ship

- Inside the Docker image: `COPY galaxy_export/samples/` — the in-container copy used when running smoke tests via `docker run --rm <image> /workspace/run_flat_english_pipeline.sh /workspace/samples`.
- On the kit USB at `samples/` next to the image tarball.
- The `.dockerignore` has an exception so they survive `**/*.mp4` exclusion: `!galaxy_export/samples/*.mp4`.
