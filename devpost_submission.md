# CogPace — Devpost Submission Draft
## DSH Hacks V1 · Theme: AI × STEM Education

---

## Project Name
**CogPace**

## Tagline
*The first STEM tutor that reads your attention field — not just your answers.*

---

## What it does

CogPace is an AI-powered adaptive STEM tutor that monitors a student's **cognitive attention state in real-time** and adapts both question difficulty and AI explanations accordingly.

Unlike traditional tutors that only check "right or wrong," CogPace uses the **Magnetic Field Model of Attention (MFA)** — an original theoretical framework — to estimate *how deeply a student is engaged* from their response patterns. It classifies attention into four states:

- ⚡ **OPTIMAL** — deeply engaged, time to push harder
- 😴 **UNDERLOADED** — bored, difficulty needs to rise fast
- ⚠️ **APPROACHING LIMIT** — load is building, needs clarity and anchoring
- 🆘 **OVERLOADED** — cognitive overload, needs simplification and grounding

The system then:
1. **Adjusts question difficulty** (+1 or +2 levels when bored, −1 when struggling)
2. **Generates a custom AI explanation** via Google Gemini API (or rich built-in fallback) that matches the attention state — challenge mode for OPTIMAL, emotional grounding for OVERLOADED
3. **Shows a session summary** with:
   - An **interactive F_att trajectory chart** — a time-series showing the attention field strength across all 12 questions, colored by state, with threshold lines
   - Attention profile analytics (% time in each of the 4 states)
   - Personalized CogPace feedback
   - Topic coverage visualization
4. **Reveals the MFA math** — after each answer, students can expand "🔬 MFA Math Breakdown" to see the actual computed r, S, and F_att values that drove the adaptation decision

Subjects covered: **Physics, Mathematics, Chemistry, Computer Science** — 128 questions across 4 difficulty levels, covering 52+ unique topics, with full deduplication (no question shown twice in a session).

---

## The Science Behind It

CogPace implements the **Magnetic Field Model of Attention** (Zeng, 2026), a theoretical framework that models attention as a magnetic field:

```
F_att(r) = S / r²
```

Where:
- **r** = psychological distance from the task (derived from response time relative to the student's personal baseline, combined with correctness)
- **S** = field strength (1.0 + streak-based momentum × 0.15, penalized on wrong answers)

This is not a metaphor — it's a quantitative model. The r² relationship matches the inverse-square law seen in physical fields: attention "intensity" drops sharply when psychological distance (confusion, distraction, boredom) increases.

The model was developed by Cora Zeng as a unification of five major attention theories (Spotlight, Gradient, Load, Resource, Spreading Activation) and has been submitted as a manuscript to peer review.

---

## How we built it

**Frontend:** Streamlit (Python) — chosen for rapid prototyping without JavaScript overhead

**Attention Engine:**
- `mfa_attention.py` — Pure Python implementation of the MFA formula
- Computes r from response time ratio (student's time / session average) + correctness
- Computes S from streak-based momentum
- Classifies into 4 states with confidence scoring based on data volume

**AI Explanation Layer:**
- `gemini_adapter.py` — Calls Google Gemini 2.0 Flash with a state-specific system prompt
- Falls back to 80+ curated topic-specific explanations (4 states × 4 subjects × topic hooks for 40+ topics)
- Topic "hooks" inject surprising facts about the specific subject being studied

**Question Bank:**
- `questions.json` — 100 hand-crafted IGCSE/A-Level quality questions
- 30 Physics, 30 Math, 20 Chemistry, 20 CS
- 5 difficulty levels per subject, tagged by topic
- Session-level deduplication: no question repeats in a 12-question session

**Session Analytics (v3.0):**
- **F_att Trajectory Chart** (Altair) — line chart of field strength over time, colored by state, dashed threshold lines at 2.0/0.8/0.25
- Attention profile breakdown (% time in each state, with inline bar charts)
- Personalized CogPace feedback based on dominant attention state
- Topic coverage visualization
- Grade + accuracy + avg response time calculation
- **MFA Math Breakdown** — per-question expander showing r, S, F_att values with confidence score
- **Judge Demo Mode** — one-click instant session summary with pre-built 12-question trajectory showing all 4 states

---

## Challenges we ran into

1. **Calibrating r**: The psychological distance formula needed to handle edge cases — very fast wrong answers (guessing) look like "underloaded" not "overloaded." We used speed×correctness interaction to distinguish these states.

2. **Demo mode quality**: Without a Gemini API key, we needed fallback responses that feel *genuinely helpful*, not generic. We wrote 80+ curated responses with topic-specific "hooks" that inject surprising facts, making the tutor feel alive even offline.

3. **Session balance**: Too few questions feels incomplete; too many causes fatigue. 12-question sessions with a summary screen hit the right balance for a demo.

---

## Accomplishments we're proud of

- **Original theoretical foundation**: CogPace is the only STEM tutor we know of that applies a published attention model (rather than simple performance tracking) to drive adaptation
- **Full offline capability**: Works without any API key, with responses that feel genuinely personalized
- **Session summary analytics with F_att chart**: Students can see their own attention field trajectory — the chart shows the arc of engagement, overload, and recovery in a way that no other tool visualizes
- **Transparent MFA math**: Students and judges can see the actual formula outputs (r, S, F_att) after each question — this is the model being explicit about *why* it adapted

---

## What we learned

Attention is not binary (engaged/not-engaged). The four-state model reveals nuances that a simple difficulty algorithm misses: a student who answers quickly but incorrectly is in a fundamentally different cognitive state than one who answers slowly but incorrectly, and they need different interventions.

---

## What's next

- **Time-based attention decay**: Add temporal dynamics (attention naturally drifts without reinforcement)
- **Multi-session memory**: Track topic weaknesses across sessions using a lightweight profile
- **A/B testing the MFA model**: Compare learning outcomes between MFA-adapted and non-adapted sessions
- **Voice interface**: Integrate speech recognition for hands-free studying (important for mobility/accessibility)
- **More subjects**: Biology, History, Languages

---

## Built With

- Python 3.11
- Streamlit 1.35+
- Altair 5.0+ (F_att trajectory visualization)
- Pandas 2.0+ (session data processing)
- Google Gemini API (gemini-2.0-flash)
- google-generativeai SDK
- Custom MFA attention model (original research, arXiv preprint)

---

## Try It Out

```bash
git clone [repo]
cd cogpace
pip install -r requirements.txt
streamlit run app.py
```

No API key required — CogPace works fully offline with built-in explanations.
With a Gemini API key (enter in sidebar), explanations become live and topic-specific.

---

*CogPace was built during DSH Hacks V1 by Cora Zeng.*
*The MFA theoretical framework is original research — preprint available upon request.*
