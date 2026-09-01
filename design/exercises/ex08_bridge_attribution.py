"""Exercise 8 — three ways to get harmonic mass, and telling them apart.

"The certificate fired" is not a finding. Spec 1 names three generators of
harmonic mass, and only one of them is the signal:

  systematic       a rotational rule on the circle       -- persists; THIS is the signal
  innocent null    noisy, sparse, genuinely rankable     -- decays to eps^2
  incomparability  the integer/complex bridge            -- depends on the mode

This exercise holds the first two fixed and moves only the bridge, which has
three modes and three different behaviours. Two of the four columns below are
exact identities; the rest are one draw.

Run:  python design/exercises/ex08_bridge_attribution.py
Spec: 1, 2.3, 5.3, 7, 8.6.  Claim: bridge-invariance.
"""

import sys
from pathlib import Path

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rig import oracle
from rig.config import RigConfig
from rig.graph import assemble

RS = (2, 4, 8, 16, 32, 64, 128)


def energies(cfg, a):
    """The two readings rig.sweep.bridge_sweep reports, and they use DIFFERENT flows.

    h(total) is the ORACLE: the clean limit `Y_expected`, i.e. what infinite data
    converges to. Under it a fresh coin flip contributes nothing, because its
    expectation is zero -- which is the whole content of "variance decays".

    h(bridge only) is the REALISED draw `Y`, restricted to the bridge edges. That
    is where a finite-R coin flip is actually visible. Read the first column and
    the coin flip looks free; read the second and it does not.
    """
    total = oracle.projector_split(cfg.n_vertices, a.edges, a.Y_expected, "empty")
    cc = set(a.blocks["cc"].edges)
    ic = set(a.blocks["ic"].edges) if a.blocks.get("ic") else set()
    ref = oracle.projector_split(
        cfg.n_vertices, a.edges,
        np.array([a.Y_expected[i] if e in cc else 0.0 for i, e in enumerate(a.edges)]),
        "empty")
    br = oracle.projector_split(
        cfg.n_vertices, a.edges,
        np.array([a.Y[i] if e in ic else 0.0 for i, e in enumerate(a.edges)]),
        "empty")
    return (total["energies"]["harmonic"], ref["energies"]["harmonic"],
            br["energies"]["harmonic"])


def main():
    cfg = RigConfig().validate().with_(n_int=6, n_cplx=5, mode_II="clean_gradient")

    print("Part 1 -- the circle block alone, which is the reference every row is")
    print("          measured against.\n")
    a0 = assemble(cfg.with_(bridge_mode="bias_rule"))
    _, circle_only, _ = energies(cfg, a0)
    print(f"  harmonic energy of the C-C block on its own: {circle_only:.10f}")

    print("\nPart 2 -- add a bridge, three modes, seven budgets.\n")
    print(f"  {'mode':>15} {'R':>5} {'h(total)':>13} {'h(bridge only)':>15} "
          f"{'bridge RMS':>11} {'log(2R-1)':>10}")
    for mode in ("bias_rule", "variance_fresh", "variance_fixed"):
        for R in RS:
            c = cfg.with_(bridge_mode=mode, bridge_R=R)
            a = assemble(c)
            tot, _, br = energies(c, a)
            rms = a.blocks["ic"].rms()
            print(f"  {mode:>15} {R:5d} {tot:13.6f} {br:15.6f} {rms:11.4f} "
                  f"{np.log(2 * R - 1):10.4f}")
        print()

    print("Part 3 -- the same graph, but the bridge replaced by a CONSTANT flow.")
    print("          Potential-consistency is what makes part 2's first block exact.\n")
    a = assemble(cfg.with_(bridge_mode="bias_rule"))
    cc = set(a.blocks["cc"].edges)
    ic = set(a.blocks["ic"].edges)
    const = np.array([-1.0 if e in ic else a.Y_expected[i]
                      for i, e in enumerate(a.edges)])
    got = oracle.projector_split(cfg.n_vertices, a.edges, const, "empty")
    print(f"  potential-consistent bridge -> harmonic {energies(cfg, a)[0]:.10f}")
    print(f"  constant bridge             -> harmonic {got['energies']['harmonic']:.10f}")
    print(f"  circle block alone          -> harmonic {circle_only:.10f}")

    print("\nRECORD")
    print("  1. One mode's h(total) column is the same number at every R, to ten")
    print("     decimals. Name it and say what that number equals.")
    print("  2. variance_fresh is meant to decay as 1/R. Check the h(bridge only)")
    print("     column at R=16..128 -- then check R=2..8 and say what stops you")
    print("     reading those four rows as a decay curve.")
    print("  3. variance_fixed does not decay. Compare its bridge RMS against the")
    print("     log(2R-1) column, and say whether 'persists' is the right word.")
    print("  4. Part 3's constant bridge is also a fixed rule that never disagrees.")
    print("     Say, in one sentence, what it lacks that the bias_rule bridge has.")
    print("  5. The sharp one. On the bias_rule rows the bridge carries 47.73 of")
    print("     harmonic energy read on its own, and the whole config still reads")
    print("     10.00. Say how both are true at once, and what that means for anyone")
    print("     who wants to attribute harmonic mass to a block by measuring it alone.")


if __name__ == "__main__":
    main()
