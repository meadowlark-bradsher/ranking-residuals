# Quantization loss and destruction of the flow are different events

`_check_collapse` in `rig/emit.py` separates two things that both look like
"the edge came out zero".

An edge whose target is genuinely near a tie *should* emit a tie. At `k` rows the
representable band around zero is `|Y| <= log((k+1)/(k-1))`, and losing an edge
inside that band is ordinary quantization loss, reported through the residual the
function returns alongside the dead-edge count.

What must never pass silently is the flow being destroyed outright. A ±1 rule at
`k = 2` rounds every edge to a 1–1 tie, and the `1/(2k)` clamp in
`analyze_comparisons` then pins the whole flow to zero. That is not rounding; it
is emitting nothing, and a run that returned it would report a clean zero
harmonic reading from a flow that never survived emission.

The guard fires only when the target has energy and the achieved flow has none —
`tgt_energy > 0` and `achieved @ achieved == 0.0` — and raises `EmissionCollapse`
naming the location, `k`, how many edges died, and the width of the band that
swallowed them, then names the two ways out: use the `sign` path for a ±1 rule,
or raise `emit_k`.

This is the same trap as spec §5.1 one level down. §5.1 is about a ±1 flow
depositing spurious harmonic mass; this is about a ±1 flow quantizing away to
nothing. Emission therefore has three non-interchangeable paths — `counts`,
`sign`, `magnitude` — and `emit_from_counts` separately refuses any `k` below
`MIN_ROWS_PER_PAIR`.
