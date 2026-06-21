"""
Unified AI tutor — Gemini live + rich offline fallback + follow-up chat.

Loads API key from sidebar, GEMINI_API_KEY, or GOOGLE_API_KEY (.env via python-dotenv).
Competition profile injects narrative-specific system prefix.
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

from gemini_adapter import _DEMO_RESPONSES, _TOPIC_HOOKS, _get_demo_response
from mfa_attention import state_to_gemini_instruction


def resolve_api_key(explicit: str | None = None) -> str | None:
    key = (explicit or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    return key or None


def get_explanation(
    *,
    state: str,
    topic: str,
    subject: str,
    wrong_answer_text: Optional[str] = None,
    api_key: Optional[str] = None,
    session_stats: Optional[dict] = None,
    profile: Optional[dict[str, Any]] = None,
) -> tuple[str, str]:
    """Returns (text, source) where source is 'gemini' or 'demo'."""
    key = resolve_api_key(api_key)
    if key:
        try:
            text = _call_gemini(
                state=state,
                topic=topic,
                subject=subject,
                wrong_answer_text=wrong_answer_text,
                api_key=key,
                session_stats=session_stats,
                profile=profile,
            )
            _track_ai("gemini", state, topic, subject, wrong_answer_text, session_stats)
            return text, "gemini"
        except Exception:
            pass

    text = _get_demo_response(state, subject, topic, session_stats)
    _track_ai("demo", state, topic, subject, wrong_answer_text, session_stats)
    return text, "demo"


def chat_followup(
    *,
    user_message: str,
    topic: str,
    subject: str,
    state: str,
    last_explanation: str,
    api_key: Optional[str] = None,
    profile: Optional[dict[str, Any]] = None,
    session_stats: Optional[dict] = None,
) -> tuple[str, str]:
    """Answer a student follow-up question in context."""
    key = resolve_api_key(api_key)
    prefix = (profile or {}).get("ai_system_prefix", "You are CogPace AI, a STEM tutor.")
    stats_line = ""
    if session_stats:
        stats_line = (
            f"Session: {session_stats.get('accuracy_pct', 0):.0f}% accuracy, "
            f"streak {session_stats.get('streak', 0)}, trend {session_stats.get('trend', 'early')}."
        )

    if key:
        try:
            import google.generativeai as genai

            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            prompt = (
                f"{prefix}\n\n"
                f"Student attention state: {state}. Subject: {subject}. Topic: {topic}. {stats_line}\n"
                f"Your last explanation:\n{last_explanation}\n\n"
                f"Student follow-up question:\n{user_message}\n\n"
                "Answer in under 150 words. Match tone to their attention state "
                "(challenge if OPTIMAL, simplify if OVERLOADED). Be warm and precise."
            )
            response = model.generate_content(prompt)
            return response.text.strip(), "gemini"
        except Exception:
            pass

    fallback = (
        f"**Offline mode:** Great question about {topic}.\n\n"
        f"Core idea: {_TOPIC_HOOKS.get(topic, 'Break the problem into what you know vs what you need.')}\n\n"
        f"*Add a Gemini API key in the sidebar for live follow-ups.*"
    )
    return fallback, "demo"


def _call_gemini(
    *,
    state: str,
    topic: str,
    subject: str,
    wrong_answer_text: Optional[str],
    api_key: str,
    session_stats: Optional[dict],
    profile: Optional[dict[str, Any]],
) -> str:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    instruction = state_to_gemini_instruction(state, topic, wrong_answer_text, session_stats)
    prefix = (profile or {}).get(
        "ai_system_prefix",
        "You are CogPace AI, an MFA-grounded STEM tutor.",
    )
    system_prompt = (
        f"{prefix} "
        "F_att(r)=S/r² measures engagement. "
        "Give SHORT responses (max 120 words) matching the student's attention state. "
        "Sound like a mentor, not a textbook."
    )
    response = model.generate_content(f"{system_prompt}\n\n{instruction}")
    return response.text.strip()


def _track_ai(
    source: str,
    state: str,
    topic: str,
    subject: str,
    wrong_answer_text: Optional[str],
    session_stats: Optional[dict],
) -> None:
    if not send_track_event:
        return
    send_track_event(
        "ai_explanation_generated",
        properties={
            "source": source,
            "attention_state": state,
            "topic": topic,
            "subject": subject,
            "has_wrong_answer_context": wrong_answer_text is not None,
            "session_trend": session_stats.get("trend") if session_stats else None,
            "accuracy_pct": round(session_stats.get("accuracy_pct", 0)) if session_stats else None,
            "streak": session_stats.get("streak") if session_stats else None,
        },
    )
