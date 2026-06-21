"""
MFA Attention Scoring Module — CogPace
Based on: Magnetic Field Model of Attention (Zeng, 2026)

Core Formula: F_att(r) = S / r²
  - r: psychological distance proxy (derived from response behavior)
  - S: field strength (motivation + streak-based momentum)

Attention States:
  OPTIMAL        — high engagement, right difficulty
  UNDERLOADED    — too easy / bored
  APPROACHING    — cognitive load rising, approaching limit
  OVERLOADED     — too hard / confused, attention collapse
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class AttentionSnapshot:
    state: str          # OPTIMAL / UNDERLOADED / APPROACHING / OVERLOADED
    f_att: float        # Raw field strength value
    r: float            # Psychological distance proxy
    S: float            # Field strength
    confidence: float   # 0–1, how confident the model is (based on data volume)
    message: str        # Human-readable note for the student


def compute_attention(
    response_time_ms: float,
    is_correct: bool,
    streak: int,
    avg_response_time_ms: float,
    n_answered: int,
) -> AttentionSnapshot:
    """
    Compute the attention field strength based on MFA theory.

    Parameters
    ----------
    response_time_ms     : Time taken to answer this question (milliseconds)
    is_correct           : Whether the answer was correct
    streak               : Current streak of correct answers
    avg_response_time_ms : Running average response time for this session
    n_answered           : Total questions answered so far (for confidence)

    Returns
    -------
    AttentionSnapshot with state, raw F_att, r, S, confidence, and message
    """
    if avg_response_time_ms <= 0:
        avg_response_time_ms = response_time_ms

    # --- Compute r (psychological distance proxy) ---
    # Intuition: r measures "how far the student's mind is from the task"
    # Slow + wrong = high distance (mind is wandering or overloaded)
    # Fast + correct = low distance (deeply engaged)
    speed_ratio = response_time_ms / max(avg_response_time_ms, 1.0)

    if is_correct:
        # Correct answer: lower psychological distance
        if speed_ratio < 0.5:
            # Very fast + correct → possibly underloaded (too easy, not really thinking)
            r = 0.3
        else:
            # Normal/slow but correct → engaged
            r = max(0.4, speed_ratio * 0.5)
    else:
        # Wrong answer: higher psychological distance
        if speed_ratio < 0.4:
            # Very fast + wrong → guessing / not engaged (underloaded)
            r = 1.8
        elif speed_ratio > 2.5:
            # Very slow + wrong → struggling, overloaded
            r = 3.5
        else:
            # Normal speed + wrong → approaching limit
            r = speed_ratio * 1.5

    # Clamp r to prevent division by near-zero
    r = max(r, 0.1)

    # --- Compute S (field strength = motivation × relevance proxy) ---
    # Streak-based momentum: longer streak = stronger engagement field
    streak_bonus = min(streak * 0.15, 1.0)   # cap bonus at +1.0
    S = 1.0 + streak_bonus

    # Penalize S slightly on wrong answers (attention "weakens" on failure)
    if not is_correct:
        S *= 0.85

    # --- Core MFA formula ---
    F_att = S / (r ** 2)

    # --- Classify state ---
    if F_att >= 2.0:
        state = "OPTIMAL"
        message = "🌟 You're in the zone! Keep going."
    elif F_att >= 0.8:
        state = "UNDERLOADED"
        message = "😴 This might be a bit easy. Let's raise the challenge."
    elif F_att >= 0.25:
        state = "APPROACHING"
        message = "⚠️ Attention is straining. Let's slow down and clarify."
    else:
        state = "OVERLOADED"
        message = "🆘 Cognitive overload detected. Time to simplify and reground."

    # --- Confidence: lower when few data points ---
    confidence = min(1.0, n_answered / 5.0)

    return AttentionSnapshot(
        state=state,
        f_att=round(F_att, 3),
        r=round(r, 3),
        S=round(S, 3),
        confidence=round(confidence, 2),
        message=message,
    )


def snapshot_with_effective_r(
    snap: AttentionSnapshot,
    r_effective: float,
    n_answered: int,
) -> AttentionSnapshot:
    """Re-score after topic magnetization lowers r (induced magnetization)."""
    r_effective = max(r_effective, 0.08)
    f_att = snap.S / (r_effective ** 2)
    if f_att >= 2.0:
        state, message = "OPTIMAL", "🌟 You're in the zone! Keep going."
    elif f_att >= 0.8:
        state, message = "UNDERLOADED", "😴 This might be a bit easy. Let's raise the challenge."
    elif f_att >= 0.25:
        state, message = "APPROACHING", "⚠️ Attention is straining. Let's slow down and clarify."
    else:
        state, message = "OVERLOADED", "🆘 Cognitive overload detected. Time to simplify and reground."
    confidence = min(1.0, n_answered / 5.0)
    return AttentionSnapshot(
        state=state,
        f_att=round(f_att, 3),
        r=round(r_effective, 3),
        S=snap.S,
        confidence=round(confidence, 2),
        message=message,
    )


def state_to_difficulty_delta(state: str) -> int:
    """
    Suggest a difficulty adjustment based on attention state.
    Returns an integer delta: -1 (easier), 0 (same), +1 (harder), +2 (challenge)
    """
    mapping = {
        "OPTIMAL": 1,
        "UNDERLOADED": 2,
        "APPROACHING": -1,
        "OVERLOADED": -1,
    }
    return mapping.get(state, 0)


def state_to_color(state: str) -> str:
    """Return a hex color for displaying the attention gauge."""
    colors = {
        "OPTIMAL": "#22c55e",       # green
        "UNDERLOADED": "#f59e0b",   # amber
        "APPROACHING": "#f97316",   # orange
        "OVERLOADED": "#ef4444",    # red
    }
    return colors.get(state, "#6b7280")


def compute_session_trend(history: list) -> str:
    """
    Analyze recent performance trend from session history.
    Returns: 'improving', 'declining', 'stable', or 'early'
    """
    if len(history) < 3:
        return "early"
    recent = history[-4:]
    correct_count = sum(1 for h in recent if h.get("correct", False))
    if correct_count >= 3:
        return "improving"
    elif correct_count <= 1:
        return "declining"
    return "stable"


def state_to_gemini_instruction(
    state: str,
    topic: str,
    wrong_answer_context: Optional[str] = None,
    session_stats: Optional[dict] = None,
) -> str:
    """
    Generate a prompt modifier for Gemini based on the current attention state.
    This tells Gemini HOW to explain the next concept.

    session_stats (optional):
        score, total, streak, accuracy_pct, trend ('improving'/'declining'/'stable'/'early')
    """
    base = f"The student is studying {topic}."
    if wrong_answer_context:
        base += f" They just answered this question incorrectly: '{wrong_answer_context}'."

    # Add session context if available
    if session_stats:
        acc = session_stats.get("accuracy_pct", 0)
        streak = session_stats.get("streak", 0)
        trend = session_stats.get("trend", "early")
        total = session_stats.get("total", 0)
        ctx = (
            f" Session context: {total} questions answered, {acc:.0f}% accuracy, "
            f"current streak of {streak}, trend is {trend}."
        )
        base += ctx

    if state == "OPTIMAL":
        return (
            f"{base} They are in OPTIMAL attention state — deeply engaged, fast accurate responses. "
            f"Push their thinking with a challenging 'what if?' extension or an unexpected connection "
            f"to a more advanced concept. Be intellectually stimulating. Keep it under 100 words."
        )
    elif state == "UNDERLOADED":
        return (
            f"{base} They seem UNDERLOADED — possibly bored or finding it too easy. "
            f"Re-ignite curiosity with a surprising or counterintuitive fact about this topic. "
            f"Use 'wait, did you know...?' framing. Make them lean in. Under 100 words."
        )
    elif state == "APPROACHING":
        return (
            f"{base} Their cognitive load is APPROACHING its limit — response patterns suggest strain. "
            f"Give a clear, step-by-step clarification with one concrete real-world analogy. "
            f"Avoid jargon. End with a single key takeaway sentence. Under 100 words."
        )
    else:  # OVERLOADED
        return (
            f"{base} They are COGNITIVELY OVERLOADED — confused, slow responses, possibly anxious. "
            f"Respond with warmth and radical simplicity: one core idea in one sentence, "
            f"one real-world example. Then suggest a brief mental reset (breathe, picture something familiar). "
            f"Be a calm, supportive mentor. Under 80 words."
        )
