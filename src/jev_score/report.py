"""Человеческий вывод по-русски."""

from jev_score.corpus import Post
from jev_score.edits import FEATURE_RU
from jev_score.model import LooReport
from jev_score.rules import Rule
from jev_score.score import Verdict, post_hook


def quantile_words(pct: float) -> str:
    quarter = min(4, int(pct * 4) + 1)
    return f"сильнее {pct:.0%} ваших постов — {quarter}-я четверть из 4 (4-я — лучшие)"


def hook_words(v: Verdict) -> str:
    level = round(v.hook_level)
    label = ["пустой", "слабый", "рабочий", "сильный", "очень сильный"][min(level, 4)]
    return (f"{label} ({v.hook_level:.1f} из {v.hook_levels}); сильнее, чем у "
            f"{v.hook_percentile:.0%} залетевших постов")


def metrics(post: Post) -> str:
    parts = [f"{post.impressions:,} показов".replace(",", " ") if post.impressions else "показы неизвестны"]
    if post.engagements is not None:
        parts.append(f"{post.engagements} вовлечений")
    s = post.stats
    parts.append(f"{s.comments} комм." if s.comments is not None else "комм. нет в выгрузке")
    parts.append(f"{s.saves} сохр." if s.saves is not None else "сохр. нет в выгрузке")
    if s.out_of_network_share is not None:
        parts.append(f"вне сети {s.out_of_network_share:.0%}")
    return ", ".join(parts)


def similar_block(similar: list[tuple[Post, float]]) -> list[str]:
    out = []
    for post, sim in similar:
        source = "" if post.text_source == "export" else " (текст из черновика)"
        out.append(f"  • {post.published}: «{post_hook(post)[:110]}…»{source}")
        out.append(f"    {metrics(post)}; похожесть по Jev {sim:.0%}")
    return out


def render(v: Verdict, rules: list[Rule], similar: list[tuple[Post, float]], edits: str | None,
           cost: dict[str, float | None]) -> str:
    lines = [
        f"Оценка: {v.grade}/10 — {quantile_words(v.percentile)}",
        f"Прогноз: ~{v.predicted_impressions} показов",
        f"Крючок (первые две строки): {hook_words(v)}",
        "",
        "Похож на залетевшие:",
        *(similar_block(similar) or ["  • не нашлось"]),
        "",
        "Что тянет вниз сильнее всего:",
        *([f"  • {FEATURE_RU[n]}" for n, _ in v.weak] or ["  • ничего заметного"]),
        "",
        "Правила:",
        *[f"  {'✓' if r.ok else '✗'} {r.name}: {r.detail}" for r in rules],
        "",
        "Правки:",
        edits or "  (правки не запрашивались: --no-edits)",
        "",
        "Стоимость прогона: " + cost_words(cost),
    ]
    return "\n".join(lines)


def cost_words(cost: dict[str, float | None]) -> str:
    parts = [f"Jev ${cost['jev_usd']:.5f} ({int(cost['jev_tokens'])} токенов)"]
    if cost.get("claude_usd") is not None:
        parts.append(f"Claude ≈${cost['claude_usd']:.3f} (оценка Claude Code, идёт в подписку)")
    return "; ".join(parts)


def render_loo(r: LooReport) -> str:
    weak = r.total - r.strong
    return "\n".join([
        f"Leave-one-out по {r.total} постам с текстом (каждый пост предсказан моделью, которая его не видела):",
        f"  залетевшие (верхняя половина по показам): {r.strong_above_median} из {r.strong} "
        f"поставлены выше нижней половины",
        f"  нижняя половина: {r.weak_below_median} из {weak} поставлены ниже медианы",
        f"  ранговая корреляция прогноза с фактом (Spearman): {r.spearman:.2f}",
    ])


def render_corpus(posts: list[Post]) -> str:
    lines = [f"Корпус: {len(posts)} постов, с текстом {sum(bool(p.text) for p in posts)}"]
    for p in posts:
        source = p.text_source or "ТЕКСТА НЕТ"
        missing = ", ".join(m for m in p.missing if m != "текст")
        lines.append(f"  {p.published} {p.label:5} {p.impressions or '—':>6}  {source}"
                     + (f"  [нет: {missing}]" if missing else ""))
    return "\n".join(lines)
