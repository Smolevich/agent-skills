"""CLI: `jev-score drafts/<файл>.md`, `jev-score corpus`, `jev-score loo`.

Данные (тексты постов, метрики, кэш признаков) живут вне репо — в JEV_SCORE_HOME,
по умолчанию ~/.local/share/jev-score: репозиторий публичный.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from jev_score import corpus, edits, model, report, rules, score
from jev_score.jev import Jev, text_hash, usd
from jev_score.text import extract_post, hook

HOME = Path(os.environ.get("JEV_SCORE_HOME", Path.home() / ".local/share/jev-score"))
CORPUS = HOME / "corpus.json"
FEATURES = HOME / "features.json"
MATCHES = HOME / "matches.json"


def read_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def api_key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        sys.exit("Нет TYPESAFE_API_KEY. Ключ Jev — в Vault secret/find-job/jev (поле api_key), "
                 "см. README, раздел «Ключ».")
    return key


def newest(pattern: str, root: Path) -> Path | None:
    found = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime)
    return found[-1] if found else None


def cmd_corpus(args: argparse.Namespace) -> None:
    aggregate = args.aggregate or newest("data/*/aggregate_analytics.xlsx", Path.cwd())
    shares = args.shares or newest("*LinkedInDataExport*.zip*", Path.home() / "Downloads")
    if not aggregate or not shares:
        sys.exit("Не нашёл выгрузку: укажите --aggregate и --shares")
    per_post = args.per_post or sorted(Path.cwd().glob("data/**/*post-analytics*.xlsx"))
    posts = corpus.load(aggregate, shares, args.drafts, per_post, read_json(MATCHES, {}))
    write_json(CORPUS, corpus.to_json(posts))
    print(report.render_corpus(posts))
    print(f"\nСохранено: {CORPUS}")


def load_corpus() -> list[corpus.Post]:
    if not CORPUS.exists():
        sys.exit("Корпуса нет — сначала `jev-score corpus` в каталоге с data/ и drafts/")
    return corpus.from_json(read_json(CORPUS, []))


def ensure_features(posts: list[corpus.Post], jev: Jev | None) -> tuple[dict[str, dict], int]:
    """Признаки Jev по post_id; недостающие считаются и сразу пишутся в кэш."""
    cache = read_json(FEATURES, {})
    spent = 0
    for post in posts:
        if post.text and text_hash(post.text) not in cache:
            jev = jev or Jev(api_key())
            found = jev.features(post.text, hook(post.text))
            cache[text_hash(post.text)] = found.values
            spent += found.input_tokens
            write_json(FEATURES, cache)
    by_id = {p.post_id: cache[text_hash(p.text)] for p in posts if p.text and text_hash(p.text) in cache}
    return by_id, spent


def cmd_loo(args: argparse.Namespace) -> None:
    posts = load_corpus()
    features, _ = ensure_features(posts, None)
    trained = score.train(posts, features)
    predicted = model.leave_one_out(trained.x, trained.y)
    print(report.render_loo(model.loo_report(trained.y, predicted)))


def cmd_score(args: argparse.Namespace) -> None:
    text = extract_post(args.draft.read_text(encoding="utf-8"))
    posts = load_corpus()
    jev = Jev(api_key())
    features, corpus_tokens = ensure_features(posts, jev)
    trained = score.train(posts, features)
    draft = jev.features(text, hook(text))
    similarity, sim_tokens = jev.similarity(text, score.candidates(trained))
    v = score.verdict(trained, draft.values, text)
    checked = rules.check(text, draft.values["personal_open"])
    similar = score.most_similar(similarity, trained.posts)
    fixes, claude_usd = None, None
    if not args.no_edits:
        fixes, claude_usd = suggest(text, v, checked, similar, args.tone_guide)
    jev_tokens = draft.input_tokens + sim_tokens + corpus_tokens
    cost = {"jev_tokens": jev_tokens, "jev_usd": usd(jev_tokens), "claude_usd": claude_usd}
    print(report.render(v, checked, similar, fixes, cost))


def suggest(text: str, v: score.Verdict, checked: list[rules.Rule],
            similar: list[tuple[corpus.Post, float]], tone_guide: Path) -> tuple[str | None, float | None]:
    guide = tone_guide.read_text(encoding="utf-8") if tone_guide.exists() else ""
    weak = [edits.FEATURE_RU[name] for name, _ in v.weak]
    failed = [f"{r.name}: {r.detail}" for r in checked if not r.ok]
    similar_hook = score.post_hook(similar[0][0]) if similar else None
    try:
        answer = edits.ask_claude(edits.prompt(text, guide, weak, failed, similar_hook))
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        return f"  (Claude недоступен: {error.__class__.__name__}; правки не получены)", None
    return answer.text, answer.cost_usd


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jev-score", description=__doc__)
    sub = p.add_subparsers(dest="command")
    c = sub.add_parser("corpus", help="собрать корпус из выгрузок LinkedIn и черновиков")
    c.add_argument("--aggregate", type=Path, help="aggregate_analytics.xlsx (лист TOP POSTS)")
    c.add_argument("--shares", type=Path, help="zip полной выгрузки или Shares.csv")
    c.add_argument("--drafts", type=Path, default=Path("drafts"))
    c.add_argument("--per-post", type=Path, nargs="*", help="выгрузки аналитики отдельных постов")
    c.set_defaults(run=cmd_corpus)
    loo = sub.add_parser("loo", help="leave-one-out по корпусу")
    loo.set_defaults(run=cmd_loo)
    s = sub.add_parser("score", help="оценить черновик")
    s.add_argument("draft", type=Path)
    s.add_argument("--no-edits", action="store_true", help="без правок от Claude")
    s.add_argument("--tone-guide", type=Path, default=Path("tone-guide.md"))
    s.set_defaults(run=cmd_score)
    return p


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] not in {"corpus", "loo", "score", "-h", "--help"}:
        argv = ["score", *argv]
    args = parser().parse_args(argv)
    if not getattr(args, "run", None):
        parser().print_help()
        return
    args.run(args)
