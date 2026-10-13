"""Корпус прошлых постов: метрики из выгрузок LinkedIn, тексты из Shares.csv и черновиков.

Ввод-вывод — в load_*; сопоставление и сборка — чистые функции над уже прочитанными строками.
"""

import csv
import io
import re
import urllib.parse
import warnings
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

import openpyxl

from jev_score.text import extract_post

POST_ID = re.compile(r"(\d{19})")
SLUG_TAIL = re.compile(r"-(share|ugcPost|activity)-\d{19}.*$")
DRAFT_NAME = re.compile(r"^(?:(\d{4}-\d{2}-\d{2})-)?(.+)\.md$")
# Слайды карусели — не текст поста, по ним сопоставлять нельзя.
SLIDES = re.compile(r"carousel|cheat-sheet")
MIN_SLUG_HITS = 4
DRAFT_DAYS = 10


@dataclass
class TopRow:
    post_id: str
    url: str
    published: date
    impressions: int | None = None
    engagements: int | None = None


@dataclass
class Share:
    post_id: str
    published: date
    text: str


@dataclass
class Draft:
    name: str
    written: date | None
    text: str

    @property
    def topic_words(self) -> list[str]:
        stem = DRAFT_NAME.match(self.name).group(2)
        return [w for w in stem.split("-") if len(w) >= 3]


@dataclass
class PostStats:
    comments: int | None = None
    saves: int | None = None
    reach: int | None = None
    out_of_network_share: float | None = None


@dataclass
class Post:
    post_id: str
    url: str
    published: str
    impressions: int | None
    engagements: int | None
    label: str  # top — в топ-50 по показам, below — опубликован в окне выгрузки, но в топ не попал
    text: str | None
    text_source: str | None  # export — Shares.csv, draft:<файл> — черновик, текст мог отличаться
    stats: PostStats = field(default_factory=PostStats)
    missing: list[str] = field(default_factory=list)


def post_id(url: str) -> str | None:
    found = POST_ID.search(urllib.parse.unquote(url))
    return found.group(1) if found else None


def us_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%m/%d/%Y").date()


def parse_top_posts(rows: list[tuple]) -> dict[str, TopRow]:
    """Лист TOP POSTS: слева топ по вовлечению, справа по показам; склеиваем по id поста."""
    out: dict[str, TopRow] = {}
    for row in rows:
        for url, published, value, metric in ((row[0], row[1], row[2], "engagements"),
                                              (row[4], row[5], row[6], "impressions")):
            pid = post_id(url) if isinstance(url, str) else None
            if not pid or not value or not str(value).strip().isdigit():
                continue
            item = out.setdefault(pid, TopRow(pid, url, us_date(published)))
            setattr(item, metric, int(value))
    return out


def window_start(discovery_rows: list[tuple]) -> date:
    """Начало окна выгрузки из листа DISCOVERY: «Overall Performance | 10/14/2025 - 10/13/2026»."""
    for row in discovery_rows:
        if row and row[0] == "Overall Performance":
            return us_date(str(row[1]).split("-")[0])
    raise ValueError("в листе DISCOVERY нет строки Overall Performance")


def clean_share_text(raw: str) -> str:
    """Shares.csv хранит абзацы как строки в кавычках внутри поля — снимаем эту обёртку."""
    lines = [line.strip().strip('"') for line in raw.replace('""', '"').splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def parse_shares(text: str) -> list[Share]:
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        pid = post_id(row.get("ShareLink", ""))
        body = clean_share_text(row.get("ShareCommentary", ""))
        if pid and body:
            out.append(Share(pid, datetime.fromisoformat(row["Date"]).date(), body))
    return out


def parse_post_analytics(rows: list[tuple]) -> tuple[str | None, PostStats]:
    """Выгрузка аналитики одного поста (Post analytics): id и то, чего нет в TOP POSTS."""
    values = {str(r[0]).strip(): r[1] for r in rows if r and r[0] is not None}
    num = lambda key: int(values[key]) if str(values.get(key, "")).strip().isdigit() else None
    stats = PostStats(comments=num("Comments"), saves=num("Saves"), reach=num("Members reached"))
    return post_id(str(values.get("Post URL", ""))), stats


def words(text: str) -> list[str]:
    return re.findall(r"[0-9a-zа-яё]+", text.lower())


def slug_words(url: str) -> list[str]:
    slug = urllib.parse.unquote(url).split("_", 1)[-1]
    return words(SLUG_TAIL.sub("", slug).replace("-", " "))


def slug_hits(url: str, text: str) -> int:
    """Сколько первых слов slug-а (LinkedIn строит его из начала поста) стоят в начале текста."""
    head = set(words(text)[:40])
    return sum(w in head for w in slug_words(url)[:6])


def match_draft(row: TopRow, drafts: list[Draft]) -> Draft | None:
    """Черновик к посту: по словам slug-а, а для slug-а из имени вложения — по дате и имени файла.

    Два равных кандидата — не угадываем, пост остаётся без текста.
    """
    by_text = max(drafts, key=lambda d: slug_hits(row.url, d.text), default=None)
    if by_text and slug_hits(row.url, by_text.text) >= min(MIN_SLUG_HITS, len(slug_words(row.url))):
        return by_text
    slug = "".join(slug_words(row.url))
    named = [d for d in drafts
             if d.written and abs((row.published - d.written).days) <= DRAFT_DAYS
             and any(w in slug for w in d.topic_words)]
    return named[0] if len(named) == 1 else None


def build(top: dict[str, TopRow], shares: list[Share], drafts: list[Draft],
          stats: dict[str, PostStats], since: date, overrides: dict[str, str | None]) -> list[Post]:
    """Корпус: топ-50 с текстом откуда нашёлся, плюс посты окна из Shares.csv, не попавшие в топ.

    overrides — ручное сопоставление id поста с черновиком (None — текста точно нет).
    """
    share_by_id = {s.post_id: s for s in shares}
    by_name = {d.name: d for d in drafts}
    posts = []
    for row in sorted(top.values(), key=lambda r: -(r.impressions or 0)):
        share = share_by_id.get(row.post_id)
        draft = None if share else \
            by_name.get(overrides[row.post_id] or "") if row.post_id in overrides else \
            match_draft(row, [d for d in drafts if not SLIDES.search(d.name)])
        text, source = (share.text, "export") if share else \
            (draft.text, f"draft:{draft.name}") if draft else (None, None)
        posts.append(make_post(row.post_id, row.url, row.published, row.impressions,
                               row.engagements, "top", text, source, stats))
    for share in shares:
        if share.post_id not in top and share.published >= since:
            url = f"https://www.linkedin.com/feed/update/urn:li:activity:{share.post_id}"
            posts.append(make_post(share.post_id, url, share.published, None, None, "below",
                                   share.text, "export", stats))
    return posts


def make_post(pid: str, url: str, published: date, impressions: int | None, engagements: int | None,
              label: str, text: str | None, source: str | None, stats: dict[str, PostStats]) -> Post:
    own = stats.get(pid, PostStats())
    missing = [name for name, value in (("текст", text), ("показы", impressions if label == "top" else 0),
                                        ("комментарии", own.comments), ("сохранения", own.saves),
                                        ("доля вне сети", own.out_of_network_share))
               if value is None]
    return Post(pid, url, published.isoformat(), impressions, engagements, label, text, source, own, missing)


def sheet_rows(path: Path, sheet: str | None = None) -> list[tuple]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # выгрузки LinkedIn без стилей, openpyxl об этом шумит
        book = openpyxl.load_workbook(path, read_only=True)
        return list((book[sheet] if sheet else book.active).iter_rows(values_only=True))


def load_shares(path: Path) -> list[Share]:
    if path.suffix == ".csv":
        return parse_shares(path.read_text(encoding="utf-8"))
    with zipfile.ZipFile(path) as archive:
        name = next(n for n in archive.namelist() if n.endswith("Shares.csv"))
        return parse_shares(archive.read(name).decode("utf-8"))


def load_drafts(folder: Path) -> list[Draft]:
    out = []
    for path in sorted(folder.glob("*.md")):
        found = DRAFT_NAME.match(path.name)
        if found:
            written = date.fromisoformat(found.group(1)) if found.group(1) else None
            out.append(Draft(path.name, written, extract_post(path.read_text(encoding="utf-8"))))
    return out


def load_post_stats(paths: list[Path]) -> dict[str, PostStats]:
    out = {}
    for path in paths:
        pid, stats = parse_post_analytics(sheet_rows(path))
        if pid:
            out[pid] = stats
    return out


def load(aggregate: Path, shares: Path, drafts: Path, per_post: list[Path],
         overrides: dict[str, str | None]) -> list[Post]:
    top = parse_top_posts(sheet_rows(aggregate, "TOP POSTS"))
    since = window_start(sheet_rows(aggregate, "DISCOVERY"))
    return build(top, load_shares(shares), load_drafts(drafts), load_post_stats(per_post),
                 since, overrides)


def to_json(posts: list[Post]) -> list[dict]:
    return [asdict(p) for p in posts]


def from_json(items: list[dict]) -> list[Post]:
    return [Post(**{**item, "stats": PostStats(**item["stats"])}) for item in items]
