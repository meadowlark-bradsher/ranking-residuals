# The instrument is not forked

`hodge.py` at the repo root is the single implementation of the Hodge
decomposition this project uses. `design/reference/hodge.py` is the same file,
byte for byte: both hash to `f9fccc81…` under SHA-256, so `git` itself carries
the proof and `shasum -a 256 hodge.py design/reference/hodge.py` is the check.

Everything downstream reads through it. `build_operators` returns the gradient
and curl operators `D0`, `D1`; `triangles_for_filling` fixes the 2-skeleton
under the `empty` / `observed` / `custom` convention; `hodge_decompose` splits a
flow by least squares and `hodge_projectors` returns `P_grad`, `P_curl`,
`P_harm` by pseudo-inverse. The two entry doors are deliberately different
tests: `analyze_flow` validates the internal `(g, c, h)` on a known real-valued
flow, and `analyze_comparisons` validates the judgment-log round trip. They
carry different default fillings by design, which is why the rig always passes
`filling` explicitly and logs it.

The rig is a data source, never a reimplementation. Its job is to manufacture
comparison data with controlled Hodge structure and hand it to this file; if the
rig computed its own decomposition, a bug shared between generator and analyzer
would cancel and the certificate would validate against itself. The oracle in
`rig/oracle.py` is held to the same rule — its projectors come from
`hodge.hodge_projectors`, not from a local copy.
