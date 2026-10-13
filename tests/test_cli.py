"""Сквозной прогон CLI: настоящие корпус, модель и отчёт; подменены только Jev и `claude`."""

import json
import subprocess
from types import SimpleNamespace

import pytest

from jev_score import cli, corpus, jev
from jev_score.corpus import Post


def fake_features(post_text: str) -> SimpleNamespace:
    strong = "сильный" in post_text
    level = 4.0 if strong else 0.0
    scores = {name: SimpleNamespace(score=level if name == "hook_strength" else 1.0) for name in jev.SCORES}
    nouls = {name: SimpleNamespace(noul=0.9 if strong else 0.1) for name in jev.NOULS}
    return SimpleNamespace(scores=scores, nouls=nouls, usage=SimpleNamespace(input_tokens=100))


def fake_similarity(questions: dict) -> SimpleNamespace:
    nouls = {name: SimpleNamespace(noul=0.9 if name.endswith("1") else 0.2) for name in questions}
    return SimpleNamespace(scores={}, nouls=nouls, usage=SimpleNamespace(input_tokens=50))


class FakeTypeSafe:
    calls = 0

    def __init__(self, **kwargs):
        pass

    def system_one(self, state, questions):
        FakeTypeSafe.calls += 1
        if "draft" in state:
            return fake_similarity(questions)
        return fake_features(state["post"])


def synthetic_corpus() -> list[Post]:
    posts = []
    for i in range(12):
        strong = i < 6
        text = (f"Я запустил сильный пост номер {i}, 300 показов.\n\nА вы?" if strong
                else f"Новость номер {i} про рынок.\n\nА вы? А они?")
        posts.append(Post(str(7_000_000_000_000_000_000 + i), f"https://example.com/{i}", "2026-03-01", 5000 - i * 300 if strong else 500 - i * 5,
                          10, "top", text, "export"))
    return posts


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "CORPUS", tmp_path / "corpus.json")
    monkeypatch.setattr(cli, "FEATURES", tmp_path / "features.json")
    monkeypatch.setattr(jev, "TypeSafeClient", FakeTypeSafe)
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    cli.write_json(cli.CORPUS, corpus.to_json(synthetic_corpus()))
    return tmp_path


@pytest.fixture
def claude_answers(monkeypatch):
    answer = json.dumps({"result": "1. было: «Новость» → стало: «Я запустил» — личное начало",
                         "total_cost_usd": 0.05})
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=answer))


def run(home, capsys, text: str, *flags: str) -> str:
    draft = home / "draft.md"
    draft.write_text(f"# Черновик\n\n## Пост\n\n{text}\n", encoding="utf-8")
    cli.main([str(draft), *flags])
    return capsys.readouterr().out


def test_strong_draft_scores_high(home, capsys, claude_answers):
    out = run(home, capsys, "Я запустил сильный пост номер 99, 300 показов.\n\nА вы?")
    assert int(out.split("Оценка: ")[1].split("/")[0]) >= 8


def test_weak_draft_scores_low(home, capsys, claude_answers):
    out = run(home, capsys, "Новость номер 99 про рынок.\n\nА вы? А они?")
    assert int(out.split("Оценка: ")[1].split("/")[0]) <= 3


def test_most_similar_post_shown_with_its_numbers(home, capsys, claude_answers):
    out = run(home, capsys, "Я запустил сильный пост.\n\nА вы?")
    assert "4 700 показов" in out


def test_edits_come_from_claude(home, capsys, claude_answers):
    out = run(home, capsys, "Новость про рынок.\n\nА вы?")
    assert "было: «Новость» → стало: «Я запустил»" in out


def test_no_edits_flag_skips_claude(home, capsys, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("claude не должен вызываться")
    monkeypatch.setattr(subprocess, "run", forbidden)
    out = run(home, capsys, "Новость про рынок.\n\nА вы?", "--no-edits")
    assert "--no-edits" in out


def test_claude_failure_still_prints_score(home, capsys, monkeypatch):
    def broken(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "claude")
    monkeypatch.setattr(subprocess, "run", broken)
    out = run(home, capsys, "Новость про рынок.\n\nА вы?")
    assert "Оценка:" in out and "Claude недоступен" in out


def test_corpus_features_are_cached_between_runs(home, capsys, claude_answers):
    run(home, capsys, "Новость про рынок.\n\nА вы?")
    FakeTypeSafe.calls = 0
    run(home, capsys, "Новость про рынок.\n\nА вы?")
    assert FakeTypeSafe.calls == 2  # только черновик и похожесть, корпус — из кэша


def test_missing_key_stops_with_hint(home, capsys, monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY")
    with pytest.raises(SystemExit, match="Vault"):
        run(home, capsys, "Текст?")
