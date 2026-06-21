# CogPace Philosophy — Not an LLM Skill Wrapper

> Cora Zeng · MFA + Aura · Zero Preset

## What CogPace is NOT

- ❌ ChatGPT with a quiz skin
- ❌ `if student == ADHD then easy question` tables
- ❌ Gemini deciding tone, depth, or difficulty

## What CogPace IS

A **computational attention tutor** where every teaching move is traceable to MFA physics:

| Mechanism | Formula / rule | Pedagogy |
|-----------|----------------|----------|
| Field strength | `F_att = S / r²` | Classify OPTIMAL → OVERLOADED |
| Induced magnetization | `r_eff = r / (1+M_topic)` | Priming from recent topics (Collins & Loftus spreading activation) |
| Lenz's law | Switch cost on subject change | Dampen S after context shift (Monsell task-switch) |
| Energy conservation | `E_used ≤ E_total - E_min` | Shrink depth when cognitive budget low (Kahneman resource) |
| Capture | Fast wrong ≈ high F_p | Warn peripheral pull (Lavie load) |
| Cerome-lite σ | RT variance EMA | Gentler difficulty swings (Castellanos & Tannock ADHD σ) |

## Zero Preset (Aura-aligned)

- **Zero content preset:** no char→answer maps, no personality quizzes
- **Structure preset OK:** MFA equations, question bank metadata, physics of fields
- **LLM role (P3 echo):** optional *polish* only — rephrase MFA-composed blocks; cannot change `tone` or `depth`

## Decision stack (v4)

```
response → mfa_attention → topic_field (r_eff)
         → mfa_pedagogy.plan (tone, depth, blocks)
         → explanation_engine.compose
         → [optional] ai_tutor polish
         → UI shows audit JSON
```

## Why this wins hackathons

Judges see **audit trail**: "Gemini didn't decide — F_att=0.31, Lenz=0.85, E_rem=1.2 → tone=ground, depth=1."

That is Cora's research story: **attention as field**, not API call.
