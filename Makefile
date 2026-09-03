# Building paper 1, in an order it is possible to get wrong by hand.
#
# The draft is not a file in this repository. `combined-body.tex`, the figures
# and the PDF are all build products, all gitignored, and every one of them is
# derived from something that moves -- which is why the order below is expressed
# as prerequisites rather than as a list of commands in a README. The figures are
# generated FROM evidence.json, so building the PDF without rebuilding them first
# is how a figure comes to disagree with the caption printed beside it.
#
#   make draft    figures -> combined-body.tex -> combined.pdf, then check refs
#   make test     the definition of done (CLAUDE.md)
#   make verify   registry + load-bearing manifest
#   make clean    remove every build product

PY      := python
METH    := design/methodology
COMB    := $(METH)/combined
EVIDENCE:= $(METH)/evidence/evidence.json
SOURCES := $(METH)/calibration-methodology.tex $(METH)/bridge-invariance.tex
FIGS    := $(METH)/fig-draws.pdf $(METH)/fig-guard.pdf \
           $(METH)/fig-rho-plateau.pdf $(METH)/fig-window.pdf
BODY    := $(COMB)/combined-body.tex
PDF     := $(COMB)/combined.pdf

.DEFAULT_GOAL := help
.PHONY: help draft figures test verify clean

help:
	@echo "make draft    build paper 1 -> $(PDF)"
	@echo "make figures  regenerate the figures from evidence.json"
	@echo "make test     python -m pytest tests/ -q"
	@echo "make verify   evidence/verify.py + .load-bearing/verify.py"
	@echo "make clean    remove build products"

# Figures come from the registry, never from a fresh run. If evidence.json moves,
# so must these -- that dependency is the reason this Makefile exists.
$(FIGS): $(EVIDENCE) $(METH)/make_figures.py
	$(PY) $(METH)/make_figures.py

figures: $(FIGS)

# build.py extracts sections by title and interleaves them; ORDER is the only
# editorial content in it. Nobody edits $(BODY) -- it is overwritten every build.
$(BODY): $(SOURCES) $(COMB)/build.py
	$(PY) $(COMB)/build.py

# An unresolved \ref or \cite is a WARNING to LaTeX, not an error: it renders as
# `??` and the build still "succeeds". So the check is part of building, and it
# fails loudly, because a draft that is quietly wrong is the thing to avoid.
$(PDF): $(BODY) $(COMB)/combined.tex $(FIGS)
	cd $(COMB) && tectonic -X compile combined.tex --keep-logs
	@n=$$(grep -cE "Reference .* undefined|Citation .* undefined" $(COMB)/combined.log || true); \
	if [ "$$n" != "0" ]; then \
	  echo "FAIL: $$n undefined reference(s)/citation(s) -- the PDF has ?? in it:"; \
	  grep -E "Reference .* undefined|Citation .* undefined" $(COMB)/combined.log | head; \
	  exit 1; \
	fi
	@echo "OK: $(PDF), no undefined references or citations"

draft: $(PDF)

test:
	$(PY) -m pytest tests/ -q

verify:
	$(PY) .load-bearing/verify.py
	cd $(METH)/evidence && $(PY) verify.py

clean:
	rm -f $(FIGS) $(BODY) $(PDF) $(COMB)/combined.log $(COMB)/combined.toc \
	      $(COMB)/combined.aux $(COMB)/combined.out
