"""Правки формулирует Claude: Jev текст не пишет, а «где слабо» уже посчитано моделью."""

import json
import subprocess
from dataclasses import dataclass

CLAUDE_MODEL = "sonnet"
TIMEOUT_S = 180

FEATURE_RU = {
    "hook_strength": "крючок в первых двух строках",
    "concreteness": "конкретика: цифры, имена, результаты",
    "personal_open": "личное начало",
    "money_cost": "деньги и цены",
    "career": "тема карьеры",
    "ai_tools": "тема AI-инструментов",
    "own_result": "собственный результат с цифрами",
    "surprising": "неожиданный тезис",
    "failure": "признание промаха",
    "how_to": "практический способ для читателя",
    "news_retell": "пересказ новости вместо своего опыта",
    "cta_easy": "вопрос в конце, на который легко ответить",
    "corporate_tone": "корпоративный или ИИ-шный тон",
    "promo": "реклама своего продукта",
    "log_words": "длина",
    "number_in_hook": "число в крючке",
    "one_cta_question": "один вопрос в CTA",
    "english": "английский язык",
}


@dataclass
class Edits:
    text: str
    cost_usd: float | None


def prompt(draft: str, tone_guide: str, weak: list[str], failed_rules: list[str],
           similar_hook: str | None) -> str:
    lines = [
        "Ты редактор LinkedIn-постов Стаса. Ниже его tone-guide, черновик и диагностика модели,",
        "обученной на его прошлых постах. Дай 2–3 конкретные правки к черновику.",
        "Правила ответа:",
        "- текст целиком не переписывать; каждая правка — одна строка вида",
        "  «было: <цитата из черновика> → стало: <вариант> — <зачем, 3–8 слов>»;",
        "- голос и факты Стаса не трогать, новых цифр и фактов не выдумывать;",
        "- личное начало (первый абзац — опыт или мотив Стаса) не убирать: цифру для крючка",
        "  ставить после него, а не вместо; итог ≤200 слов, в конце один вопрос;",
        "- первая правка — про то, что сильнее всего тянет пост вниз;",
        "- по-русски, без вступления и без заключения, только список.",
        "",
        "## Tone-guide", tone_guide.strip(), "",
        "## Что модель считает слабым (от самого тяжёлого)", *[f"- {w}" for w in weak], "",
    ]
    if failed_rules:
        lines += ["## Нарушенные правила Стаса", *[f"- {r}" for r in failed_rules], ""]
    if similar_hook:
        lines += ["## Начало его похожего залетевшего поста (для ориентира, не копировать)", similar_hook, ""]
    lines += ["## Черновик", draft.strip()]
    return "\n".join(lines)


def parse_cli_output(raw: str) -> Edits:
    data = json.loads(raw)
    return Edits(str(data.get("result", "")).strip(), data.get("total_cost_usd"))


def ask_claude(text: str) -> Edits:
    """Граница с Claude Code: один ход без инструментов и без сохранения сессии."""
    done = subprocess.run(
        ["claude", "-p", "--model", CLAUDE_MODEL, "--output-format", "json", "--tools", "",
         "--no-session-persistence", "--strict-mcp-config"],
        input=text, capture_output=True, text=True, timeout=TIMEOUT_S, check=True,
    )
    return parse_cli_output(done.stdout)
