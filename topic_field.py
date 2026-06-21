"""
Topic field — induced magnetization / spreading activation (MFA §2.3.2).

Priming lowers effective psychological distance r for topics recently engaged.
Zero preset: magnetization M_t decays exponentially; boost from correct engagement
proportional to F_att at bind time (not char→topic tables).
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TopicField:
    """Session-scoped topic magnetization state."""

    magnetization: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    visit_count: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    subject_topics: dict[str, set[str]] = field(default_factory=dict)

    @classmethod
    def from_question_bank(cls, bank: dict[str, list[dict[str, Any]]]) -> TopicField:
        tf = cls()
        for subject, questions in bank.items():
            topics = {q.get("topic", "General") for q in questions}
            tf.subject_topics[subject] = topics
        return tf

    def decay(self, factor: float = 0.92) -> None:
        for t in list(self.magnetization.keys()):
            self.magnetization[t] *= factor
            if self.magnetization[t] < 0.01:
                del self.magnetization[t]

    def bind(
        self,
        topic: str,
        *,
        f_att: float,
        correct: bool,
        subject: str | None = None,
    ) -> None:
        """Induced magnetization after answering — stronger when F_att high and correct."""
        self.visit_count[topic] += 1
        gain = max(0.0, f_att) * (0.35 if correct else 0.12)
        self.magnetization[topic] += gain
        if subject and subject in self.subject_topics:
            for related in self.subject_topics[subject]:
                if related != topic:
                    self.magnetization[related] += gain * 0.15

    def effective_r(self, topic: str, base_r: float) -> float:
        """r_eff = r / (1 + M_topic) — primed topics feel psychologically closer."""
        m = self.magnetization.get(topic, 0.0)
        return max(0.08, base_r / (1.0 + m))

    def spreading_hint(self, topic: str, subject: str | None) -> str | None:
        """Return highest magnetized neighbor topic for cross-link hints."""
        if not subject or subject not in self.subject_topics:
            return None
        neighbors = self.subject_topics[subject] - {topic}
        if not neighbors:
            return None
        best = max(neighbors, key=lambda t: self.magnetization.get(t, 0.0))
        if self.magnetization.get(best, 0.0) < 0.2:
            return None
        return best
