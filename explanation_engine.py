"""
Explanation engine — primary CogPace voice (deterministic).

LLM is NOT allowed to choose tone, depth, or difficulty — only optional polish
on already-composed MFA blocks (Aura P3 echo: affordance, not correction).
"""

from __future__ import annotations

from typing import Any, Optional

from gemini_adapter import _TOPIC_HOOKS
from mfa_pedagogy import PedagogyPlan, plan_pedagogy


def compose_explanation(plan: PedagogyPlan, topic: str) -> tuple[str, dict[str, Any]]:
    """Render PedagogyPlan to markdown + return audit trail."""
    lines: list[str] = []
    icons = {
        "challenge": "⚡",
        "curiosity": "😮",
        "scaffold": "⚠️",
        "ground": "🆘",
    }
    lines.append(f"{icons.get(plan.tone, '🧲')} **MFA tutor** · tone=`{plan.tone}` · depth={plan.depth}")
    lines.append("")

    for block in plan.blocks:
        lines.append(f"**{block.title}**")
        lines.append(block.body)
        lines.append("")

    hook = _TOPIC_HOOKS.get(topic)
    if hook and plan.depth >= 2 and plan.tone in ("challenge", "curiosity"):
        lines.append(f"**Field note ({topic}):** {hook}")
        lines.append("")

    lines.append("---")
    lines.append(
        f"*Decision trace: F_eff={plan.audit.get('effective_f')} · "
        f"Lenz={plan.audit.get('lenz_factor')} · "
        f"E_rem={plan.audit.get('energy_remaining')} · "
        f"σ={plan.audit.get('cerome_sigma')}*"
    )

    audit = {**plan.audit, "topic": topic, "source": "mfa_engine"}
    return "\n".join(lines), audit


def build_plan_and_explanation(
    *,
    snap,
    question: dict[str, Any],
    history: list[dict[str, Any]],
    response_time_ms: float,
    avg_rt: float,
    is_correct: bool,
    subject: str | None,
    cerome=None,
    spreading_topic: str | None = None,
) -> tuple[PedagogyPlan, str, dict[str, Any]]:
    plan = plan_pedagogy(
        snap_state=snap.state,
        f_att=snap.f_att,
        r=snap.r,
        S=snap.S,
        question=question,
        history=history,
        response_time_ms=response_time_ms,
        avg_rt=avg_rt,
        is_correct=is_correct,
        subject=subject,
        cerome=cerome,
        spreading_topic=spreading_topic,
    )
    text, audit = compose_explanation(plan, question.get("topic", "General"))
    return plan, text, audit


def followup_without_llm(
    user_message: str,
    *,
    topic: str,
    plan: Optional[PedagogyPlan],
    topic_hook: str | None = None,
) -> str:
    """Template follow-up from topic field + last pedagogy plan — no LLM."""
    msg = user_message.lower().strip()
    hook = topic_hook or _TOPIC_HOOKS.get(topic, "")

    if any(w in msg for w in ("why", "为啥", "为什么")):
        return (
            f"**Why ({topic}):** Start from the anchor in the last explanation. "
            f"MFA says your tone was `{plan.tone if plan else 'scaffold'}` — "
            f"I keep depth low until F_att recovers.\n\n{hook}"
        )
    if any(w in msg for w in ("example", "例子", "举例")):
        return (
            f"**Worked pattern:** Copy givens → formula → units. "
            f"For {topic}, the canonical explanation above *is* the minimal example."
        )
    if any(w in msg for w in ("career", "工作", "major")):
        return (
            f"**Career link:** {topic} shows up in olympiad prep, engineering labs, and ML feature design. "
            f"Your Cerome engagement label in the sidebar is the honest signal — not a personality quiz."
        )
    return (
        f"**On {topic}:** {hook or 'Break the stem into knowns vs unknowns.'}\n\n"
        f"Ask *why*, *example*, or *career* for structured follow-ups (no LLM needed)."
    )
