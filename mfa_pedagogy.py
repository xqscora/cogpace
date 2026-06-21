"""
MFA pedagogy planner — deterministic teaching decisions (NOT LLM).

Maps attention physics + Cerome + session energy to structure:
  - Lenz's law: subject switch → temporary S dampening (Monsell, 2003 / MFA inertia)
  - Energy conservation: E1+E2 ≤ E_total - E_min (Kahneman, 1973 / MFA)
  - Capture: peripheral pull when fast-guess wrong (Lavie, 1995 / F_p > S/r²)

Zero preset: no student-type→script tables; continuous functions of observables only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional

from aura_cerome_lite import LearnerCerome, infer_learner_cerome


@dataclass
class PedagogyBlock:
    kind: str
    title: str
    body: str


@dataclass
class PedagogyPlan:
    tone: str
    depth: int
    blocks: list[PedagogyBlock]
    lenz_factor: float
    energy_remaining: float
    capture_risk: bool
    audit: dict[str, Any] = field(default_factory=dict)


def _session_energy(history: list[dict[str, Any]], n_answered: int) -> tuple[float, float, float]:
    """E_total scales with session length; E_used from level-weighted load."""
    e_total = 4.0 + 0.35 * max(n_answered, len(history))
    e_min = 0.8
    e_used = 0.0
    for h in history:
        lvl = float(h.get("level", 2))
        load = lvl * (1.0 if not h.get("correct", True) else 0.55)
        if h.get("state") in ("APPROACHING", "OVERLOADED"):
            load *= 1.25
        e_used += load
    return e_total, e_used, e_min


def _lenz_factor(history: list[dict[str, Any]], current_subject: str | None) -> float:
    """Switch cost — recent subject change dampens effective S."""
    if len(history) < 2 or not current_subject:
        return 1.0
    recent_subjects = [h.get("subject") for h in history[-3:] if h.get("subject")]
    if not recent_subjects:
        return 1.0
    switches = sum(
        1 for i in range(1, len(recent_subjects))
        if recent_subjects[i] != recent_subjects[i - 1]
    )
    if current_subject != history[-1].get("subject") and history[-1].get("subject"):
        switches += 1
    return max(0.55, 1.0 - 0.15 * switches)


def _capture_risk(
    response_time_ms: float,
    avg_rt: float,
    is_correct: bool,
    f_att: float,
) -> bool:
    """Fast wrong ≈ peripheral capture (low main-task engagement)."""
    if is_correct or avg_rt <= 0:
        return False
    speed_ratio = response_time_ms / avg_rt
    return speed_ratio < 0.45 and f_att < 0.9


def plan_pedagogy(
    *,
    snap_state: str,
    f_att: float,
    r: float,
    S: float,
    question: dict[str, Any],
    history: list[dict[str, Any]],
    response_time_ms: float,
    avg_rt: float,
    is_correct: bool,
    subject: str | None,
    cerome: Optional[LearnerCerome] = None,
    spreading_topic: str | None = None,
) -> PedagogyPlan:
    cerome = cerome or infer_learner_cerome(history)
    e_total, e_used, e_min = _session_energy(history, len(history))
    energy_remaining = max(0.0, e_total - e_min - e_used)
    lenz = _lenz_factor(history, subject)
    capture = _capture_risk(response_time_ms, avg_rt, is_correct, f_att)

    effective_f = f_att * lenz * (0.85 + 0.15 * min(1.0, energy_remaining / max(e_total - e_min, 0.1)))

    depth = int(max(1, min(4, round(1 + 3 * (effective_f / 2.5)))))
    if energy_remaining < 1.0:
        depth = min(depth, 2)
    if cerome.sigma > 0.5:
        depth = min(depth, max(1, depth - 1))

    if snap_state == "OPTIMAL" and not capture:
        tone = "challenge"
    elif snap_state == "UNDERLOADED":
        tone = "curiosity"
    elif snap_state == "APPROACHING":
        tone = "scaffold"
    else:
        tone = "ground"

    if capture:
        tone = "ground"
        depth = 1

    blocks: list[PedagogyBlock] = []
    canonical = question.get("explanation", "")
    topic = question.get("topic", "this topic")
    q_text = question.get("question", "")

    if not is_correct:
        blocks.append(PedagogyBlock(
            kind="misconception",
            title="Where the field slipped",
            body=f"You chose against: **{q_text}**. The canonical path starts from the givens in the stem.",
        ))

    blocks.append(PedagogyBlock(
        kind="anchor",
        title="Core",
        body=canonical,
    ))

    if depth >= 2 and spreading_topic:
        blocks.append(PedagogyBlock(
            kind="magnetization",
            title="Primed link",
            body=f"Your field still carries **{spreading_topic}** — same subject cluster, lower r_eff.",
        ))

    if tone == "challenge" and depth >= 3:
        blocks.append(PedagogyBlock(
            kind="extension",
            title="Push (OPTIMAL)",
            body=f"If F_att stays high, ask: what would change the answer if one givens doubled?",
        ))
    elif tone == "curiosity":
        blocks.append(PedagogyBlock(
            kind="hook",
            title="Re-engage",
            body=f"UNDERLOADED often means r is tiny but S is bored — try predicting before calculating.",
        ))
    elif tone == "scaffold":
        blocks.append(PedagogyBlock(
            kind="steps",
            title="Scaffold",
            body="1) List knowns → 2) Pick formula → 3) One unit check → 4) Match an option.",
        ))
    elif tone == "ground":
        blocks.append(PedagogyBlock(
            kind="reset",
            title="Ground",
            body="OVERLOADED: one breath, one sentence of the idea, then retry. Load theory says shrink the task.",
        ))

    if capture:
        blocks.append(PedagogyBlock(
            kind="capture",
            title="Capture warning",
            body="Fast miss suggests peripheral pull (Lavie): slow down 3s before clicking.",
        ))

    audit = {
        "snap_state": snap_state,
        "f_att": round(f_att, 3),
        "r": round(r, 3),
        "S": round(S, 3),
        "effective_f": round(effective_f, 3),
        "lenz_factor": round(lenz, 3),
        "energy_total": round(e_total, 2),
        "energy_used": round(e_used, 2),
        "energy_remaining": round(energy_remaining, 2),
        "cerome_sigma": cerome.sigma,
        "cerome_engagement": cerome.engagement_label,
        "tone": tone,
        "depth": depth,
        "capture_risk": capture,
        "decision": "MFA pedagogy engine (zero LLM)",
    }

    return PedagogyPlan(
        tone=tone,
        depth=depth,
        blocks=blocks,
        lenz_factor=lenz,
        energy_remaining=energy_remaining,
        capture_risk=capture,
        audit=audit,
    )
