"""Модель «текст → ожидаемые показы»: композит признаков Jev и простых признаков из кода.

Постов десятки, признаков ~20: регрессия (и ridge тоже) на таком корпусе подгоняется под шум
и в leave-one-out не лучше монетки. Поэтому вес признака — его корреляция с log показов
на обучающих постах (improper linear model, Dawes), а сумма один раз калибруется на показы.
"""

import math
from dataclasses import dataclass

import numpy as np

from jev_score.jev import FEATURE_NAMES
from jev_score.text import cta_questions, has_number_in_hook, is_english, word_count

CODE_FEATURES = ["log_words", "number_in_hook", "one_cta_question", "english"]
ALL_FEATURES = FEATURE_NAMES + CODE_FEATURES


@dataclass
class Fit:
    mean: np.ndarray
    std: np.ndarray
    weights: np.ndarray
    bias: float


def code_features(text: str) -> dict[str, float]:
    return {
        "log_words": math.log1p(word_count(text)),
        "number_in_hook": float(has_number_in_hook(text)),
        "one_cta_question": float(cta_questions(text) == 1),
        "english": float(is_english(text)),
    }


def vector(jev_values: dict[str, float], text: str) -> np.ndarray:
    merged = {**jev_values, **code_features(text)}
    return np.array([merged[name] for name in ALL_FEATURES], dtype=float)


def target(impressions: int | None, below_threshold: int) -> float:
    """log показов; у постов вне топ-50 точное число неизвестно — берём половину порога топа."""
    return math.log(impressions if impressions else below_threshold / 2)


def correlation(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else 0.0


def fit(x: np.ndarray, y: np.ndarray) -> Fit:
    mean, std = x.mean(axis=0), x.std(axis=0)
    std[std == 0] = 1.0
    z = (x - mean) / std
    r = np.array([correlation(z[:, j], y) for j in range(z.shape[1])])
    composite = z @ r
    slope, bias = np.polyfit(composite, y, 1) if composite.std() > 0 else (0.0, float(y.mean()))
    return Fit(mean, std, r * slope, float(bias))


def predict(model: Fit, x: np.ndarray) -> np.ndarray:
    return ((np.atleast_2d(x) - model.mean) / model.std) @ model.weights + model.bias


def contributions(model: Fit, x: np.ndarray, reference: np.ndarray) -> dict[str, float]:
    """Насколько каждый признак тянет прогноз вниз или вверх относительно эталона (в log-показах)."""
    delta = (x - reference) / model.std * model.weights
    return dict(zip(ALL_FEATURES, delta.tolist()))


def percentile(value: float, corpus: np.ndarray) -> float:
    """Доля постов корпуса слабее значения, равные считаются наполовину: 0.8 — сильнее 80 %."""
    return float((corpus < value).mean() + 0.5 * (corpus == value).mean())


def grade(pct: float) -> int:
    return min(10, max(1, math.ceil(pct * 10)))


def leave_one_out(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    keep = np.ones(len(y), dtype=bool)
    out = np.empty(len(y))
    for i in range(len(y)):
        keep[i] = False
        out[i] = predict(fit(x[keep], y[keep]), x[i])[0]
        keep[i] = True
    return out


@dataclass
class LooReport:
    total: int
    strong: int
    strong_above_median: int
    weak_below_median: int
    spearman: float


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra, rb = a.argsort().argsort(), b.argsort().argsort()
    return float(np.corrcoef(ra, rb)[0, 1])


def loo_report(y: np.ndarray, predicted: np.ndarray) -> LooReport:
    """«Сильные» — верхняя половина корпуса по факту; выше медианы — прогноз выше медианы факта."""
    median = float(np.median(y))
    strong = y > median
    above = predicted > median
    return LooReport(len(y), int(strong.sum()), int((strong & above).sum()),
                     int((~strong & ~above).sum()), spearman(y, predicted))
