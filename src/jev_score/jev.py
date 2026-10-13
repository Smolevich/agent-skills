"""Jev (TypeSafe) как источник признаков поста и похожести на прошлые посты.

Jev не умеет «оценить по образцам» сам: он отвечает на узкие вопросы о тексте вероятностями.
Поэтому каждый пост превращается в вектор ответов, а сравнение с прошлыми постами делает код.
"""

import hashlib
import json
from dataclasses import dataclass

from typesafe_sdk import Noul, Score, TypeSafeClient

MODEL = "jev-latest"
PRICE_PER_MTOK_USD = 0.042
SCHEMA_VERSION = "1"

CONTEXT = (
    "State is one LinkedIn post by a Data & AI engineering manager writing for engineers and tech "
    "managers. `post` is the full text, `first_lines` is what readers see before 'see more'."
)

HOOK_LEVELS = [
    "Generic or vague opening that gives no reason to keep reading",
    "Names a topic but has no tension, no number and no personal stake",
    "Concrete subject with one hook element: a specific number, a personal stake or a surprising claim",
    "Two hook elements: a specific number or result plus a personal stake or a surprising claim",
    "Specific surprising result with numbers and the author's own stake; hard not to open",
]
CONCRETE_LEVELS = [
    "Abstract opinions only, no specifics",
    "A few specifics, mostly general talk",
    "Several concrete facts, names or numbers",
    "Dense with concrete numbers, names, prices or measured results",
]

SCORES = {
    "hook_strength": ("How strongly does `first_lines` make a tech reader want to open the full post?",
                      HOOK_LEVELS),
    "concreteness": ("How concrete and specific is `post`?", CONCRETE_LEVELS),
}
NOULS = {
    "personal_open": "Does the first paragraph of `post` describe the author's own experience, "
                     "situation or motive (what the author did, ran into or wants), rather than a "
                     "general statement or news?",
    "money_cost": "Is `post` about money, prices, costs, limits or quotas of tools or services?",
    "career": "Is `post` about the author's career, job search, hiring or interviews?",
    "ai_tools": "Is `post` mainly about AI coding agents or AI tools such as Claude Code, Codex or LLMs?",
    "own_result": "Does `post` report a concrete result the author achieved personally: numbers "
                  "from their own launch, experiment or usage?",
    "surprising": "Does `post` make a counterintuitive or surprising claim?",
    "failure": "Does the author of `post` admit a mistake, failure or problem they ran into?",
    "how_to": "Does `post` give the reader a practical method or setup they can reuse?",
    "news_retell": "Is `post` mainly retelling news or describing someone else's product rather "
                   "than the author's own experience?",
    "cta_easy": "Does `post` end with a single question that a reader can answer from their own "
                "experience in one sentence?",
    "corporate_tone": "Does `post` read like a corporate press release or generic AI-written text?",
    "promo": "Is `post` mainly an announcement or promotion of the author's own product?",
}
FEATURE_NAMES = list(SCORES) + list(NOULS)


@dataclass
class Features:
    values: dict[str, float]
    input_tokens: int


def questions() -> dict:
    qs: dict = {name: Score(instructions=[CONTEXT, q], criteria=levels)
                for name, (q, levels) in SCORES.items()}
    qs.update({name: Noul(instructions=[CONTEXT, q]) for name, q in NOULS.items()})
    return qs


def state(text: str, first_lines: str) -> dict:
    return {"post": text, "first_lines": first_lines}


def text_hash(text: str) -> str:
    """Отпечаток текста и версии вопросов: поменялось одно — признаки считаются заново."""
    blob = json.dumps({"v": SCHEMA_VERSION, "text": text}, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def to_features(response) -> Features:
    """Score нормируется в 0..1 по числу уровней, чтобы все признаки были в одной шкале."""
    values = {name: answer.score / (len(SCORES[name][1]) - 1) for name, answer in response.scores.items()}
    values.update({name: answer.noul for name, answer in response.nouls.items()})
    return Features(values, tokens(response))


def tokens(response) -> int:
    return getattr(response.usage, "input_tokens", 0) or 0


def similarity_questions(candidate_ids: list[str]) -> dict:
    instruction = ("State holds a `draft` LinkedIn post and earlier `candidates` by the same author. "
                   "Is candidates.{cid} similar to `draft` both in topic and in how it is built: "
                   "the kind of opening, personal story versus news, use of numbers?")
    return {f"sim_{cid}": Noul(instructions=instruction.format(cid=cid)) for cid in candidate_ids}


def similarity_state(draft: str, candidates: dict[str, str]) -> dict:
    return {"draft": draft, "candidates": candidates}


def to_similarity(response) -> dict[str, float]:
    return {name.removeprefix("sim_"): answer.noul for name, answer in response.nouls.items()}


def usd(input_tokens: int) -> float:
    return input_tokens / 1_000_000 * PRICE_PER_MTOK_USD


class Jev:
    """Тонкая граница с API: всё, что ходит в сеть, — здесь, остальное чистое."""

    def __init__(self, api_key: str, model: str = MODEL):
        self.client = TypeSafeClient(api_key=api_key, model=model, timeout=120.0)

    def features(self, text: str, first_lines: str) -> Features:
        return to_features(self.client.system_one(state=state(text, first_lines), questions=questions()))

    def similarity(self, draft: str, candidates: dict[str, str]) -> tuple[dict[str, float], int]:
        response = self.client.system_one(state=similarity_state(draft, candidates),
                                          questions=similarity_questions(list(candidates)))
        return to_similarity(response), tokens(response)
