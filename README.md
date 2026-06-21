# CogPace 馃 鈥?Adaptive STEM Tutor Powered by Attention Science

> **Built for DSH Hacks V1 + STEMINATE HACKS 2026 + ML Empowerment Build Challenge**

CogPace is the first adaptive STEM tutor built on a **peer-reviewed attention science framework**: the Magnetic Field Model of Attention (MFA). Rather than adapting only on right/wrong signals, CogPace continuously estimates a student's cognitive state and dynamically adjusts difficulty and AI explanation style in real time.

---

## v3.0 — Multi-hackathon profiles (2026-06-21)

One runnable app, **per-competition narrative**. See [`RUN_PROFILES.md`](RUN_PROFILES.md).

```powershell
pip install -r requirements.txt
.\run_cogpace.ps1 -Profile youth_code_social
# or: streamlit run app.py  with  ?profile=youth_social
```

| Profile | Angle |
|---------|--------|
| `youth_code_social` | Track 03 social impact + overload detection |
| `youth_code_education` | Track 04 career coach + Cerome hints |
| `gitlab_devops` | JSON telemetry export |
| `splunk_observability` | HEC streaming |
| `mind_the_product` | Pendo analytics |

**New:** Aura **Cerome-lite** (σ from RT variance), **Gemini follow-up chat**, `.env` API key, `test_smoke.py`.

---

CogPace is grounded in an original mathematical model: **F_att(r) = S / r虏**

| Symbol | Meaning |
|--------|---------|
| `F_att` | Attention field strength 鈥?measures cognitive engagement |
| `S` | Motivational field strength 鈥?streak momentum 脳 base motivation |
| `r` | Psychological distance 鈥?estimated from response time + error patterns |

**4 Attention States** (classified from F_att value):
- 鈿?**OPTIMAL** (F_att 鈮?2.0) 鈥?Deep flow state, increase difficulty
- 馃槾 **UNDERLOADED** (F_att 鈮?0.8) 鈥?Too easy, student may disengage soon
- 鈿狅笍 **APPROACHING** (F_att 鈮?0.25) 鈥?Cognitive load rising, simplify approach
- 馃啒 **OVERLOADED** (F_att < 0.25) 鈥?Attention collapse, provide grounding explanation

The MFA framework synthesizes five major attention theories (Spotlight, Load, Resource, Spreading Activation, and Gradient models) into a single unified mathematical model. The F_att formula derives from 3D field geometry, making it physically motivated 鈥?not just a metaphor.

*Reference: Zeng, Z. (2026). Attention as a Magnetic Field: A Unifying Framework for Attentional Gradient, Load, and Incidental Processing.*

---

## Features

### Core Adaptive Engine
- **Real-time F_att calculation** from every student response
- **4-tier difficulty adaptation** based on current attention state
- **Psychological distance (r)** computed from response time ratios
- **Streak-based field strength (S)** with momentum modeling

### Visual Transparency
- **馃敩 MFA Math Breakdown** 鈥?expandable panel showing r, S, F_att after each answer
- **馃搱 F_att Trajectory Chart** 鈥?Altair line chart of attention field evolution over the session
- **馃幆 Live Attention Gauge** 鈥?color-coded state display after each question

### AI-Powered Explanations
- **Google Gemini Integration** 鈥?state-aware explanations generated for each question
- **Explanation style adapts to cognitive state**: extension challenge (Optimal), curiosity hook (Underloaded), step-by-step (Approaching), warm simplicity (Overloaded)
- **Works offline** without API key (reduced mode)

### Session Analytics
- Attention profile breakdown (% time in each state)
- Accuracy grade (A+ to D)
- Topic coverage visualization
- Personalized session feedback message

### Demo Mode
- **馃幁 Judge / Demo Mode** 鈥?one-click demo of all four attention states, no live interaction needed

---

## Question Bank

| Subject | Questions | Topics |
|---------|-----------|--------|
| 鈿?Physics | 33 | Kinematics, Forces, Energy, Waves, Optics, Fluids, Circular Motion, Momentum |
| 鈭?Mathematics | 35 | Algebra, Calculus, Probability, Statistics, Sequences, Trigonometry, Combinatorics |
| 馃И Chemistry | 35 | Atomic Structure, Bonding, Stoichiometry, Acids/Bases, Kinetics, Gas Laws, Equilibrium, Organic, Electrochemistry |
| 馃捇 Computer Science | 25 | Algorithms, Data Structures, OOP, Networks, Machine Learning, Theory of Computation |

**Total: 128 questions across 4 difficulty levels (1鈥?)**

---

## Setup

```bash
# Clone / download
git clone https://github.com/xqscora/cogpace.git
cd cogpace

# Install dependencies
pip install streamlit google-generativeai altair pandas

# Run
streamlit run app.py
```

### Optional: Add Gemini API Key

1. Get a free API key from [Google AI Studio](https://aistudio.google.com/)
2. Enter it in the sidebar after launching (no `.env` file needed)

Without an API key, CogPace uses pre-generated fallback explanations.

---

## Architecture

```
app.py              鈥?Main Streamlit app (UI, session management, rendering)
mfa_attention.py    鈥?MFA engine (F_att calculation, state classification)
gemini_adapter.py   鈥?Gemini API wrapper (state-aware prompt generation)
questions.json      鈥?Question bank (4 subjects, 4 difficulty tiers)
requirements.txt    鈥?Python dependencies
```

---

## Social Impact

**Problem:** Quality STEM tutoring costs $30鈥?150/hour 鈥?inaccessible to most students globally.

**CogPace is free, open source, and requires no account.**

- Runs on any laptop with Python installed
- Deployable offline in schools with limited internet
- Adapts to each student's actual cognitive state 鈥?not their grade level or income bracket
- Scientific foundation: not just AI hype, but testable attention science

**Target users:**
- High school students preparing for AMC, USABO, SAT, Olympiads
- Teachers in under-resourced schools looking for adaptive tools
- NGOs delivering STEM education in developing regions
- Any self-directed learner who has struggled to stay focused while studying

---

## Author

**Zihan (Cora) Zeng** 鈥?Age 15, G9, Beijing  
Published researcher: *first paper accepted at Frontiers in Psychology (2026)*  
Author of the Magnetic Field Model of Attention

---

## License

MIT License 鈥?free to use, modify, and distribute with attribution.

---

## Screenshots

*(Add screenshots here before submitting to Devpost)*

1. Welcome screen with MFA formula display
2. Live session with attention gauge + MFA math breakdown
3. Session summary with F_att trajectory chart
4. AI explanation panel
