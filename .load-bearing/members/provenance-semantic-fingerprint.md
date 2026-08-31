# A fingerprint sensitive to meaning and blind to presentation

`semantic_fingerprint(module, entry)` in `rig/provenance.py` hashes an entry
point together with everything in its module it transitively depends on, so an
artifact can record the code that produced it.

It works over a normalized AST dump with docstrings stripped, which is what makes
it stable across comments, docstrings, blank lines and reindentation while still
changing when any body or constant in the closure changes meaning. Starting from
`entry`, it walks module-level names by repeated reference-resolution: at each
round it collects the names referenced by the current frontier, subtracts what it
has already seen, and stops when a round adds nothing, bounded by `_max_depth`.

Sibling modules are treated as a separate species from module-level names. An
imported sibling is an alias, not a definition in this module, so aliases are
added to `known` — otherwise a reference through one would not count as a
reference at all — but they are routed to `reached` rather than the frontier, and
folded in at the end through `_sibling_parts`. The digest is over
`name::normalized-source` for every reached local name, sorted, plus those
sibling parts.

It returns `None` when the module has no module-level definition by that name,
rather than hashing an empty closure into a plausible-looking value.

`module_fingerprint` is the coarser companion for artifacts that no single entry
point owns: it hashes every module-level definition, so any change anywhere in
the module re-stamps the artifact, which is the correct reading when the artifact
is the module's collected output.
