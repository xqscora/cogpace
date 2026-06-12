# CogPace — Project Description
**DSH Hacks V1 | AI × STEM Education | June 2026**  
**Author:** Cora Zeng | Age 15 | BIBS Beijing International School

---

## The Problem

Current STEM tutors ask one question: *Did you get the answer right?*

But learning breaks down not just when students get things wrong — it breaks when they are **bored** (underloaded) or **overwhelmed** (overloaded). Cognitive load theory (Sweller, 1988) and attention research show that optimal learning happens in a narrow window between these extremes.

No existing tool detects and adapts to this in real-time.

---

## The Solution: CogPace

**CogPace** is an attention-aware AI STEM tutor that uses the **Magnetic Field Model of Attention (MFA)** to measure cognitive engagement every time a student answers a question — then adapts both difficulty and AI explanations to match.

### Core Formula
```
F_att(r) = S / r²
```
- **r** = psychological distance from the topic (derived from response time + accuracy)
- **S** = field strength (engagement, built from answer streak)
- **F_att** = attention field intensity → maps to: OPTIMAL / UNDERLOADED / APPROACHING / OVERLOADED

### The Adaptive Loop
1. Student answers a STEM question (Physics, Math, Chemistry, or CS)
2. CogPace computes their attention state using MFA formula
3. Google Gemini 2.0 Flash generates an explanation matched to that state:
   - **OPTIMAL** → challenging extension, "what if?" question
   - **UNDERLOADED** → surprising fact to re-ignite curiosity
   - **APPROACHING** → clear analogy + step-by-step anchor
   - **OVERLOADED** → one core idea + mental reset prompt
4. Difficulty automatically adjusts for the next question

---

## Why This Is Unique

> *This is the first STEM tutor grounded in a published attention theory — not just "we added AI."*

The MFA framework was developed by Cora Zeng (2026) as part of ongoing cognitive science research. CogPace is its first applied implementation, translating theoretical predictions into a real adaptive learning system.

---

## Technical Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit (Python) |
| AI | Google Gemini 2.0 Flash API |
| Attention Model | Custom MFA Python module |
| Content | **128 curated STEM questions** (Physics 33, Math 35, Chemistry 35, CS 25; 4 difficulty levels, 52+ topics) |
| Analytics | Session summary with attention profile, topic coverage, grade, personalized AI feedback |
| Offline Mode | 80+ topic-specific curated responses — no API key needed |

---

## Features (v3.0)

- ⚡ **Real-time attention monitoring** using MFA (F_att = S/r²) after every answer
- 🎯 **Adaptive difficulty** — 5 levels, adjusts based on attention state not just correctness
- 🤖 **Session-aware AI** — explanations reference your streak, accuracy trend, and specific topic
- 🏆 **Achievement badges** — streak milestones (3, 5, 7, 10, 15)
- 📈 **F_att Trajectory Chart** — Altair line chart showing attention field strength over the session with state threshold lines
- 🔬 **MFA Math Breakdown** — expandable per-question view of actual r, S, F_att values
- 🎭 **Judge Demo Mode** — one-click instant session summary showing all 4 attention states
- 📊 **Session analytics** — attention profile, grade, topic coverage, personalized feedback
- 🔄 **Question deduplication** — no repeats within a 12-question session
- 📴 **Full offline capability** — works without API key, 80+ curated topic-specific responses

## Impact

- **Applies published cognitive science** to everyday student learning
- **Accessible:** Free, runs in browser, no signup required
- **Global:** Works for any student learning STEM in any country
- **Extensible:** Framework can integrate with LMS, spaced repetition, or parent dashboards

---

## Reference

Zeng, C. (2026). *Attention as a Magnetic Field: A Unifying Framework for Attentional Gradient, Load, and Incidental Processing.* Preprint available on arXiv.
