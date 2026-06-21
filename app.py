"""
CogPace — Attention-Aware STEM Tutor
Built for DSH Hacks V1 | Theme: AI × STEM Education

Author: Cora Zeng
Theoretical foundation: Magnetic Field Model of Attention (MFA)
  — published as preprint, Frontiers in Psychology 2026

v3.0 — Competition profiles, Aura Cerome-lite, live AI chat follow-ups,
        per-hackathon narratives (see competition_profiles/ + narratives/).
"""

import json
import os
import random
import time
from typing import Any, Optional

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from ai_tutor import chat_followup, get_explanation, resolve_api_key
from aura_cerome_lite import (
    adjust_difficulty_delta,
    cerome_career_hint,
    infer_learner_cerome,
)
from competition_profiles import list_profile_ids, load_profile, resolve_profile_from_query
from mfa_attention import compute_attention, snapshot_with_effective_r, state_to_color, state_to_difficulty_delta
from topic_field import TopicField

try:
    from integrations.splunk_hec import send_attention_event
except ImportError:
    send_attention_event = None  # type: ignore[misc, assignment]

try:
    from integrations.pendo_track import send_track_event
except ImportError:
    send_track_event = None  # type: ignore[misc, assignment]

try:
    from integrations.event_log import append_event, export_session_summary
except ImportError:
    append_event = None  # type: ignore[misc, assignment]
    export_session_summary = None  # type: ignore[misc, assignment]

from integrations.pendo import inject_pendo

# ──────────────────────────── CONFIG ────────────────────────────
SESSION_LENGTH = 12          # Questions per session before showing summary

st.set_page_config(
    page_title="CogPace — STEM Tutor",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────── GLOBAL CSS ────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
[data-testid="stAppViewContainer"] {
    background: #0b0f1a;
}
[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid #1f2937;
}
/* ── Option buttons ── */
.stButton > button {
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 0.55em 1em;
    font-size: 0.95rem;
    transition: all 0.15s ease;
    text-align: left;
}
.stButton > button:hover {
    background: #7c3aed;
    border-color: #7c3aed;
    color: white;
    transform: translateX(3px);
}
/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #1e293b;
    border-radius: 10px;
    padding: 10px;
    border: 1px solid #334155;
}
/* ── Progress ── */
.progress-bar-outer {
    background: #1e293b;
    border-radius: 8px;
    height: 10px;
    width: 100%;
    margin: 6px 0 14px;
    overflow: hidden;
    border: 1px solid #334155;
}
.progress-bar-inner {
    height: 100%;
    border-radius: 8px;
    background: linear-gradient(90deg, #7c3aed, #06b6d4);
    transition: width 0.3s ease;
}
/* ── Achievement badge ── */
.achievement-badge {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: white;
    padding: 6px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
    display: inline-block;
    margin: 4px 0;
    animation: pulse 0.6s ease;
}
@keyframes pulse {
    0% { transform: scale(0.95); opacity: 0.7; }
    50% { transform: scale(1.05); opacity: 1; }
    100% { transform: scale(1); opacity: 1; }
}
/* ── Summary card ── */
.summary-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 20px 24px;
    margin: 12px 0;
}
/* ── Topic tag ── */
.topic-tag {
    background: #312e81;
    color: #c4b5fd;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    display: inline-block;
    margin: 2px;
}
/* ── Persona header ── */
.persona-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: linear-gradient(90deg, #1e1b4b, #1e293b);
    border-radius: 10px;
    border: 1px solid #4338ca;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

SUBJECT_LABELS = {
    "physics": "⚡ Physics",
    "math": "∑ Mathematics",
    "chemistry": "🧪 Chemistry",
    "cs": "💻 Computer Science",
}

SUBJECT_COLORS = {
    "physics": "#06b6d4",
    "math": "#8b5cf6",
    "chemistry": "#10b981",
    "cs": "#f59e0b",
}

STREAK_MILESTONES = {
    3:  ("🔥 On Fire!", "3-question streak — you're warming up."),
    5:  ("⚡ Charged!", "5-question streak — attention field is strong."),
    7:  ("🌟 Zone State!", "7 correct in a row — optimal attention detected."),
    10: ("🚀 Unstoppable!", "10-question streak — textbook hyperfocus."),
    15: ("🧲 Maximum Field!", "15 streak — field strength at theoretical maximum."),
}


# ──────────────────────────── DATA LOADING ────────────────────────────
@st.cache_data
def load_questions():
    q_path = os.path.join(os.path.dirname(__file__), "questions.json")
    with open(q_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────── SESSION STATE ────────────────────────────
def init_state():
    defaults = {
        "subject": None,
        "level_map": {},
        "seen_ids": set(),           # track shown question IDs
        "current_question": None,
        "answered": False,
        "selected_option": None,
        "q_start_time": None,
        "session_history": [],
        "streak": 0,
        "score": 0,
        "total": 0,
        "attention_state": None,
        "attention_snap": None,
        "explanation": None,
        "current_level": 2,
        "gemini_api_key": "",
        "game_started": False,
        "session_complete": False,
        "attention_history": [],     # list of states for mini-chart
        "f_att_history": [],         # list of (question_num, f_att) tuples for line chart
        "splunk_session_id": None,  # stable id for HEC events
        "chat_messages": [],
        "ai_source": "demo",
        "profile_id": None,
        "topic_field": None,
        "last_pedagogy_plan": None,
        "pedagogy_audit": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_active_profile() -> dict[str, Any]:
    if st.session_state.get("_profile_cache"):
        return st.session_state["_profile_cache"]
    qp = st.query_params.get("profile")
    if qp:
        prof = resolve_profile_from_query(qp)
    else:
        prof = load_profile(st.session_state.get("profile_id"))
    st.session_state["_profile_cache"] = prof
    return prof


def profile_feature(name: str) -> bool:
    return bool(get_active_profile().get("features", {}).get(name, False))


def get_avg_response_time() -> float:
    if not st.session_state.session_history:
        return 15000.0
    times = [h["time_ms"] for h in st.session_state.session_history]
    return sum(times) / len(times)


def select_question(level_map: dict, level: int) -> Optional[dict]:
    """Pick a question at the target level, avoiding already-seen questions."""
    seen = st.session_state.seen_ids
    for delta in [0, 1, -1, 2, -2, 3, -3]:
        target = level + delta
        bucket = [q for q in level_map.get(target, []) if q["id"] not in seen]
        if bucket:
            return random.choice(bucket)
    # All questions seen — reset seen set and pick from all
    st.session_state.seen_ids = set()
    all_q = [q for qs in level_map.values() for q in qs]
    return random.choice(all_q) if all_q else None


def build_level_map(questions: list) -> dict:
    level_map = {}
    for q in questions:
        lvl = q.get("level", 2)
        level_map.setdefault(lvl, []).append(q)
    return level_map


def start_session(subject: str):
    all_q = load_questions()
    subject_q = all_q.get(subject, [])
    st.session_state.subject = subject
    st.session_state.level_map = build_level_map(subject_q)
    st.session_state.seen_ids = set()
    st.session_state.current_level = 2
    st.session_state.session_history = []
    st.session_state.streak = 0
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.attention_state = None
    st.session_state.attention_snap = None
    st.session_state.explanation = None
    st.session_state.answered = False
    st.session_state.selected_option = None
    st.session_state.game_started = True
    st.session_state.session_complete = False
    st.session_state.attention_history = []
    st.session_state.f_att_history = []
    st.session_state.splunk_session_id = f"cogpace-{int(time.time())}-{random.randint(1000, 9999)}"
    st.session_state.chat_messages = []
    st.session_state.ai_source = "mfa_engine"
    st.session_state.topic_field = TopicField.from_question_bank(load_questions())
    st.session_state.last_pedagogy_plan = None
    st.session_state.pedagogy_audit = None

    q = select_question(st.session_state.level_map, 2)
    st.session_state.current_question = q
    if q:
        st.session_state.seen_ids.add(q["id"])
    st.session_state.q_start_time = time.time()

    # Pendo: session_started
    if send_track_event:
        total_available = sum(len(qs) for qs in st.session_state.level_map.values())
        send_track_event(
            "session_started",
            visitor_id=st.session_state.splunk_session_id or "anonymous",
            properties={
                "subject": subject,
                "session_id": st.session_state.splunk_session_id,
                "total_questions_available": total_available,
                "initial_difficulty_level": 2,
            },
        )


def next_question():
    if st.session_state.total >= SESSION_LENGTH:
        st.session_state.session_complete = True
        return

    prev_level = st.session_state.current_level
    att_state = st.session_state.attention_state or "OPTIMAL"
    raw_delta = state_to_difficulty_delta(att_state)
    if profile_feature("cerome_panel"):
        cerome = infer_learner_cerome(st.session_state.session_history)
        delta = adjust_difficulty_delta(raw_delta, cerome)
    else:
        delta = raw_delta
    new_level = max(1, min(5, prev_level + delta))
    st.session_state.current_level = new_level

    # Pendo: difficulty_level_adjusted
    if send_track_event and new_level != prev_level:
        send_track_event(
            "difficulty_level_adjusted",
            visitor_id=st.session_state.splunk_session_id or "anonymous",
            properties={
                "previous_level": prev_level,
                "new_level": new_level,
                "difficulty_delta": delta,
                "attention_state": att_state,
                "subject": st.session_state.subject,
                "question_number": st.session_state.total,
            },
        )

    q = select_question(st.session_state.level_map, new_level)
    st.session_state.current_question = q
    if q:
        st.session_state.seen_ids.add(q["id"])
    st.session_state.answered = False
    st.session_state.selected_option = None
    st.session_state.explanation = None
    st.session_state.q_start_time = time.time()


# ──────────────────────────── UI HELPERS ────────────────────────────
def render_attention_gauge(state: str, f_att: float):
    color = state_to_color(state)
    display_pct = min(100, int(f_att / 4.0 * 100))
    labels = {
        "OPTIMAL": "⚡ Optimal",
        "UNDERLOADED": "😴 Underloaded",
        "APPROACHING": "⚠️ Approaching Limit",
        "OVERLOADED": "🆘 Overloaded",
    }
    label = labels.get(state, state)
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, {color} {display_pct}%, #1e293b {display_pct}%);
        height: 28px; border-radius: 14px;
        display: flex; align-items: center; padding: 0 12px;
        font-size: 13px; font-weight: 600; color: white;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5); margin-bottom: 8px;
    ">{label} &nbsp; F<sub>att</sub> = {f_att:.2f}</div>
    """, unsafe_allow_html=True)


def render_progress_bar():
    done = st.session_state.total
    pct = int(done / SESSION_LENGTH * 100)
    st.markdown(f"""
    <div style="font-size:12px; color:#94a3b8; margin-bottom:4px;">
        Progress: {done} / {SESSION_LENGTH} questions
    </div>
    <div class="progress-bar-outer">
        <div class="progress-bar-inner" style="width:{pct}%"></div>
    </div>
    """, unsafe_allow_html=True)


def render_mfa_info_box():
    st.markdown("""
    <div style="
        background: #0f172a; border: 1px solid #334155;
        border-radius: 10px; padding: 14px 16px;
        font-size: 12px; color: #94a3b8; margin-top: 16px;
    ">
    <strong style="color:#7c3aed">🧲 MFA Theory</strong><br>
    CogPace models your attention using the <em>Magnetic Field Model</em>:<br>
    <code style="color:#a78bfa">F<sub>att</sub>(r) = S / r²</code><br>
    <code>r</code> = psychological distance &nbsp;|&nbsp; <code>S</code> = field strength<br>
    <span style="color:#64748b">Research by Cora Zeng (2026)</span>
    </div>
    """, unsafe_allow_html=True)


def render_persona_header(state: Optional[str] = None):
    """Render the CogPace AI tutor persona header."""
    prof = get_active_profile()
    persona = prof.get("persona_name", "CogPace AI")
    persona_msg = {
        "OPTIMAL": "You're in the zone — let's push further. 🚀",
        "UNDERLOADED": "Looks easy for you — I'm raising the challenge. ⚡",
        "APPROACHING": "Slowing down together — clarity over speed. 🌊",
        "OVERLOADED": "Taking a breath. Let's ground this. 🧘",
        None: "Ready to map your attention field. 🧲",
    }
    msg = persona_msg.get(state)
    subj_color = SUBJECT_COLORS.get(st.session_state.subject or "physics", "#7c3aed")
    accent = prof.get("accent_color", "#4338ca")
    st.markdown(f"""
    <div class="persona-header" style="border-color:{accent}">
        <div style="font-size:2rem">🤖</div>
        <div>
            <div style="font-weight:700; color:#c4b5fd; font-size:0.9rem">{persona}</div>
            <div style="font-size:0.82rem; color:#94a3b8">{msg}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_achievement(streak: int):
    """Show achievement badge if streak hits a milestone."""
    if streak in STREAK_MILESTONES:
        title, desc = STREAK_MILESTONES[streak]
        st.markdown(f"""
        <div class="achievement-badge">{title}</div>
        <div style="font-size:0.8rem; color:#94a3b8; margin-bottom:8px">{desc}</div>
        """, unsafe_allow_html=True)

        # Pendo: achievement_unlocked
        if send_track_event:
            send_track_event(
                "achievement_unlocked",
                visitor_id=st.session_state.splunk_session_id or "anonymous",
                properties={
                    "streak_count": streak,
                    "achievement_title": title,
                    "achievement_description": desc,
                    "subject": st.session_state.subject,
                    "question_number": st.session_state.total,
                    "current_level": st.session_state.current_level,
                    "attention_state": st.session_state.attention_state,
                },
            )


def render_attention_history():
    """Show a mini color-strip of the last 10 attention states."""
    hist = st.session_state.attention_history[-10:]
    if not hist:
        return
    colors = [state_to_color(s) for s in hist]
    strips = "".join(
        f'<div style="flex:1;height:12px;background:{c};border-radius:3px;'
        f'margin:0 1px" title="{s}"></div>'
        for c, s in zip(colors, hist)
    )
    st.markdown(f"""
    <div style="margin-top:6px">
        <div style="font-size:11px;color:#64748b;margin-bottom:3px">Attention history</div>
        <div style="display:flex;align-items:center">{strips}</div>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────── SIDEBAR ────────────────────────────
def render_sidebar():
    prof = get_active_profile()
    with st.sidebar:
        display = prof.get("display_name", "CogPace")
        st.markdown(f"## 🧠 {display}")
        st.caption(prof.get("tagline", "Attention-aware STEM tutor"))
        st.caption(f"📋 {prof.get('competition', '')}")
        if prof.get("track"):
            st.caption(f"🏷 {prof['track']}")

        with st.expander("Switch competition profile", expanded=False):
            ids = list_profile_ids()
            labels = {load_profile(i).get("display_name", i): i for i in ids}
            choice = st.selectbox(
                "Profile",
                options=list(labels.keys()),
                index=ids.index(prof["id"]) if prof.get("id") in ids else 0,
                label_visibility="collapsed",
            )
            if st.button("Apply profile", use_container_width=True):
                st.session_state.profile_id = labels[choice]
                st.session_state.pop("_profile_cache", None)
                st.query_params["profile"] = labels[choice].replace("_", "-")
                st.rerun()

        st.divider()

        if not st.session_state.game_started or st.session_state.session_complete:
            st.markdown("### Choose a Subject")
            for key, label in SUBJECT_LABELS.items():
                color = SUBJECT_COLORS[key]
                if st.button(label, key=f"subj_{key}", use_container_width=True):
                    start_session(key)
                    st.rerun()
        else:
            subj = st.session_state.subject
            color = SUBJECT_COLORS.get(subj, "#7c3aed")
            st.markdown(
                f'<div style="font-weight:700;color:{color};font-size:1.1rem">'
                f'{SUBJECT_LABELS.get(subj, subj)}</div>',
                unsafe_allow_html=True
            )
            st.markdown("---")
            render_progress_bar()

            c1, c2 = st.columns(2)
            with c1:
                st.metric("Score", f"{st.session_state.score}/{st.session_state.total}")
            with c2:
                st.metric("Streak", f"{st.session_state.streak} 🔥")

            st.markdown(f"**Level:** {st.session_state.current_level} / 5")

            if st.session_state.attention_snap:
                snap = st.session_state.attention_snap
                st.divider()
                st.markdown("**🧲 Attention Field**")
                render_attention_gauge(snap.state, snap.f_att)
                st.caption(snap.message)
                render_attention_history()

            if profile_feature("cerome_panel") and st.session_state.session_history:
                cerome = infer_learner_cerome(st.session_state.session_history)
                st.divider()
                st.markdown("**🧬 Cerome-lite** *(Aura-inspired)*")
                st.caption(f"σ stability: **{cerome.sigma}** · {cerome.stability_label}")
                st.caption(f"Engagement: **{cerome.engagement_label}**")
                st.caption(f"Baseline S: {cerome.baseline_s}")

            st.divider()
            if st.button("🔄 Change Subject", use_container_width=True):
                st.session_state.game_started = False
                st.session_state.session_complete = False
                st.session_state.subject = None
                st.rerun()

        st.divider()
        st.markdown("### 🔑 LLM polish (optional)")
        st.caption("Off by default. MFA engine decides teaching; Gemini may only rephrase.")
        if profile_feature("llm_polish"):
            st.success("Profile enables polish")
        else:
            st.info("Profile: MFA-only (enable llm_polish in profile JSON to allow rephrase)")
        env_key = resolve_api_key()
        if env_key and not st.session_state.gemini_api_key:
            st.caption("✅ Loaded from environment")
        key_input = st.text_input(
            "API Key",
            value=st.session_state.gemini_api_key,
            type="password",
            placeholder="AIza...",
            label_visibility="collapsed",
        )
        if key_input != st.session_state.gemini_api_key:
            # Pendo: gemini_api_key_configured
            if send_track_event:
                send_track_event(
                    "gemini_api_key_configured",
                    visitor_id=st.session_state.splunk_session_id or "anonymous",
                    properties={
                        "key_provided": bool(key_input),
                        "key_removed": bool(st.session_state.gemini_api_key) and not bool(key_input),
                    },
                )
            st.session_state.gemini_api_key = key_input

        render_mfa_info_box()


# ──────────────────────────── WELCOME SCREEN ────────────────────────────
def render_welcome():
    prof = get_active_profile()
    display = prof.get("display_name", "CogPace")
    accent = prof.get("accent_color", "#7c3aed")
    subtitle = prof.get("welcome_subtitle", prof.get("tagline", ""))
    cards = prof.get("card_highlights") or [
        {"icon": "🧲", "title": "Attention-Aware", "body": "MFA engagement scoring."},
        {"icon": "🎯", "title": "Adaptive", "body": "Difficulty follows attention state."},
        {"icon": "🤖", "title": "AI Tutor", "body": "Gemini + offline fallback + chat."},
    ]

    st.markdown(f"""
    <div style="text-align:center; padding: 50px 20px 30px;">
        <div style="font-size: 64px; margin-bottom: 8px;">🧠</div>
        <h1 style="font-size: 2.8rem; margin-bottom: 6px; background: linear-gradient(90deg, {accent}, #06b6d4);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{display}</h1>
        <p style="font-size: 1.05rem; color: #94a3b8; max-width: 560px; margin: 0 auto 32px;">
            {subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    for col, card in zip([col1, col2, col3], cards[:3]):
        with col:
            st.markdown(f"""
            <div class="summary-card">
                <div style="font-size:1.8rem">{card.get('icon', '✨')}</div>
                <div style="font-weight:700; margin:6px 0; color:#c4b5fd">{card.get('title', '')}</div>
                <div style="font-size:0.88rem; color:#94a3b8">{card.get('body', '')}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div style="
        background: #1e293b; border-radius: 14px; padding: 22px 28px;
        text-align: center; border: 1px solid #334155; margin: 16px 0;
    ">
        <div style="font-size: 1.5rem; font-family: monospace; color: #a78bfa; margin-bottom: 10px;">
            F<sub>att</sub>(r) = S / r²
        </div>
        <div style="color: #64748b; font-size: 0.85rem; line-height: 1.6">
            r = psychological distance from the subject &nbsp;|&nbsp; S = field strength (motivation × streak)<br>
            <em>Magnetic Field Model of Attention — Zeng (2026)</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 👈 Pick a subject in the sidebar to start your session")

    st.divider()
    with st.expander("🎭 Judge / Demo Mode — Skip to Session Summary", expanded=False):
        st.caption(
            "For hackathon judges: instantly load a pre-built demo session to see the "
            "full attention field trajectory, analytics, and AI explanations without "
            "answering all 12 questions."
        )
        demo_subject = st.selectbox(
            "Demo subject",
            options=["physics", "math", "chemistry", "cs"],
            format_func=lambda k: SUBJECT_LABELS[k],
            key="demo_subject_picker",
        )
        if st.button("⚡ Launch Demo Session", type="primary", use_container_width=True):
            _load_demo_session(demo_subject)
            st.rerun()


def _load_demo_session(subject: str):
    """Load a pre-built demonstration session for judge review."""
    import random
    from mfa_attention import compute_attention

    # Load real questions so topic names are genuine
    all_q = load_questions()
    subject_q = all_q.get(subject, [])
    sample_q = random.sample(subject_q, min(12, len(subject_q)))

    # Pre-defined pattern: Optimal → Underloaded → Optimal → Approaching → Overloaded → recovery
    # Shows all 4 attention states for maximum demo impact
    patterns = [
        (9000,  True),   # Q1  — normal correct → OPTIMAL
        (7000,  True),   # Q2  — fast correct → OPTIMAL (streak)
        (6000,  True),   # Q3  — fast correct → OPTIMAL (streak peak)
        (2800,  False),  # Q4  — very fast wrong → UNDERLOADED (guessing, not engaged)
        (4500,  True),   # Q5  — fast correct → UNDERLOADED (too easy)
        (9500,  True),   # Q6  — normal correct → OPTIMAL (re-engagement)
        (10000, True),   # Q7  — normal correct → OPTIMAL
        (8200,  False),  # Q8  — moderate wrong → APPROACHING (load rising)
        (28000, False),  # Q9  — very slow wrong → OVERLOADED (cognitive crash)
        (26000, False),  # Q10 — slow wrong → OVERLOADED
        (11000, True),   # Q11 — normal correct → recovery → OPTIMAL
        (9000,  True),   # Q12 — normal correct → OPTIMAL
    ]

    history = []
    f_att_hist = []
    att_hist = []
    streak = 0
    score = 0
    avg_time = 10000.0

    for i, (rt, correct) in enumerate(patterns):
        if correct:
            streak += 1
            score += 1
        else:
            streak = 0
        snap = compute_attention(rt, correct, streak, avg_time, i + 1)
        avg_time = (avg_time * i + rt) / (i + 1)
        q = sample_q[i] if i < len(sample_q) else {"topic": "General", "level": 2}
        history.append({
            "correct": correct,
            "time_ms": rt,
            "level": q.get("level", 2),
            "topic": q.get("topic", "General"),
            "state": snap.state,
        })
        f_att_hist.append({"Q": i + 1, "F_att": snap.f_att, "State": snap.state})
        att_hist.append(snap.state)

    st.session_state.subject = subject
    st.session_state.level_map = {}
    st.session_state.seen_ids = set()
    st.session_state.current_level = 2
    st.session_state.session_history = history
    st.session_state.streak = streak
    st.session_state.score = score
    st.session_state.total = len(patterns)
    st.session_state.attention_state = att_hist[-1]
    st.session_state.attention_snap = None
    st.session_state.explanation = None
    st.session_state.answered = False
    st.session_state.selected_option = None
    st.session_state.game_started = True
    st.session_state.session_complete = True
    st.session_state.attention_history = att_hist
    st.session_state.f_att_history = f_att_hist

    # Pendo: demo_session_launched
    if send_track_event:
        sim_total = len(patterns)
        sim_accuracy = round(score / sim_total * 100) if sim_total else 0
        send_track_event(
            "demo_session_launched",
            properties={
                "subject": subject,
                "simulated_score": score,
                "simulated_total": sim_total,
                "simulated_accuracy_pct": sim_accuracy,
            },
        )


# ──────────────────────────── SESSION SUMMARY ────────────────────────────
def render_session_summary():
    hist = st.session_state.session_history
    score = st.session_state.score
    total = st.session_state.total
    accuracy = round(score / total * 100) if total else 0

    # Count attention states
    state_counts = {}
    for h in hist:
        state_counts[h.get("state", "?")] = state_counts.get(h.get("state", "?"), 0) + 1

    dominant_state = max(state_counts, key=state_counts.get) if state_counts else "OPTIMAL"
    avg_time_s = round(get_avg_response_time() / 1000, 1)

    # Grade
    if accuracy >= 90:
        grade, grade_color = "A+", "#22c55e"
    elif accuracy >= 75:
        grade, grade_color = "A", "#22c55e"
    elif accuracy >= 60:
        grade, grade_color = "B", "#f59e0b"
    elif accuracy >= 45:
        grade, grade_color = "C", "#f97316"
    else:
        grade, grade_color = "D", "#ef4444"

    subj_color = SUBJECT_COLORS.get(st.session_state.subject or "physics", "#7c3aed")

    # Pendo: session_completed
    if send_track_event:
        topics = list({h.get("topic", "?") for h in hist})
        max_streak = 0
        _cur = 0
        for h in hist:
            if h.get("correct"):
                _cur += 1
                max_streak = max(max_streak, _cur)
            else:
                _cur = 0
        send_track_event(
            "session_completed",
            visitor_id=st.session_state.splunk_session_id or "anonymous",
            properties={
                "subject": st.session_state.subject,
                "score": score,
                "total": total,
                "accuracy_pct": accuracy,
                "grade": grade,
                "avg_response_time_ms": round(get_avg_response_time()),
                "dominant_attention_state": dominant_state,
                "max_streak": max_streak,
                "topics_covered_count": len(topics),
                "optimal_count": state_counts.get("OPTIMAL", 0),
                "underloaded_count": state_counts.get("UNDERLOADED", 0),
                "approaching_count": state_counts.get("APPROACHING", 0),
                "overloaded_count": state_counts.get("OVERLOADED", 0),
                "session_id": st.session_state.splunk_session_id,
            },
        )

    st.markdown(f"""
    <div style="text-align:center; padding: 30px 10px 16px;">
        <div style="font-size:48px">{'🏆' if accuracy >= 75 else '📊'}</div>
        <h2 style="margin:8px 0">Session Complete!</h2>
        <p style="color:#94a3b8">Here's what your attention field looked like this session.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Score", f"{score}/{total}")
    with c2:
        st.metric("Accuracy", f"{accuracy}%")
    with c3:
        st.metric("Grade", grade)
    with c4:
        st.metric("Avg Time", f"{avg_time_s}s")

    st.divider()

    # Attention breakdown
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.markdown("#### 🧲 Attention Profile")
        state_info = {
            "OPTIMAL": ("⚡ Optimal", "#22c55e"),
            "UNDERLOADED": ("😴 Underloaded", "#f59e0b"),
            "APPROACHING": ("⚠️ Approaching", "#f97316"),
            "OVERLOADED": ("🆘 Overloaded", "#ef4444"),
        }
        for state, count in sorted(state_counts.items(), key=lambda x: -x[1]):
            label, color = state_info.get(state, (state, "#6b7280"))
            pct = int(count / len(hist) * 100) if hist else 0
            st.markdown(f"""
            <div style="margin:6px 0">
                <div style="display:flex;justify-content:space-between;font-size:0.85rem;color:#e2e8f0;margin-bottom:2px">
                    <span>{label}</span><span>{count}×  ({pct}%)</span>
                </div>
                <div style="background:#1e293b;border-radius:6px;height:8px;overflow:hidden">
                    <div style="width:{pct}%;height:100%;background:{color};border-radius:6px"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_r:
        st.markdown("#### 📚 Topics Covered")
        topics = list({h.get("topic", "?") for h in hist})
        tags_html = " ".join(f'<span class="topic-tag">{t}</span>' for t in topics)
        st.markdown(tags_html, unsafe_allow_html=True)

        st.markdown("")
        # Personalized feedback
        feedback = _generate_feedback(dominant_state, accuracy, st.session_state.streak)
        st.markdown(f"""
        <div style="
            background:#0f172a; border:1px solid #334155;
            border-radius:10px; padding:14px; margin-top:8px;
            font-size:0.88rem; color:#94a3b8; line-height:1.6;
        ">
        <strong style="color:#c4b5fd">{get_active_profile().get('persona_name', 'CogPace')} says:</strong><br>
        {feedback}
        </div>
        """, unsafe_allow_html=True)

        if profile_feature("career_insights") and st.session_state.session_history:
            cerome = infer_learner_cerome(st.session_state.session_history)
            hint = cerome_career_hint(cerome, st.session_state.subject)
            st.markdown(f"""
            <div style="
                background:#0c1929; border:1px solid #0891b2;
                border-radius:10px; padding:14px; margin-top:10px;
                font-size:0.88rem; color:#94a3b8;
            ">
            <strong style="color:#06b6d4">🛤 Career insight (Cerome-lite):</strong><br>{hint}
            </div>
            """, unsafe_allow_html=True)

    # Attention Field Trajectory Chart
    f_att_data = st.session_state.f_att_history
    if len(f_att_data) >= 2:
        st.divider()
        st.markdown("#### 📈 Attention Field Trajectory")
        st.caption("Your F_att (attention field strength) over the course of this session. The dashed lines show state boundaries.")
        try:
            import pandas as pd
            import altair as alt
            df = pd.DataFrame(f_att_data)
            # Cap F_att for display clarity (thresholds are at 2.0, 0.8, 0.25)
            Y_MAX = 5.5
            df["F_att_display"] = df["F_att"].clip(upper=Y_MAX)
            # Color by state
            state_color = {
                "OPTIMAL": "#22c55e",
                "UNDERLOADED": "#f59e0b",
                "APPROACHING": "#f97316",
                "OVERLOADED": "#ef4444",
            }
            df["Color"] = df["State"].map(state_color).fillna("#6b7280")
            chart = (
                alt.Chart(df)
                .mark_line(point=True, strokeWidth=2)
                .encode(
                    x=alt.X("Q:O", title="Question #", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("F_att_display:Q", title="F_att (capped at 5.5 for readability)",
                            scale=alt.Scale(domain=[0, Y_MAX])),
                    color=alt.Color("State:N",
                                   scale=alt.Scale(
                                       domain=list(state_color.keys()),
                                       range=list(state_color.values())
                                   ),
                                   legend=alt.Legend(title="Attention State")),
                    tooltip=["Q", "F_att_display", "State"],
                )
                .properties(height=260)
            )
            # Add threshold lines
            thresholds = pd.DataFrame([
                {"y": 2.0, "label": "Optimal threshold"},
                {"y": 0.8, "label": "Underloaded threshold"},
                {"y": 0.25, "label": "Overloaded threshold"},
            ])
            rules = (
                alt.Chart(thresholds)
                .mark_rule(strokeDash=[4, 4], color="#475569", opacity=0.6)
                .encode(y="y:Q", tooltip="label:N")
            )
            st.altair_chart((chart + rules).configure_view(
                strokeOpacity=0
            ).configure_axis(
                grid=False,
                labelColor="#94a3b8",
                titleColor="#94a3b8",
            ).configure_legend(
                labelColor="#94a3b8",
                titleColor="#94a3b8",
            ), use_container_width=True)
        except Exception:
            # Fallback: simple metric display
            st.line_chart({r["Q"]: r["F_att"] for r in f_att_data})

    if profile_feature("export_json") and export_session_summary and st.session_state.splunk_session_id:
        cerome = infer_learner_cerome(hist) if hist else None
        summary_payload = {
            "session_id": st.session_state.splunk_session_id,
            "profile": get_active_profile().get("id"),
            "subject": st.session_state.subject,
            "score": score,
            "total": total,
            "accuracy_pct": accuracy,
            "dominant_state": dominant_state,
            "state_counts": state_counts,
            "cerome": cerome.to_dict() if cerome else None,
        }
        out_path = export_session_summary(st.session_state.splunk_session_id, summary_payload)
        if out_path:
            st.caption(f"📁 DevOps export: `{out_path.name}` in session_logs/")

    st.divider()
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Try Again (Same Subject)", type="primary", use_container_width=True):
            # Pendo: session_restarted (capture before start_session resets state)
            if send_track_event:
                prev_total = st.session_state.total
                prev_score = st.session_state.score
                prev_acc = round(prev_score / prev_total * 100) if prev_total else 0
                prev_sc = {}
                for h in st.session_state.session_history:
                    prev_sc[h.get("state", "?")] = prev_sc.get(h.get("state", "?"), 0) + 1
                prev_dom = max(prev_sc, key=prev_sc.get) if prev_sc else "OPTIMAL"
                if prev_acc >= 90:
                    prev_grade = "A+"
                elif prev_acc >= 75:
                    prev_grade = "A"
                elif prev_acc >= 60:
                    prev_grade = "B"
                elif prev_acc >= 45:
                    prev_grade = "C"
                else:
                    prev_grade = "D"
                send_track_event(
                    "session_restarted",
                    visitor_id=st.session_state.splunk_session_id or "anonymous",
                    properties={
                        "subject": st.session_state.subject,
                        "previous_score": prev_score,
                        "previous_total": prev_total,
                        "previous_accuracy_pct": prev_acc,
                        "previous_grade": prev_grade,
                        "previous_dominant_state": prev_dom,
                    },
                )
            start_session(st.session_state.subject)
            st.rerun()
    with col_btn2:
        if st.button("🎯 Change Subject", use_container_width=True):
            st.session_state.game_started = False
            st.session_state.session_complete = False
            st.session_state.subject = None
            st.rerun()


def _generate_feedback(dominant_state: str, accuracy: int, max_streak: int) -> str:
    msgs = {
        "OPTIMAL": (
            f"Your attention field was consistently strong this session — "
            f"{accuracy}% accuracy with {max_streak}-question peaks. "
            f"This is the zone where real learning happens. "
            f"Try a harder subject next time to keep the field engaged."
        ),
        "UNDERLOADED": (
            f"Your response patterns suggest the difficulty was a bit below your optimal load. "
            f"You scored {accuracy}%, but your attention field shows signs of drift. "
            f"Try jumping to Level 3–5 questions right away next session."
        ),
        "APPROACHING": (
            f"Your cognitive load was near its limit for parts of this session. "
            f"A {accuracy}% score under pressure is solid. "
            f"Try shorter sessions with more breaks — your field will recover faster."
        ),
        "OVERLOADED": (
            f"The content was challenging — your attention field shows heavy load. "
            f"That's not failure; that's growth. Your {accuracy}% under strain is meaningful. "
            f"Review the explanations, then re-try. Learning happens at the edge."
        ),
    }
    return msgs.get(dominant_state, f"Good session! You scored {accuracy}%. Keep it up.")


# ──────────────────────────── QUESTION RENDER ────────────────────────────
def render_question():
    if not st.session_state.current_question:
        st.error("No questions available for this subject.")
        return

    q = st.session_state.current_question
    answered = st.session_state.answered

    render_persona_header(st.session_state.attention_state)

    # Progress + header
    render_progress_bar()

    col_score, col_streak, col_level = st.columns(3)
    with col_score:
        st.metric("Score", f"{st.session_state.score}/{st.session_state.total}")
    with col_streak:
        render_achievement(st.session_state.streak)
        st.metric("Streak", f"{st.session_state.streak} 🔥")
    with col_level:
        st.metric("Level", f"{q.get('level', '?')} / 5")

    st.markdown(f"""
    <div style="font-size:0.82rem; color:#64748b; margin:4px 0 12px;">
        <span class="topic-tag">{q.get('topic', 'General')}</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Question
    st.markdown(f"### {q['question']}")
    st.markdown("")

    options = q["options"]
    correct_idx = q["answer"]

    if not answered:
        for i, opt in enumerate(options):
            if st.button(f"  {chr(65+i)}) {opt}", key=f"opt_{i}", use_container_width=True):
                handle_answer(i, q)
                st.rerun()
    else:
        selected = st.session_state.selected_option
        for i, opt in enumerate(options):
            if i == correct_idx:
                st.success(f"✅ {chr(65+i)}) {opt}")
            elif i == selected and i != correct_idx:
                st.error(f"❌ {chr(65+i)}) {opt}")
            else:
                st.markdown(
                    f'<div style="padding:8px 12px;color:#94a3b8">'
                    f'{chr(65+i)}) {opt}</div>',
                    unsafe_allow_html=True
                )

        snap = st.session_state.attention_snap
        if snap:
            st.divider()
            render_attention_gauge(snap.state, snap.f_att)
            # MFA Math Breakdown
            with st.expander("🔬 MFA Math Breakdown (see the theory in action)", expanded=False):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("r (distance)", f"{snap.r:.3f}",
                              help="Psychological distance proxy. Low = engaged, High = lost/bored.")
                with c2:
                    st.metric("S (field strength)", f"{snap.S:.3f}",
                              help="Motivation × streak momentum. Increases with correct streaks.")
                with c3:
                    st.metric("F_att = S/r²", f"{snap.f_att:.3f}",
                              help="Attention field strength. ≥2.0 = Optimal, ≥0.8 = Underloaded, ≥0.25 = Approaching, <0.25 = Overloaded.")
                st.caption(
                    f"Confidence: {snap.confidence:.0%} (based on {st.session_state.total} data points). "
                    f"Formula: F_att(r) = S / r² — Zeng (2026)"
                )

        if st.session_state.explanation:
            src_badge = {
                "mfa_engine": "🧲 MFA engine",
                "mfa_engine+polish": "🧲 MFA + LLM polish",
                "mfa_followup": "🧲 MFA follow-up",
                "mfa_followup+polish": "🧲 MFA follow-up + polish",
            }.get(src, f"🧲 {src}")
            with st.expander(f"🧲 Tutor output ({src_badge})", expanded=True):
                st.markdown(st.session_state.explanation)

            if st.session_state.pedagogy_audit:
                with st.expander("📜 MFA decision trace (zero LLM)", expanded=False):
                    st.json(st.session_state.pedagogy_audit)

            if profile_feature("chat_followup"):
                st.markdown("**💬 Ask a follow-up**")
                for msg in st.session_state.get("chat_messages", []):
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
                if prompt := st.chat_input("Ask CogPace about this topic…"):
                    st.session_state.chat_messages.append({"role": "user", "content": prompt})
                    reply, rsrc = chat_followup(
                        user_message=prompt,
                        topic=q.get("topic", "this topic"),
                        plan=st.session_state.last_pedagogy_plan,
                        api_key=st.session_state.gemini_api_key or None,
                        profile=get_active_profile(),
                    )
                    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    st.rerun()

        with st.expander("📖 Answer Explanation"):
            st.info(q.get("explanation", "No explanation available."))

        st.divider()
        remaining = SESSION_LENGTH - st.session_state.total
        btn_label = "🏁 See Session Summary" if remaining <= 0 else f"➡️ Next Question ({remaining} left)"
        if st.button(btn_label, type="primary", use_container_width=True):
            next_question()
            st.rerun()


# ──────────────────────────── ANSWER HANDLER ────────────────────────────
def handle_answer(selected_idx: int, q: dict):
    now = time.time()
    start = st.session_state.q_start_time or now
    response_time_ms = (now - start) * 1000

    correct_idx = q["answer"]
    is_correct = (selected_idx == correct_idx)

    previous_streak = st.session_state.streak
    previous_state = st.session_state.attention_state

    st.session_state.total += 1
    if is_correct:
        st.session_state.score += 1
        st.session_state.streak += 1
    else:
        st.session_state.streak = 0

    # Pendo: streak_broken
    if send_track_event and not is_correct and previous_streak >= 1:
        send_track_event(
            "streak_broken",
            visitor_id=st.session_state.splunk_session_id or "anonymous",
            properties={
                "broken_streak_length": previous_streak,
                "subject": st.session_state.subject,
                "topic": q.get("topic", ""),
                "level": q.get("level", 2),
                "attention_state": previous_state,
                "response_time_ms": round(response_time_ms),
                "question_number": st.session_state.total,
            },
        )

    avg_time = get_avg_response_time()
    snap = compute_attention(
        response_time_ms=response_time_ms,
        is_correct=is_correct,
        streak=st.session_state.streak,
        avg_response_time_ms=avg_time,
        n_answered=st.session_state.total,
    )

    tf: TopicField | None = st.session_state.topic_field
    topic_name = q.get("topic", "General")
    if tf:
        tf.decay()
        r_eff = tf.effective_r(topic_name, snap.r)
        if abs(r_eff - snap.r) > 0.01:
            snap = snapshot_with_effective_r(snap, r_eff, st.session_state.total)
        spreading = tf.spreading_hint(topic_name, st.session_state.subject)
    else:
        spreading = None

    cerome = infer_learner_cerome(st.session_state.session_history) if profile_feature("cerome_panel") else None

    # Record history
    st.session_state.session_history.append({
        "correct": is_correct,
        "time_ms": response_time_ms,
        "level": q.get("level", 2),
        "topic": topic_name,
        "subject": st.session_state.subject,
        "state": snap.state,
    })
    st.session_state.attention_history.append(snap.state)
    st.session_state.f_att_history.append({
        "Q": st.session_state.total,
        "F_att": snap.f_att,
        "State": snap.state,
    })
    st.session_state.attention_snap = snap
    st.session_state.attention_state = snap.state
    st.session_state.answered = True
    st.session_state.selected_option = selected_idx
    st.session_state.chat_messages = []

    # Pendo: question_answered
    if send_track_event:
        send_track_event(
            "question_answered",
            visitor_id=st.session_state.splunk_session_id or "anonymous",
            properties={
                "subject": st.session_state.subject,
                "question_id": str(q.get("id", "")),
                "topic": q.get("topic", ""),
                "level": q.get("level", 2),
                "is_correct": is_correct,
                "response_time_ms": round(response_time_ms),
                "attention_state": snap.state,
                "f_att": snap.f_att,
                "r": snap.r,
                "S": snap.S,
                "streak": st.session_state.streak,
                "score": st.session_state.score,
                "total": st.session_state.total,
                "question_number": st.session_state.total,
            },
        )

    # Pendo: attention_state_changed
    if send_track_event and previous_state and previous_state != snap.state:
        send_track_event(
            "attention_state_changed",
            visitor_id=st.session_state.splunk_session_id or "anonymous",
            properties={
                "previous_state": previous_state,
                "new_state": snap.state,
                "f_att": snap.f_att,
                "r": snap.r,
                "S": snap.S,
                "question_number": st.session_state.total,
                "subject": st.session_state.subject,
                "topic": q.get("topic", ""),
                "is_correct": is_correct,
                "response_time_ms": round(response_time_ms),
            },
        )

    # AI explanation with session context
    total = st.session_state.total
    score = st.session_state.score

    from mfa_attention import compute_session_trend
    trend = compute_session_trend(st.session_state.session_history)

    session_stats = {
        "score": score,
        "total": total,
        "streak": st.session_state.streak,
        "accuracy_pct": (score / total * 100) if total else 0,
        "trend": trend,
    }

    explanation, ai_src, ped_plan, ped_audit = get_explanation(
        snap=snap,
        question=q,
        history=st.session_state.session_history[:-1],
        response_time_ms=response_time_ms,
        avg_rt=avg_time,
        is_correct=is_correct,
        subject=st.session_state.subject,
        cerome=cerome,
        spreading_topic=spreading,
        api_key=st.session_state.gemini_api_key or None,
        profile=get_active_profile(),
        session_stats=session_stats,
    )
    st.session_state.explanation = explanation
    st.session_state.ai_source = ai_src
    st.session_state.last_pedagogy_plan = ped_plan
    st.session_state.pedagogy_audit = ped_audit

    if tf:
        tf.bind(topic_name, f_att=snap.f_att, correct=is_correct, subject=st.session_state.subject)

    if profile_feature("local_event_log") and append_event and st.session_state.splunk_session_id:
        append_event(
            st.session_state.splunk_session_id,
            "attention_answer",
            {
                "question_id": str(q.get("id", "")),
                "subject": st.session_state.subject,
                "state": snap.state,
                "f_att": snap.f_att,
                "r": snap.r,
                "S": snap.S,
                "correct": is_correct,
                "response_ms": int(response_time_ms),
                "ai_source": ai_src,
                "pedagogy_tone": ped_plan.tone,
                "pedagogy_depth": ped_plan.depth,
                "profile": get_active_profile().get("id"),
            },
        )

    if send_attention_event and st.session_state.splunk_session_id and profile_feature("splunk_hec"):
        send_attention_event(
            session_id=st.session_state.splunk_session_id,
            question_id=str(q.get("id", "")),
            subject=st.session_state.subject or "unknown",
            state=snap.state,
            f_att=snap.f_att,
            r=snap.r,
            s=snap.S,
            correct=is_correct,
            response_ms=int(response_time_ms),
            extra={"topic": q.get("topic", ""), "level": q.get("level", 2)},
        )


# ──────────────────────────── MAIN ────────────────────────────
def main():
    init_state()
    # Resolve profile early (query param > env > sidebar selection)
    get_active_profile()
    if profile_feature("pendo"):
        inject_pendo()
    render_sidebar()

    if not st.session_state.game_started:
        render_welcome()
    elif st.session_state.session_complete:
        render_session_summary()
    else:
        render_question()


if __name__ == "__main__":
    main()
