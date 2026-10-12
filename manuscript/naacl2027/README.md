# NAACL 2027 Paper

## Canonical artifacts

- `main.tex`: anonymous long-paper source.
- `main.pdf`: compiled nine-page review PDF.
- `references.bib`: 13 cited and resolved references.
- `figures/figure_1_three_graphs.svg`: editable framework figure.
- `figures/render_results.py`: evidence-frozen results plotting source.

The PDF contains seven content pages, references, and a two-page appendix. It
has not been uploaded or submitted.

## Build

From this directory:

```bash
rsvg-convert -f pdf -o figures/figure_1_three_graphs.rsvg.pdf figures/figure_1_three_graphs.svg
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dNOPAUSE -dBATCH \
  -sOutputFile=figures/figure_1_three_graphs.pdf \
  figures/figure_1_three_graphs.rsvg.pdf
python3 figures/render_results.py
tectonic --keep-logs --keep-intermediates main.tex
```

The checked-in `acl.sty` and `acl_natbib.bst` are hash-identical to the
official ACL style repository snapshot used for this draft.

The plotting step requires Matplotlib and NumPy.
