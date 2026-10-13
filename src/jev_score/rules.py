"""Жёсткие правила Стаса для LinkedIn: ≤200 слов, личное начало, один вопрос в CTA."""

from dataclasses import dataclass

from jev_score.text import MAX_WORDS, cta_questions, word_count

PERSONAL_THRESHOLD = 0.5


@dataclass
class Rule:
    name: str
    ok: bool
    detail: str


def check(text: str, personal_open: float) -> list[Rule]:
    words = word_count(text)
    questions = cta_questions(text)
    cta_detail = {0: "в последнем абзаце нет вопроса", 1: "один вопрос"}.get(
        questions, f"{questions} вопроса подряд — оставить один")
    return [
        Rule("≤200 слов", words <= MAX_WORDS, f"{words} слов"),
        Rule("личное начало", personal_open >= PERSONAL_THRESHOLD,
             f"Jev: {personal_open:.0%}, что первый абзац — личный опыт или мотив"),
        Rule("один вопрос в CTA", questions == 1, cta_detail),
    ]
