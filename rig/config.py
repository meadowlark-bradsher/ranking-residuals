"""Config schema for the calibration rig (spec §3), with the §2.6 regime gates.

Every field here appears in a sweep record, because §9 requires that any record
state the budget that produced it. The defaults are the spec §3 defaults.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, replace

# Spec §10 / §2.6: both of these are floored at 2, and the floor is enforced with a
# loud error rather than a silent default. At R=1 the instrument's clamp (1/(2k))
# pins phat to exactly 0.5 and every reconstructed flow is 0.
MIN_ROWS_PER_PAIR = 2

# Spec §2.6: the fit window. Not a tuning knob -- below this the O(1/k^2) logit-bias
# term of §7 is absorbed into the intercept (measured floor bias 0.83x-2.48x).
MIN_FIT_K = 64


@dataclass(frozen=True)
class BTLConfig:
    """The statistical-null generator (§2.4) and its fit window (§2.6)."""

    beta: float = 0.3                 # §2.6: anywhere in [0.15,0.30] works on k>=64
    p: float = 0.45                   # edge-retention (sparsity -> holes -> b1>0)
    k: tuple[int, ...] = (8, 16, 32, 64, 128, 256, 512, 1024)   # SAMPLING grid
    fit_k_min: int = MIN_FIT_K        # FITTING window: floor fitted on k >= this only
    theta_shape: str = "gamma"        # gamma | random  (gamma is the primary probe)
    gamma: tuple[float, ...] = (1.0, 1.5, 2.0, 3.0)             # 1.0 == symmetric
    standardize_theta: bool = True    # REQUIRED (§2.4)
    fixed_mask_across_k: bool = True  # REQUIRED (§2.4): P_h must not move with k

    def validate(self) -> None:
        if self.theta_shape not in ("gamma", "random"):
            raise ValueError(f"theta_shape must be gamma|random, got {self.theta_shape!r}")
        if not 0 < self.p <= 1:
            raise ValueError(f"p must be in (0,1], got {self.p}")
        if min(self.k) < 2:
            raise ValueError(f"k grid must start at >=2, got {min(self.k)}")
        if self.fit_k_min < MIN_FIT_K:
            raise ValueError(
                f"fit_k_min={self.fit_k_min} < {MIN_FIT_K}. Spec §2.6: below this the "
                "O(1/k^2) logit-bias term is absorbed into the intercept and the floor "
                "is biased 0.83x-2.48x. This is not a tuning knob."
            )
        if not any(k >= self.fit_k_min for k in self.k):
            raise ValueError(
                f"no k in {self.k} reaches fit_k_min={self.fit_k_min}; nothing to fit"
            )
        if not self.fixed_mask_across_k:
            raise ValueError(
                "fixed_mask_across_k=False violates §2.4: P_h would move with k and "
                "floor + c/k would not be well-posed."
            )


@dataclass(frozen=True)
class RigConfig:
    """One rig configuration (spec §3). Frozen + hashable so it can seed itself."""

    n_int: int = 8
    n_cplx: int = 5
    mode_II: str = "null_btl"          # clean_gradient | null_btl
    btl: BTLConfig = field(default_factory=BTLConfig)
    eps: tuple[float, ...] = (0.0, 0.1, 0.2, 0.4)   # §2.5 THE FLOOR AXIS
    complex_pool: str = "equal_spaced"  # equal_spaced | random | surrogate_defeating
    bridge_mode: str = "bias_rule"      # variance_fresh | bias_rule | variance_fixed
    bridge_gap: float = 1.0             # bias_rule offset below min(s_int)
    bridge_R: int = 8                   # comparisons per bridge pair; >= 2
    filling: str = "empty"              # rig calibration default (§4)
    mixed_triangles_filled: bool = False
    edge_density: float = 1.0
    block_scale: tuple[float, float, float] = (1.0, 1.0, 1.0)   # (ii, cc, ic) §5.7
    emit_k: int = 64                    # rows per pair for magnitude/sign blocks; >= 2.
                                        # 64 keeps the mixed-config round-trip deviation
                                        # ~2e-3 with no saturated edges; at 8 it is ~4e-2
                                        # and 5 bridge edges exceed log(2k-1) (§10).
    reps: int = 16                      # draws averaged per (seed,k) before the OLS fit.
                                        # A budget knob, logged like any other (§9).
    seeds: int = 64                     # replicates for the §8.5 floor CI
    seed: int = 0                       # base seed

    # ---- validation -----------------------------------------------------
    def validate(self) -> RigConfig:
        self.btl.validate()
        if self.mode_II not in ("clean_gradient", "null_btl"):
            raise ValueError(f"mode_II must be clean_gradient|null_btl, got {self.mode_II!r}")
        if self.complex_pool not in ("equal_spaced", "random", "surrogate_defeating"):
            raise ValueError(f"unknown complex_pool: {self.complex_pool!r}")
        if self.bridge_mode not in ("variance_fresh", "bias_rule", "variance_fixed"):
            raise ValueError(f"unknown bridge_mode: {self.bridge_mode!r}")
        if self.filling not in ("empty", "observed", "full", "custom"):
            raise ValueError(f"unknown filling: {self.filling!r}")
        for name, val in (("bridge_R", self.bridge_R), ("emit_k", self.emit_k)):
            if val < MIN_ROWS_PER_PAIR:
                raise ValueError(
                    f"{name}={val} < {MIN_ROWS_PER_PAIR}. Spec §10: analyze_comparisons "
                    f"clamps phat to 1/(2k), so a single row per pair yields Y=0 on every "
                    f"edge and total_mass=0. Emission needs >= {MIN_ROWS_PER_PAIR} rows."
                )
        if self.n_cplx == 1:
            raise ValueError("n_cplx=1 gives no C-C edges; use 0 or >=2")
        if self.n_cplx >= 2 and self.n_cplx % 2 == 0 and self.complex_pool == "equal_spaced":
            raise ValueError(
                f"n_cplx={self.n_cplx} is even: equal spacing puts antipodal pairs at "
                "exactly pi, an undefined comparison (§2.2). Use odd m."
            )
        if any(s <= 0 for s in self.block_scale):
            raise ValueError(f"block_scale entries must be > 0, got {self.block_scale}")
        if not 0 < self.edge_density <= 1:
            raise ValueError(f"edge_density must be in (0,1], got {self.edge_density}")
        return self

    # ---- identity / reproducibility --------------------------------------
    @property
    def n_vertices(self) -> int:
        return self.n_int + self.n_cplx

    @property
    def complex_fraction(self) -> float:
        return self.n_cplx / self.n_vertices if self.n_vertices else 0.0

    def echo(self) -> dict:
        """Full config as plain JSON-able data -- §9 requires this in every record."""
        d = asdict(self)
        d["block_scale"] = {"ii": self.block_scale[0],
                            "cc": self.block_scale[1],
                            "ic": self.block_scale[2]}
        return d

    def fingerprint(self) -> str:
        """Stable hash of the config -- same config => same seed => same output (§9)."""
        blob = json.dumps(self.echo(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def derive_seed(self, *tags) -> int:
        """Per-config, per-purpose seed. Deterministic in (base seed, config, tags)."""
        h = hashlib.sha256(f"{self.seed}|{self.fingerprint()}|{'|'.join(map(str, tags))}".encode())
        return int.from_bytes(h.digest()[:8], "big") % (2**63)

    def with_(self, **kw) -> RigConfig:
        return replace(self, **kw).validate()


def quick(cfg: RigConfig) -> RigConfig:
    """--quick: fewer seeds, shorter k grid. Still respects the §2.6 fit window."""
    k = tuple(k for k in cfg.btl.k if k >= 32)[:4] or cfg.btl.k
    if not any(x >= cfg.btl.fit_k_min for x in k):
        k = tuple(x for x in cfg.btl.k if x >= cfg.btl.fit_k_min)[:3]
    return cfg.with_(
        seeds=max(8, cfg.seeds // 8),
        reps=max(4, cfg.reps // 4),
        btl=replace(cfg.btl, k=k, gamma=cfg.btl.gamma[:2]),
        eps=cfg.eps[:3],
    )


def budget_echo(cfg: RigConfig, is_quick: bool) -> dict:
    """§9: every record states the budget that produced it."""
    return {
        "seeds": cfg.seeds,
        "reps": cfg.reps,
        "k_grid": list(cfg.btl.k),
        "fit_k_min": cfg.btl.fit_k_min,
        "gamma_grid": list(cfg.btl.gamma),
        "eps_grid": list(cfg.eps),
        "quick": is_quick,
        "config_fingerprint": cfg.fingerprint(),
    }
