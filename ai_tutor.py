"""
AI layer — OPTIONAL polish only. Pedagogy is decided by mfa_pedagogy + explanation_engine.

Default path: mfa_engine (deterministic).
LLM: rephrase only; cannot change tone/depth/blocks (Cora zero-preset / P3 echo rule).
"""

from __future__ import annotations

import os
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()

try:
    from integrations.pendo_track import send_track_event
except ImportError:
    send_track_event = None  # type: ignore[misc, assignment]

from explanation_engine import build_plan_and_explanation, followup_without_llm
from mfa_pedagogy import PedagogyPlan


def resolve_api_key(explicit: str | None = None) -> str | None:
    key = (explicit or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    return key or None


def llm_polish_enabled(profile: Optional[dict[str, Any]]) -> bool:
    if not profile:
        return False
    return bool(profile.get("features", {}).get("llm_polish", False))


def get_explanation(
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
    api_key: Optional[str] = None,
    profile: Optional[dict[str, Any]] = None,
    session_stats: Optional[dict] = None,
) -> tuple[str, str, PedagogyPlan, dict[str, Any]]:
    """
    Returns (text, source, plan, audit).
    source ∈ {'mfa_engine', 'mfa_engine+polish', 'mfa_engine'} — never raw 'gemini'.
    """
    plan, text, audit = build_plan_and_explanation(
        snap=snap,
        question=question,
        history=history,
        response_time_ms=response_time_ms,
        avg_rt=avg_rt,
        is_correct=is_correct,
        subject=subject,
        cerome=cerome,
        spreading_topic=spreading_topic,
    )
    source = "mfa_engine"

    if llm_polish_enabled(profile) and resolve_api_key(api_key):
        polished = _polish_only(text, plan, api_key)
        if polished:
            text = polished
            source = "mfa_engine+polish"
            audit["polish"] = True

    _track(source, plan, question, session_stats)
    return text, source, plan, audit


def chat_followup(
    *,
    user_message: str,
    topic: str,
    plan: Optional[PedagogyPlan],
    api_key: Optional[str] = None,
    profile: Optional[dict[str, Any]] = None,
) -> tuple[str, str]:
    text = followup_without_llm(user_message, topic=topic, plan=plan)
    source = "mfa_followup"

    if llm_polish_enabled(profile) and resolve_api_key(api_key):
        polished = _polish_followup(text, user_message, topic, api_key)
        if polished:
            return polished, "mfa_followup+polish"

    return text, source


def _polish_only(text: str, plan: PedagogyPlan, api_key: str) -> str | None:
    """Rephrase for readability — MUST preserve all pedagogical claims."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = (
            "Rephrase for clarity ONLY. Do NOT add facts, change tone, or change teaching depth. "
            f"Locked tone={plan.tone}, depth={plan.depth}. Keep markdown structure.\n\n"
            f"{text}"
        )
        return model.generate_content(prompt).text.strip()
    except Exception:
        return None


def _polish_followup(text: str, user_message: str, topic: str, api_key: str) -> str | None:
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = (
            f"Polish wording only. Topic={topic}. Student asked: {user_message}\n\n"
            f"Draft (keep all claims):\n{text}"
        )
        return model.generate_content(prompt).text.strip()
    except Exception:
        return None


def _track(
    source: str,
    plan: PedagogyPlan,
    question: dict[str, Any],
    session_stats: Optional[dict],
) -> None:
    if not send_track_event:
        return
    send_track_event(
        "mfa_explanation_generated",
        properties={
            "source": source,
            "tone": plan.tone,
            "depth": plan.depth,
            "topic": question.get("topic"),
            "capture_risk": plan.capture_risk,
            "session_trend": session_stats.get("trend") if session_stats else None,
        },
    )
