"""Smoke tests for CogPace v3 profiles + Cerome + MFA."""

from competition_profiles import list_profile_ids, load_profile
from mfa_attention import compute_attention
from aura_cerome_lite import infer_learner_cerome, adjust_difficulty_delta
from ai_tutor import get_explanation, resolve_api_key


def test_profiles():
    ids = list_profile_ids()
    assert len(ids) >= 6, ids
    for pid in ids:
        p = load_profile(pid)
        assert "display_name" in p
        assert "features" in p
    print("profiles OK:", ids)


def test_mfa_cerome():
    snap = compute_attention(8000, True, 3, 10000, 5)
    assert snap.state in ("OPTIMAL", "UNDERLOADED", "APPROACHING", "OVERLOADED")
    hist = [{"time_ms": 8000, "correct": True, "state": "OPTIMAL"}] * 5
    c = infer_learner_cerome(hist)
    assert 0 <= c.sigma <= 1
    assert adjust_difficulty_delta(2, c) in (0, 1, 2)
    print("mfa+cerome OK:", snap.state, c.engagement_label)


def test_ai_demo():
    text, src = get_explanation(
        state="OPTIMAL",
        topic="Kinematics",
        subject="physics",
        profile=load_profile("youth_code_social"),
    )
    assert src == "demo"
    assert len(text) > 20
    print("ai demo OK, len=", len(text))


if __name__ == "__main__":
    test_profiles()
    test_mfa_cerome()
    test_ai_demo()
    print("ALL SMOKE TESTS PASSED")
