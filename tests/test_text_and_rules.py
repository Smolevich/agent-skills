from jev_score.rules import check
from jev_score.text import cta_questions, extract_post, hook, word_count

DRAFT = """# LinkedIn — тема

Служебные заметки, не пост.

## Пост

Сейчас мы используем GPU в работе.

А вы используете GPU?

#GPU #AI

## Первый комментарий

Ссылка: https://example.com
"""


def test_extract_post_takes_post_section_only():
    assert extract_post(DRAFT) == "Сейчас мы используем GPU в работе.\n\nА вы используете GPU?\n\n#GPU #AI"


def test_extract_post_drops_meta_header_and_first_comment():
    draft = "# Заголовок\n\n**Статус:** Черновик\n\nТекст поста.\n\n**Первый комментарий:**\nссылка"
    assert extract_post(draft) == "Текст поста."


def test_extract_post_without_headings_is_whole_text():
    assert extract_post("Просто пост.\n\nВторой абзац.") == "Просто пост.\n\nВторой абзац."


def test_extract_post_falls_back_to_first_nonempty_section():
    draft = "# Пост: тема\n\n## v4\n\nТекст четвёртой версии.\n\n## v3\n\nСтарый текст."
    assert extract_post(draft) == "Текст четвёртой версии."


def test_word_count_ignores_hashtag_line():
    assert word_count("Раз два три — четыре.\n\n#a #b #c") == 5


def test_cta_counts_questions_in_last_paragraph():
    assert cta_questions("Текст.\n\nА вы? И если да, то зачем?\n\n#tag") == 2


def test_hook_cut_on_word_boundary():
    text = "слово " * 100
    assert hook(text).endswith("слово") and len(hook(text)) <= 210


def test_rules_fail_over_200_words():
    text = "слово " * 201 + "\n\nВопрос?"
    assert not check(text, personal_open=0.9)[0].ok


def test_rules_flag_two_questions_in_cta():
    rule = check("Начало.\n\nА вы? А они?", personal_open=0.9)[2]
    assert (rule.ok, rule.detail) == (False, "2 вопроса подряд — оставить один")


def test_rules_personal_open_follows_jev_probability():
    assert [r.ok for r in check("Текст?", personal_open=0.2)][1] is False
