"""Разбор текста поста: тело из черновика, крючок, слова, CTA. Только чистые функции."""

import re

# Столько знаков LinkedIn показывает до «…ещё» в ленте на десктопе.
HOOK_CHARS = 210
MAX_WORDS = 200

POST_HEADING = re.compile(
    r"^#{2,3}\s*(пост\b|post\b|your post|текущая версия|published version)", re.IGNORECASE
)
HEADING = re.compile(r"^#{1,6}\s")
# Служебная шапка черновика: «**Статус:** Черновик».
META_LINE = re.compile(r"^\*\*[^*]{1,40}:\*\*")
FIRST_COMMENT = re.compile(r"^\*\*(первый комментарий|first comment)", re.IGNORECASE)
BRAILLE_BLANK = "⠀"


def is_hashtag_line(line: str) -> bool:
    words = line.split()
    return bool(words) and all(w.startswith("#") for w in words)


def section_after(lines: list[str], start: int) -> list[str]:
    """Строки после заголовка start до следующего заголовка второго уровня и выше."""
    out = []
    for line in lines[start + 1:]:
        if re.match(r"^#{1,2}\s", line):
            break
        out.append(line)
    return out


def clean_body(lines: list[str]) -> str:
    kept = []
    for line in lines:
        if FIRST_COMMENT.match(line):
            break
        if not line.startswith("```") and line.strip() != "---" and not META_LINE.match(line):
            kept.append(line.replace(BRAILLE_BLANK, "").rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


def extract_post(markdown: str) -> str:
    """Тело поста из черновика: секция «Пост»/«Your Post»/«Текущая версия», иначе текст до первого подзаголовка."""
    lines = markdown.splitlines()
    for i, line in enumerate(lines):
        if POST_HEADING.match(line):
            return clean_body(section_after(lines, i))
    headings = [i for i, line in enumerate(lines) if HEADING.match(line)]
    if not headings:
        return clean_body(lines)
    candidates = [lines[:headings[0]]] + [section_after(lines, i) for i in headings]
    return next((body for body in map(clean_body, candidates) if body), "")


def body_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip() and not is_hashtag_line(line)]


def word_count(text: str) -> int:
    """Как `wc -w` по телу без строки хэштегов: так Стас и считает свои 200 слов."""
    return sum(len(line.split()) for line in body_lines(text))


def hook(text: str) -> str:
    """Видимая до «…ещё» часть: первые ~210 знаков по границе слова."""
    flat = " ".join(line.strip() for line in body_lines(text))
    if len(flat) <= HOOK_CHARS:
        return flat
    return flat[:HOOK_CHARS].rsplit(" ", 1)[0]


def paragraphs(text: str) -> list[str]:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text)]
    return [b for b in blocks if b and not is_hashtag_line(b)]


def cta_questions(text: str) -> int:
    """Сколько вопросов в последнем абзаце — CTA должен быть одним вопросом."""
    blocks = paragraphs(text)
    return blocks[-1].count("?") if blocks else 0


def is_english(text: str) -> bool:
    letters = re.findall(r"[a-zA-Zа-яА-ЯёЁ]", text)
    latin = sum(ch.isascii() for ch in letters)
    return bool(letters) and latin / len(letters) > 0.6


def has_number_in_hook(text: str) -> bool:
    return bool(re.search(r"\d", hook(text)))
