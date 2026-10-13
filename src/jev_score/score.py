"""Оценка черновика против корпуса: прогноз, квантиль, слабые места, похожие посты. Без сети."""

from dataclasses import dataclass

import numpy as np

from jev_score import model
from jev_score.corpus import Post
from jev_score.jev import SCORES
from jev_score.text import hook

# Тема поста в модели есть, но советовать «смени тему» бессмысленно — правки только про подачу.
ACTIONABLE = {
    "hook_strength", "concreteness", "personal_open", "own_result", "surprising", "failure",
    "how_to", "news_retell", "cta_easy", "corporate_tone", "promo", "log_words",
    "number_in_hook", "one_cta_question",
}
CANDIDATES = 15
CANDIDATE_CHARS = 600


@dataclass
class Trained:
    posts: list[Post]
    x: np.ndarray
    y: np.ndarray
    fit: model.Fit

    @property
    def strong(self) -> np.ndarray:
        return self.y > np.median(self.y)


@dataclass
class Verdict:
    grade: int
    percentile: float
    predicted_impressions: int
    hook_level: float
    hook_levels: int
    hook_percentile: float
    weak: list[tuple[str, float]]


def below_threshold(posts: list[Post]) -> int:
    """Порог топ-50: минимум показов среди постов, попавших в топ."""
    return min(p.impressions for p in posts if p.label == "top" and p.impressions)


def usable(posts: list[Post], features: dict[str, dict[str, float]]) -> list[Post]:
    return [p for p in posts if p.text and p.post_id in features]


def train(posts: list[Post], features: dict[str, dict[str, float]]) -> Trained:
    """features — признаки Jev по post_id; посты без текста в обучение не идут."""
    rows = usable(posts, features)
    threshold = below_threshold(posts)
    x = np.array([model.vector(features[p.post_id], p.text) for p in rows])
    y = np.array([model.target(p.impressions if p.label == "top" else None, threshold) for p in rows])
    return Trained(rows, x, y, model.fit(x, y))


def verdict(trained: Trained, jev_values: dict[str, float], text: str) -> Verdict:
    x = model.vector(jev_values, text)
    predicted = float(model.predict(trained.fit, x)[0])
    pct = model.percentile(predicted, trained.y)
    reference = trained.x[trained.strong].mean(axis=0)
    pulls = model.contributions(trained.fit, x, reference)
    weak = sorted(((n, v) for n, v in pulls.items() if n in ACTIONABLE and v < 0), key=lambda t: t[1])
    hook_col = model.ALL_FEATURES.index("hook_strength")
    levels = len(SCORES["hook_strength"][1]) - 1
    return Verdict(
        grade=model.grade(pct),
        percentile=pct,
        predicted_impressions=round(float(np.exp(predicted))),
        hook_level=jev_values["hook_strength"] * levels,
        hook_levels=levels,
        hook_percentile=model.percentile(jev_values["hook_strength"], trained.x[trained.strong, hook_col]),
        weak=weak[:3],
    )


def candidates(trained: Trained) -> dict[str, str]:
    """Залетевшие посты (верхняя половина), с которыми Jev сравнивает черновик."""
    strong = [p for p, s in zip(trained.posts, trained.strong) if s]
    top = sorted(strong, key=lambda p: -(p.impressions or 0))[:CANDIDATES]
    return {p.post_id: p.text[:CANDIDATE_CHARS] for p in top}


def most_similar(similarity: dict[str, float], posts: list[Post], n: int = 2) -> list[tuple[Post, float]]:
    by_id = {p.post_id: p for p in posts}
    ranked = sorted(similarity.items(), key=lambda kv: -kv[1])
    return [(by_id[pid], s) for pid, s in ranked[:n] if pid in by_id]


def post_hook(post: Post) -> str:
    return hook(post.text or "")
