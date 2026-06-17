# Minimal makefile for Sphinx

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

.PHONY: help Makefile clean dirhtml html livehtml static-prep

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Prepare _static by copying assets from the repo's Hugo static/ dir
static-prep:
	@mkdir -p _static
	@cp -u ../static/headshot.jpg _static/headshot.jpg 2>/dev/null || true
	@cp -u ../static/favicon.ico _static/favicon.ico 2>/dev/null || true
	@cp -u ../static/social.jpg _static/social.jpg 2>/dev/null || true

# Build with dirhtml (clean URLs: /post/slug/ instead of /post/slug.html)
dirhtml: static-prep
	@$(SPHINXBUILD) -M dirhtml "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Regular HTML build (for local preview)
html: static-prep
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Live-reload development server (requires sphinx-autobuild)
livehtml: static-prep
	sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" \
		--ignore "*.pyc" --ignore "_build" --ignore "content" \
		--watch sphinx_kschaul_theme $(SPHINXOPTS)

clean:
	@$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx
%: Makefile static-prep
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
