from datetime import date

from jev_score.corpus import (Draft, PostStats, Share, TopRow, build, clean_share_text,
                              match_draft, parse_post_analytics, parse_top_posts, window_start)

BASE = "https://www.linkedin.com/posts/someone-59482bb4_"
ID1, ID2, ID3 = "7443280381560279040", "7429543981329379329", "7444740104776134656"
SLUG_URL = BASE + "%D0%B2%D1%87%D0%B5%D1%80%D0%B0-%D0%B7%D0%B0%D0%BF%D1%83%D1%81%D1%82%D0%B8%D0%BB-" \
    "%D0%B1%D0%BE%D1%82%D0%B0-%D0%B4%D0%BB%D1%8F-%D0%B3%D0%BE%D0%BB%D0%BE%D1%81%D0%B0-share-" + ID1 + "-WBWI"
DOC_URL = BASE + "geo-seo-carousel-ugcPost-" + ID3 + "-6Vyy"


def top_row(url: str, pid: str, day: date) -> TopRow:
    return TopRow(pid, url, day, impressions=1000)


def test_top_posts_merge_engagement_and_impression_halves():
    rows = [(BASE + "a-share-" + ID1, "3/27/2026", "122", "", BASE + "b-share-" + ID2, "2/17/2026", "7933"),
            (BASE + "b-share-" + ID2, "2/17/2026", "89", "", BASE + "a-share-" + ID1, "3/27/2026", "8004")]
    merged = parse_top_posts(rows)
    assert (merged[ID1].impressions, merged[ID1].engagements) == (8004, 122)


def test_window_start_from_discovery_sheet():
    assert window_start([("Overall Performance", "10/14/2025 - 10/13/2026")]) == date(2025, 10, 14)


def test_share_text_unwraps_quoted_paragraphs():
    assert clean_share_text('Первый абзац."\n""\n"Второй абзац') == "Первый абзац.\n\nВторой абзац"


def test_draft_matched_by_slug_words():
    right = Draft("2026-03-01-voice.md", date(2026, 3, 1), "Вчера запустил бота для голоса, и вот что вышло")
    wrong = Draft("2026-03-01-other.md", date(2026, 3, 1), "Совсем другой текст про GPU")
    assert match_draft(top_row(SLUG_URL, ID1, date(2026, 3, 2)), [wrong, right]) is right


def test_attachment_slug_matched_by_draft_name_near_date():
    draft = Draft("2026-03-30-geo-seo-skills.md", date(2026, 3, 30), "Текст про сайт")
    assert match_draft(top_row(DOC_URL, ID3, date(2026, 3, 31)), [draft]) is draft


def test_date_in_draft_name_is_not_a_topic_match():
    url = BASE + "linkedin-2026-05-26pdf-ugcPost-" + ID3 + "-OLnF"
    draft = Draft("2026-05-26-stt-benchmark.md", date(2026, 5, 26), "Про распознавание речи")
    assert match_draft(top_row(url, ID3, date(2026, 5, 26)), [draft]) is None


def test_two_equal_candidates_leave_post_without_text():
    a = Draft("2026-03-24-agents-fin-model.md", date(2026, 3, 24), "один")
    b = Draft("2026-03-24-agents-other.md", date(2026, 3, 24), "два")
    url = BASE + "agents-cheatsheet-ugcPost-" + ID3 + "-3SEk"
    assert match_draft(top_row(url, ID3, date(2026, 3, 24)), [a, b]) is None


def test_carousel_slides_are_never_used_as_post_text():
    slides = Draft("2026-03-30-geo-seo-carousel.md", date(2026, 3, 30), "Слайд 1")
    posts = build({ID3: top_row(DOC_URL, ID3, date(2026, 3, 31))}, [], [slides], {}, date(2025, 10, 1), {})
    assert posts[0].text is None


def test_post_without_text_is_marked_missing():
    posts = build({ID1: top_row(SLUG_URL, ID1, date(2026, 3, 2))}, [], [], {}, date(2025, 10, 1), {})
    assert "текст" in posts[0].missing


def test_override_none_means_no_text_even_if_slug_matches():
    draft = Draft("2026-03-01-voice.md", date(2026, 3, 1), "Вчера запустил бота для голоса")
    posts = build({ID1: top_row(SLUG_URL, ID1, date(2026, 3, 2))}, [], [draft], {}, date(2025, 10, 1),
                  {ID1: None})
    assert posts[0].text is None


def test_export_posts_outside_top_join_as_below():
    share = Share(ID2, date(2026, 1, 5), "Пост, который не залетел")
    posts = build({}, [share], [], {}, date(2025, 10, 14), {})
    assert [(p.label, p.impressions) for p in posts] == [("below", None)]


def test_export_posts_before_window_are_skipped():
    share = Share(ID2, date(2025, 1, 5), "Старый пост")
    assert build({}, [share], [], {}, date(2025, 10, 14), {}) == []


def test_per_post_analytics_fill_comments_and_saves():
    rows = [("Post URL", BASE + "x-ugcPost-" + ID1 + "-olW-"), ("Impressions", "665"),
            ("Members reached", "359"), ("Comments", "9"), ("Saves", "1")]
    assert parse_post_analytics(rows) == (ID1, PostStats(comments=9, saves=1, reach=359))
