# Argos VSP - LaTeX Beamer Presentation

Academic-style presentation using the Metropolis theme with custom Argos branding.

## Quick Start

```bash
# Install dependencies (one-time)
make install-deps

# Build the PDF
make

# Present with pdfpc (inline video playback + timer)
make present
```

## Build Targets

| Target | Description |
|--------|-------------|
| `make` | Build `main.pdf` (generates thumbnails + compiles) |
| `make notes` | Build `main-notes.pdf` with speaker notes visible |
| `make present` | Launch pdfpc with inline video playback |
| `make present-notes` | Launch pdfpc with notes on second screen |
| `make thumbnails` | Generate video thumbnails from MP4 first frames |
| `make watch` | Continuous compilation (auto-rebuild on save) |
| `make clean` | Remove all build artifacts |
| `make install-deps` | Install TeX Live + pdfpc + ffmpeg |

## Structure

```
main.tex                    # Master document
beamer-argos-theme.sty      # Custom theme (colors, commands, layouts)
Makefile                    # Build system
sections/
  01_opening.tex            # Slides 1-4: Context
  02_research_findings.tex  # Slides 5-16: Research (40%)
  03_engineering.tex        # Slides 17-23: Engineering (25%)
  04_future_directions.tex  # Slides 24-30: Future (35%)
  05_appendix.tex           # Slides A1-A10: Backup
tables/                     # Standalone table files
figures/                    # Symlinks to presentation_materials_20260224/
videos/                     # Symlinks + auto-generated thumbnails
```

## Video Playback

Videos are embedded using the `multimedia` package. They play inline via pdfpc:

- **pdfpc**: `pdfpc main.pdf` - videos play on slide click
- **Static PDF**: thumbnails with play icons shown (click opens external player)

## Dependencies

- TeX Live (texlive-latex-extra, texlive-fonts-extra, texlive-science, texlive-pictures)
- latexmk
- ffmpeg (for video thumbnail generation)
- pdfpc (for presentation delivery)
