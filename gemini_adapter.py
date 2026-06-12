"""
Gemini API Adapter — CogPace v2.0
Generates attention-adapted STEM explanations using Google Gemini.

Falls back to rich curated demo responses when API key is not configured.
Demo responses are topic-aware for a more personalized experience.
"""

import os
from typing import Optional


# ── Topic-specific insights (used in demo mode for extra richness) ──
_TOPIC_HOOKS = {
    "Kinematics": "Kinematics is the study of motion *without* asking why — pure geometry of movement.",
    "Forces": "Every force has an equal and opposite reaction — the universe is obsessed with balance.",
    "Energy": "Energy can't be created or destroyed — it just changes costume.",
    "Momentum": "Momentum is inertia in motion. The universe never forgets it.",
    "Waves": "Sound, light, water, seismic — waves are how information travels through space.",
    "Electricity": "Electrons are lazy — they take the path of least resistance. Always.",
    "Electromagnetism": "Maxwell's equations unified electricity, magnetism, and light in 4 equations. Einstein called it the greatest intellectual achievement.",
    "Quantum Physics": "At quantum scales, particles are probability clouds — reality is fundamentally uncertain.",
    "Thermodynamics": "Entropy always increases. The universe trends toward disorder, always.",
    "Circular Motion": "Circular motion needs a constant inward force — without it, objects fly straight (Newton's 1st).",
    "Optics": "Light travels at c in vacuum but slows in any medium — that's why it bends at interfaces.",
    "Oscillations": "Simple harmonic motion: the restoring force is proportional to displacement. Springs, pendulums, even atoms.",
    "Special Relativity": "Time is relative. Simultaneity is relative. Only c is absolute.",
    "Nuclear Physics": "Nuclear binding energy is 10⁶× stronger than chemical bonds. That's the atomic bomb vs. TNT.",
    "Fluids": "Fluids transmit pressure equally in all directions — that's Pascal's Law.",
    "Algebra": "Algebra is the language of relationships — equations are just balanced sentences.",
    "Geometry": "Geometry is how space is organized. Euclid proved 5 axioms explain all of flat space.",
    "Calculus": "Calculus is the mathematics of change. Differentiation asks 'how fast?' Integration asks 'how much?'",
    "Trigonometry": "Trigonometry maps the relationship between angles and distances — from triangles to waves.",
    "Probability": "Probability quantifies uncertainty. Without it, statistics, quantum mechanics, and AI don't exist.",
    "Statistics": "Statistics is how we make sense of data. The central limit theorem makes it all possible.",
    "Linear Algebra": "Linear algebra is the mathematics of dimensions. Neural networks run on it.",
    "Sequences": "Sequences encode patterns. Fibonacci appears in nature; arithmetic/geometric sequences appear everywhere else.",
    "Combinatorics": "Combinatorics counts arrangements. It's the foundation of probability, cryptography, and algorithms.",
    "Complex Numbers": "Complex numbers extend the real line into 2D — they make rotations and wave equations elegant.",
    "Arithmetic": "Arithmetic is the foundation of all mathematics. Numbers are humanity's oldest abstraction.",
    "Atomic Structure": "Atoms are 99.999% empty space. The electrons are a cloud of probability, not tiny balls.",
    "Chemical Bonding": "Atoms bond to reach stable electron configurations — especially the noble gas configuration.",
    "Stoichiometry": "Stoichiometry is just chemistry accounting — atoms don't appear or disappear.",
    "Acids and Bases": "pH is logarithmic. pH 4 is 10× more acidic than pH 5, not just a little more.",
    "Kinetics": "Reaction rate depends on collision frequency and energy — temperature dramatically speeds this up.",
    "Chemical Equilibrium": "Le Chatelier's principle: disturb a system, it shifts to restore balance. Like elastic revenge.",
    "Organic Chemistry": "Organic chemistry is carbon's dominance: carbon bonds to 4 things, chains infinitely, forms life.",
    "Thermochemistry": "Enthalpy and entropy battle for control of reactions — Gibbs free energy is the scoreboard.",
    "Redox Reactions": "Oxidation and reduction always happen together — LEO GER (Lose Electrons Oxidized, Gain Electrons Reduced).",
    "Electrochemistry": "Galvanic cells convert chemical energy to electricity. Your phone battery is this.",
    "Gas Laws": "Gas molecules obey statistics — Boyle, Charles, Gay-Lussac describe their average behaviors.",
    "States of Matter": "Matter's state depends on how molecules balance kinetic energy against intermolecular forces.",
    "Solutions": "When a solute dissolves, it's surrounded by solvent molecules — like disappearing into a crowd.",
    "Nuclear Chemistry": "Radioactive decay is quantum mechanical — each nucleus has a probability of decaying per unit time.",
    "Quantum Chemistry": "Quantum chemistry replaces orbits with orbitals — probability clouds shaped by wave functions.",
    "Hardware": "CPUs execute billions of simple operations per second. Complexity emerges from speed + repetition.",
    "Programming": "Programs are precise instructions. Computers follow them exactly — bugs are always human error.",
    "Algorithms": "An algorithm is a repeatable process. Efficiency matters when inputs scale to millions.",
    "Data Structures": "Data structures organize information for efficient access. Choose the right one for the operation.",
    "OOP": "OOP models real-world entities as objects. Encapsulation, inheritance, and polymorphism are its pillars.",
    "Databases": "Databases persist information beyond program execution. SQL is the universal query language.",
    "Networking": "The internet is billions of devices communicating via agreed-upon protocols (TCP/IP).",
    "Theory of Computation": "Turing proved some problems are fundamentally unsolvable — the halting problem, for instance.",
    "Machine Learning": "ML is pattern recognition at scale. The algorithm finds structure; humans interpret meaning.",
    "Distributed Systems": "Distributed systems trade simplicity for scale. The CAP theorem defines their fundamental limits.",
    "Number Systems": "Binary is base-2 — the language of electronics where 0=off, 1=on.",
}

# ── Subject-level demo responses (fallback when topic not found) ──
_DEMO_RESPONSES = {
    "OPTIMAL": {
        "physics": (
            "🌟 **Challenge mode!**\n\n"
            "Since you're in the zone: **Why does the inverse-square law appear in gravity, light intensity, "
            "and electric fields?** It emerges from 3D geometry — a field radiating from a point spreads "
            "over a spherical surface of area 4πr², so intensity ∝ 1/r².\n\n"
            "**Push further:** Can you think of a field that *doesn't* follow the inverse-square law, and why?"
        ),
        "math": (
            "🌟 **Let's go deeper!**\n\n"
            "The Fundamental Theorem of Calculus says differentiation and integration are inverses — "
            "but *why*? Integration accumulates area, differentiation asks 'how fast is the area growing?' "
            "They undo each other by definition.\n\n"
            "**Challenge:** Can you derive the area of a circle using a definite integral?"
        ),
        "chemistry": (
            "🌟 **Go further!**\n\n"
            "Le Chatelier's Principle in action: why does increasing pressure favor the side with *fewer* "
            "moles of gas? The system minimizes Gibbs free energy. Pressure increases chemical potential "
            "of gases — the system shifts to reduce it.\n\n"
            "**Think:** How does a catalyst change kinetics without shifting equilibrium position?"
        ),
        "cs": (
            "🌟 **Advanced challenge!**\n\n"
            "**P vs NP**: verification is easy, but can we always find solutions quickly? "
            "RSA encryption works because factoring large numbers is (probably) in NP but not P. "
            "If P=NP, most encryption collapses overnight.\n\n"
            "**Challenge:** Is the Traveling Salesman Problem NP-complete? What does that mean practically?"
        ),
    },
    "UNDERLOADED": {
        "physics": (
            "😮 **Wait, did you know...**\n\n"
            "A feather and a hammer fall at the same rate in a vacuum. On the Moon, Apollo 15 astronaut "
            "David Scott demonstrated this live in 1971. Meanwhile, GPS satellites must correct for "
            "**gravitational time dilation** — Einstein's prediction that time runs slower near mass. "
            "Without this correction, GPS would drift by kilometers per day."
        ),
        "math": (
            "😮 **Here's something wild...**\n\n"
            "Georg Cantor proved there are infinitely many sizes of infinity. The real numbers form a "
            "'larger' infinity than the integers — you can't even list them, in principle. "
            "This broke 19th-century mathematics and nearly drove Cantor mad."
        ),
        "chemistry": (
            "😮 **Chemistry gets weird...**\n\n"
            "August Kekulé discovered benzene's ring structure from a dream of a snake eating its tail. "
            "The real reason for its stability — resonance delocalization of π electrons — "
            "wasn't understood until quantum mechanics arrived 70 years later."
        ),
        "cs": (
            "😮 **The bug that changed computing...**\n\n"
            "The first actual computer 'bug' was a real moth taped into the Harvard Mark II logbook in 1947 "
            "by Grace Hopper's team. Modern computers are fundamentally the same machine as Turing's 1936 "
            "theoretical model — just billions of times faster."
        ),
    },
    "APPROACHING": {
        "physics": (
            "⚠️ **Let's clarify this together.**\n\n"
            "**Anchor:** Forces cause *changes* in velocity, not velocity itself. "
            "A car cruising at 100 km/h has near-zero net force — you only feel force when it accelerates.\n\n"
            "**Key formula:** F = ma. Know two, find the third.\n\n"
            "**Takeaway:** Draw a free body diagram. Label every force. Sum them."
        ),
        "math": (
            "⚠️ **Let's simplify.**\n\n"
            "Every equation is just asking you to *isolate something*. "
            "Before computing, ask: 'What do I want to find?'\n\n"
            "**Example:** 3x + 6 = 21 → subtract 6 → divide by 3 → x = 5.\n\n"
            "**Takeaway:** Identify the unknown first. Then work backward."
        ),
        "chemistry": (
            "⚠️ **Back to basics.**\n\n"
            "**Anchor:** Reactions are atoms rearranging. Mass is conserved. Charge is conserved.\n\n"
            "**Real world:** Burning wood = carbon + oxygen → CO₂ + H₂O. Same atoms, new arrangement.\n\n"
            "**Takeaway:** Balance by counting atoms on each side. Nothing is created or destroyed."
        ),
        "cs": (
            "⚠️ **Let's ground this.**\n\n"
            "**Anchor:** A computer does three things: store data, read data, execute instructions.\n\n"
            "**Real world:** A for-loop = 'do this thing repeatedly, count how many times, stop.'\n\n"
            "**Takeaway:** When stuck, trace your code manually with a small example."
        ),
    },
    "OVERLOADED": {
        "physics": (
            "🆘 **Simplest version — no jargon.**\n\n"
            "**One idea:** Things fall because Earth pulls them. Stronger gravity → faster fall.\n\n"
            "**Real world:** Drop your phone — that's gravity. On the Moon, it falls slower.\n\n"
            "---\n🧘 **Reset:** Take a breath. Close your eyes. Picture something falling. "
            "That's physics. You already understand it. We're just adding math."
        ),
        "math": (
            "🆘 **Simplest version.**\n\n"
            "**One idea:** Math is patterns. Numbers follow rules that never change.\n\n"
            "**Real world:** Apples cost $2. You have $10. You can buy 5. That's division.\n\n"
            "---\n🧘 **Reset:** Find one number you recognize in the problem. Start there."
        ),
        "chemistry": (
            "🆘 **Core idea only.**\n\n"
            "**One idea:** Atoms combine to form molecules. Different atoms → different substances.\n\n"
            "**Real world:** H₂O = 2 hydrogen + 1 oxygen. Change atoms → different substance.\n\n"
            "---\n🧘 **Reset:** Think LEGO blocks. Chemistry is learning which blocks stick together."
        ),
        "cs": (
            "🆘 **Back to zero.**\n\n"
            "**One idea:** Programs are instructions the computer follows one at a time.\n\n"
            "**Real world:** A recipe. Step 1: get flour. Step 2: add water. That's a program.\n\n"
            "---\n🧘 **Reset:** Think of the last app you used. Every button was coded. You're learning that."
        ),
    },
}


def get_explanation(
    state: str,
    topic: str,
    subject: str,
    wrong_answer_text: Optional[str] = None,
    api_key: Optional[str] = None,
    session_stats: Optional[dict] = None,
) -> str:
    """
    Generate an attention-adapted explanation.

    If a valid Gemini API key is provided, uses Gemini 2.0 Flash.
    Otherwise falls back to rich curated demo responses with topic hooks.

    session_stats (optional): dict with keys score, total, streak, accuracy_pct, trend
    """
    if api_key:
        try:
            return _call_gemini(state, topic, subject, wrong_answer_text, api_key, session_stats)
        except Exception:
            pass

    return _get_demo_response(state, subject, topic, session_stats)


def _call_gemini(
    state: str,
    topic: str,
    subject: str,
    wrong_answer_text: Optional[str],
    api_key: str,
    session_stats: Optional[dict] = None,
) -> str:
    """Call Gemini 2.0 Flash with attention-adapted prompting."""
    import google.generativeai as genai
    from mfa_attention import state_to_gemini_instruction

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    instruction = state_to_gemini_instruction(state, topic, wrong_answer_text, session_stats)

    system_prompt = (
        "You are CogPace AI, an intelligent STEM tutor built on the Magnetic Field Model of Attention (MFA). "
        "MFA measures a student's cognitive engagement as a field strength: F_att(r) = S / r², "
        "where r is psychological distance from the topic and S is motivation-weighted field strength. "
        "Your job is to give SHORT, powerful responses (max 120 words) that EXACTLY match the student's "
        "current attention state. Be direct, insightful, and feel like a mentor — not a textbook. "
        "If session context is provided, reference it naturally (e.g., 'You've been doing well so far...')."
    )

    full_prompt = f"{system_prompt}\n\n{instruction}"
    response = model.generate_content(full_prompt)
    return response.text


def _get_demo_response(state: str, subject: str, topic: str = "", session_stats: Optional[dict] = None) -> str:
    """Return a curated demo response, enriched with topic-specific insight when available."""
    subject_key = subject.lower() if subject.lower() in _DEMO_RESPONSES.get(state, {}) else "physics"
    state_responses = _DEMO_RESPONSES.get(state, _DEMO_RESPONSES["APPROACHING"])
    base_response = state_responses.get(subject_key, state_responses.get("physics", "Keep going!"))

    # Inject topic hook for OPTIMAL and UNDERLOADED states (when student has capacity to absorb more)
    topic_hook = _TOPIC_HOOKS.get(topic, "")
    if topic_hook and state in ("OPTIMAL", "UNDERLOADED"):
        hook_section = (
            f"\n\n---\n"
            f"**🎯 About {topic}:** {topic_hook}"
        )
        return base_response + hook_section

    # Add session-aware suffix for personalized feel
    if session_stats and session_stats.get("total", 0) >= 3:
        trend = session_stats.get("trend", "stable")
        acc = session_stats.get("accuracy_pct", 0)
        streak = session_stats.get("streak", 0)
        if trend == "improving" and state == "OPTIMAL":
            return base_response + f"\n\n*CogPace sees you — {acc:.0f}% accuracy and a {streak}-streak. The field is strong.*"
        elif trend == "declining" and state == "OVERLOADED":
            return base_response + f"\n\n*You've answered {session_stats.get('total', 0)} questions. It's okay to struggle — that's where growth happens.*"

    return base_response
