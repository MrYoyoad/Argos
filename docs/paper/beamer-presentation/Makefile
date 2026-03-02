TEX      = pdflatex
LATEXMK  = latexmk
MAIN     = main
OUTDIR   = build

.PHONY: all clean watch thumbnails install-deps present notes

# Default: build the presentation PDF
all: thumbnails $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex sections/*.tex tables/*.tex figures/tikz/*.tex beamer-argos-theme.sty
	$(LATEXMK) -pdf \
		-pdflatex="$(TEX) -interaction=nonstopmode -halt-on-error -shell-escape" \
		-outdir=$(OUTDIR) $(MAIN).tex
	cp $(OUTDIR)/$(MAIN).pdf .

# Build with speaker notes visible (dual-screen mode for pdfpc)
notes: thumbnails
	$(LATEXMK) -pdf \
		-pdflatex="$(TEX) -interaction=nonstopmode -halt-on-error -shell-escape \
		'\def\shownotes{1}\input{$(MAIN)}'" \
		-outdir=$(OUTDIR) -jobname=$(MAIN)-notes
	cp $(OUTDIR)/$(MAIN)-notes.pdf .

# Generate video thumbnails from MP4 first frames
thumbnails:
	@mkdir -p videos/thumbnails
	@for v in videos/source/*.mp4; do \
		name=$$(basename "$$v" _with_hyp.mp4); \
		thumb="videos/thumbnails/$${name}_thumb.png"; \
		if [ ! -f "$$thumb" ]; then \
			echo "Generating thumbnail: $$thumb"; \
			ffmpeg -y -i "$$v" -vframes 1 -q:v 2 "$$thumb" 2>/dev/null || true; \
		fi; \
	done

# Present using pdfpc (inline video playback + speaker notes)
present: all
	@echo "Launching pdfpc with video support..."
	pdfpc $(MAIN).pdf

# Present with notes on second screen
present-notes: notes
	pdfpc --notes=right $(MAIN)-notes.pdf

# Continuous compilation (auto-rebuild on save)
watch:
	$(LATEXMK) -pdf -pvc \
		-pdflatex="$(TEX) -interaction=nonstopmode -shell-escape" \
		-outdir=$(OUTDIR) $(MAIN).tex

# Install system dependencies (Ubuntu/Debian)
install-deps:
	sudo apt-get update && sudo apt-get install -y \
		texlive-latex-base texlive-latex-recommended texlive-latex-extra \
		texlive-fonts-extra texlive-fonts-recommended texlive-science \
		texlive-pictures texlive-font-utils latexmk ffmpeg pdfpc

# Clean build artifacts
clean:
	$(LATEXMK) -outdir=$(OUTDIR) -C $(MAIN).tex 2>/dev/null || true
	rm -rf $(OUTDIR)
	rm -f $(MAIN).pdf $(MAIN)-notes.pdf
	rm -f videos/thumbnails/*.png
