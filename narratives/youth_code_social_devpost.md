# CogPace — Youth Code × AI (Track 03: Social Impact)

**Project:** [CogPace Learning Guard](https://devpost.com/software/cogpace)  
**Run locally:** `COGPACE_PROFILE=youth_code_social streamlit run app.py`

## Inspiration

STEM homework fails quietly. Students don't always say "I'm confused" — they speed-click, guess, or quit. Cognitive load theory (Sweller, 1988) and Lavie's load model predict overload before grades drop. CogPace detects **OVERLOADED** attention states from response patterns and switches to grounding AI explanations.

## What it does

- Free adaptive tutor: Physics, Math, Chemistry, CS (128 questions)
- MFA attention gauge: OPTIMAL → UNDERLOADED → APPROACHING → OVERLOADED
- **Cerome-lite** (Aura-inspired): σ stability emerges from session RT variance — no preset personality types
- Live Gemini tutor + offline fallback; follow-up chat after each explanation

## Why it helps people

- No account, no paywall — runs on any laptop
- Overload detection before shame spirals
- Open source (MIT)

## Built with

Python · Streamlit · Gemini · MFA attention engine · Aura Cerome-lite

## Demo

1. Open app with `?profile=youth_social`
2. Launch **Demo Mode** → see full attention trajectory
3. Show OVERLOADED recovery in session summary
