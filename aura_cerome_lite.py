"""
Cerome-lite — Aura-inspired learner state for CogPace (zero preset).

Maps session behavior to MFA-relevant traits without importing CogArch:
  - sigma (σ): attention stability from response-time variance (Castellanos & Tannock, 2002 — ADHD σ)
  - baseline_S: emergent motivational field from accuracy + streak
  - load_bias: gentle difficulty modulation (high σ → smaller level jumps)

Aura reference: Cerome L1 neurochemistry modulates MFA field strength S in CogArch Arc 10.
Here we infer analogous scalars only from observable session stats.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class LearnerCerome:
    sigma: float
    baseline_s: float
    stability_label: str
    engagement_label: str
    difficulty_dampening: float

    def to_dict(self) -> dict[str, float | str]:
        return {
            "sigma": round(self.sigma, 3),
            "baseline_S": round(self.baseline_s, 3),
            "stability_label": self.stability_label,
            "engagement_label": self.engagement_label,
            "difficulty_dampening": round(self.difficulty_dampening, 2),
        }


def _rt_variance_ms(history: list[dict[str, Any]]) -> float:
    times = [float(h["time_ms"]) for h in history if "time_ms" in h]
    if len(times) < 2:
        return 0.0
    mean = sum(times) / len(times)
    var = sum((t - mean) ** 2 for t in times) / len(times)
    return var


def infer_learner_cerome(history: list[dict[str, Any]]) -> LearnerCerome:
    """Infer learner profile from session history — no char→trait lookup."""
    n = len(history)
    if n == 0:
        return LearnerCerome(
            sigma=0.0,
            baseline_s=1.0,
            stability_label="warming up",
            engagement_label="calibrating",
            difficulty_dampening=1.0,
        )

    rt_var = _rt_variance_ms(history)
    mean_rt = sum(h["time_ms"] for h in history) / n
    cv = math.sqrt(rt_var) / max(mean_rt, 1.0)

    sigma = min(1.0, cv)
    correct_rate = sum(1 for h in history if h.get("correct")) / n
    optimal_rate = sum(1 for h in history if h.get("state") == "OPTIMAL") / n
    baseline_s = 0.85 + 0.3 * correct_rate + 0.15 * optimal_rate

    if sigma >= 0.55:
        stability_label = "volatile focus"
        dampening = 0.5
    elif sigma >= 0.3:
        stability_label = "moderate stability"
        dampening = 0.75
    else:
        stability_label = "steady focus"
        dampening = 1.0

    if optimal_rate >= 0.5 and correct_rate >= 0.7:
        engagement_label = "hyperfocus-prone"
    elif sum(1 for h in history if h.get("state") == "OVERLOADED") / n >= 0.35:
        engagement_label = "load-sensitive"
    elif sum(1 for h in history if h.get("state") == "UNDERLOADED") / n >= 0.4:
        engagement_label = "underload-prone"
    else:
        engagement_label = "balanced"

    return LearnerCerome(
        sigma=round(sigma, 3),
        baseline_s=round(baseline_s, 3),
        stability_label=stability_label,
        engagement_label=engagement_label,
        difficulty_dampening=dampening,
    )


def adjust_difficulty_delta(raw_delta: int, cerome: LearnerCerome) -> int:
    """Apply Cerome dampening — volatile learners get gentler level swings."""
    if raw_delta == 0:
        return 0
    scaled = raw_delta * cerome.difficulty_dampening
    if abs(scaled) < 0.5:
        return 0
    return int(math.copysign(max(1, round(abs(scaled))), scaled))


def cerome_career_hint(cerome: LearnerCerome, subject: str | None) -> str:
    """Short career-coaching blurb for youth_code_education profile."""
    subj = subject or "STEM"
    hints = {
        "hyperfocus-prone": (
            f"Your session shows deep OPTIMAL engagement in {subj} — research labs, olympiad prep, "
            "or long-form engineering projects often fit this pattern."
        ),
        "load-sensitive": (
            f"You hit OVERLOADED states often in {subj} — clinical/supportive STEM paths "
            "(medicine, psych, education tech) may suit a scaffolding-first style."
        ),
        "underload-prone": (
            f"You trend UNDERLOADED in {subj} — fast-paced fields (trading tech, startup CS, "
            "competition math) might need more challenge to stay engaged."
        ),
        "balanced": (
            f"Balanced attention profile in {subj} — keep sampling subfields before specializing; "
            "your data doesn't scream one lane yet (that's okay)."
        ),
    }
    return hints.get(cerome.engagement_label, hints["balanced"])
