# CogPace Demo Guide — v3.0
## For DSH Hacks V1 Judges

---

## Quick Setup (2 minutes)

```bash
pip install streamlit google-generativeai altair pandas
streamlit run app.py
```

Browser opens at `http://localhost:8501`

---

## ⚡ Fastest Route: Judge Demo Mode (30 seconds)

Don't have time for a full session? Use **Demo Mode**:

1. Open the welcome screen
2. Scroll down → expand **"🎭 Judge / Demo Mode"**
3. Select a subject
4. Click **"⚡ Launch Demo Session"**

→ Instantly see the full session summary with a real F_att trajectory chart, attention profile breakdown, personalized feedback, and grade — all populated from a pre-built 12-question session that shows all 4 attention states.

---

## Full Demo Script (5 minutes)

### 1. Welcome Screen (30 seconds)
- Show the MFA formula: `F_att(r) = S / r²`
- Explain: "This is real attention science — not just tracking right/wrong"
- Point out the 3 features: Attention-Aware, Adaptive Difficulty, AI Explanations

### 2. Start a Session (60 seconds)
- Click **⚡ Physics** in the sidebar
- Answer the first 2-3 questions **correctly and quickly** → watch the attention gauge turn GREEN (OPTIMAL)
- Then answer one **slowly and incorrectly** → watch it shift to APPROACHING or OVERLOADED

### 3. Show the MFA Math (NEW in v3!)
After answering any question:
- Expand **"🔬 MFA Math Breakdown"**
- See the actual computed values: r (psychological distance), S (field strength), F_att
- This is the actual formula running in real-time
- **Say:** "These aren't magic numbers — this is F_att = S/r² computed from your response time and streak"

### 4. Show Adaptation (90 seconds)
**The key demo moment:** Answer wrong, slowly
- Attention gauge shows ⚠️ APPROACHING or 🆘 OVERLOADED
- Difficulty DROPS on the next question (lower level shown in top-right metric)
- The AI explanation shows the "grounding" response (step-by-step anchor, real-world analogy)

Answer correctly a few times
- Gauge turns GREEN again
- AI response shifts to "challenge mode" / "interesting fact" mode
- Difficulty RISES

### 5. Streak Achievement (30 seconds)
- Get 3 in a row → badge appears: "🔥 On Fire!"
- Get 5 in a row → "⚡ Charged!"
- These appear above the score metrics during the question

### 6. Session Summary + F_att Chart (60 seconds, NEW in v3!)
After 12 questions (or use Demo Mode):
- **Score, accuracy, grade, avg response time** — at a glance
- **Attention Profile breakdown** — how many questions in each state, with percentage bars
- **📈 F_att Trajectory Chart** — an Altair line chart showing the attention field strength across all 12 questions, colored by state
  - Threshold lines at 2.0 (Optimal), 0.8 (Underloaded), 0.25 (Overloaded)
  - **This is the visual proof that the model detects real attention dynamics**
- **Topics covered** — tag cloud from actual question topics
- **Personalized CogPace feedback** — different message based on dominant attention state

### 7. Gemini API (optional)
Enter API key in sidebar → explanations become live, topic-specific, and session-aware
(CogPace tells Gemini your score, streak, and trend — not just the topic)

---

## What to Highlight to Judges

### Uniqueness
> "Every other adaptive tutor tracks performance. CogPace tracks *attention state* using a published research model (MFA, arXiv 2026). The same score can hide very different cognitive states — fast+wrong (bored/guessing) is NOT the same as slow+wrong (confused/overloaded)."

### Scientific Grounding (NEW v3 talking point)
> "The MFA Math Breakdown shows you the actual numbers: r = psychological distance, S = field strength, F_att = S/r². This isn't a black box — every adaptation is mathematically justified and traceable."

### F_att Chart (NEW v3 talking point)
> "The session summary now shows the full attention field trajectory as a time-series. You can literally see the student's engagement arc — the rise, the overload, the recovery. No existing tool shows this."

### Full Offline Operation
> "Without a Gemini key, CogPace has 80+ curated responses across 40+ topics and 4 attention states. Each response is specifically written for that cognitive state."

### 100 Questions, No Repeats
> "A student can go through 3-4 full sessions before seeing the same question. The deduplication system tracks per-session, and when all questions at a level are exhausted, it resets smartly."

---

## Potential Questions

**Q: How is this different from Khan Academy?**
A: Khan Academy tracks content mastery. CogPace tracks cognitive attention state. We model *how you're thinking*, not just *what you know*. The adaptations happen in real-time within a single session.

**Q: How accurate is the attention detection?**
A: Early-session confidence is low (we show this explicitly with the confidence percentage). After 5+ answers, the model has enough calibration data. Response time relative to personal baseline is more robust than absolute thresholds.

**Q: Can you prove the MFA model works?**
A: The model makes testable predictions (OPTIMAL state → harder next question → better learning outcomes vs. fixed difficulty). A proper randomized A/B study is the next step — exactly what we'd build post-hackathon.

**Q: What's the F_att chart showing?**
A: It's plotting the actual field strength value over time — each dot is a question. The dashed lines are the state boundaries (2.0, 0.8, 0.25). When the line dips below 0.25, the student is overloaded; when it's above 2.0, they're in the optimal learning zone.

---

## File Summary

| File | Purpose |
|---|---|
| `app.py` | Main app (v3.0 — Demo Mode, F_att chart, MFA math breakdown) |
| `mfa_attention.py` | F_att = S/r² + session trend analysis |
| `gemini_adapter.py` | AI explanation engine (80+ curated responses + Gemini live) |
| `questions.json` | 113 questions across 4 subjects, 52+ topics |
| `devpost_submission.md` | Full hackathon submission |
| `STEMINATE_submission.md` | Reframed for AI×Social Good |
| `.streamlit/config.toml` | Dark theme |
| `requirements.txt` | Dependencies (streamlit, altair, pandas, google-generativeai) |

*Demo prepared by Cora Zeng for DSH Hacks V1, June 2026.*
