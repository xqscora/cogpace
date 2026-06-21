"""Smoke tests — MFA engine path (not LLM)."""

from competition_profiles import load_profile
from mfa_attention import compute_attention, snapshot_with_effective_r
from topic_field import TopicField
from mfa_pedagogy import plan_pedagogy
from explanation_engine import build_plan_and_explanation
from ai_tutor import get_explanation, chat_followup


def test_mfa_engine_path():
    snap = compute_attention(8000, True, 3, 10000, 5)
    q = {
        "id": "t1",
        "level": 2,
        "topic": "Kinematics",
        "question": "v=?",
        "explanation": "v = d/t",
    }
    hist = [{"time_ms": 8000, "correct": True, "state": "OPTIMAL", "level": 2, "topic": "K", "subject": "physics"}]
    text, src, plan, audit = get_explanation(
        snap=snap,
        question=q,
        history=hist,
        response_time_ms=8000,
        avg_rt=9000,
        is_correct=True,
        subject="physics",
        profile=load_profile("stem_education"),
    )
    assert src == "mfa_engine"
    assert plan.tone in ("challenge", "curiosity", "scaffold", "ground")
    assert "Decision trace" in text
    assert audit["source"] == "mfa_engine"
    print("mfa_engine OK:", plan.tone, plan.depth)


def test_magnetization():
    tf = TopicField()
    tf.bind("Kinematics", f_att=2.5, correct=True, subject="physics")
    r0 = 1.2
    r_eff = tf.effective_r("Kinematics", r0)
    assert r_eff < r0
    snap = compute_attention(8000, True, 1, 10000, 3)
    snap2 = snapshot_with_effective_r(snap, r_eff, 3)
    if r_eff < snap.r - 0.01:
        assert snap2.f_att >= snap.f_att
    print("magnetization OK:", r0, "->", r_eff, "f", snap.f_att, "->", snap2.f_att)


def test_followup_no_llm():
    reply, src = chat_followup(
        user_message="why?",
        topic="Kinematics",
        plan=None,
        profile=load_profile("stem_education"),
    )
    assert src == "mfa_followup"
    assert "Why" in reply or "why" in reply.lower()
    print("followup OK")


if __name__ == "__main__":
    test_mfa_engine_path()
    test_magnetization()
    test_followup_no_llm()
    print("ALL v4 SMOKE TESTS PASSED")
