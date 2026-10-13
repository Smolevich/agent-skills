import json

from jev_score.edits import parse_cli_output, prompt


def test_prompt_forbids_dropping_personal_opening():
    # Claude на реальном черновике предлагал заменить личное начало цифрой — правило Стаса это запрещает.
    text = prompt("Черновик.", "tone", ["крючок"], [], None)
    assert "личное начало" in text and "не убирать" in text


def test_prompt_lists_failed_rules():
    text = prompt("Черновик.", "tone", [], ["≤200 слов: 211 слов"], None)
    assert "≤200 слов: 211 слов" in text


def test_cli_output_gives_text_and_cost():
    edits = parse_cli_output(json.dumps({"result": " 1. правка \n", "total_cost_usd": 0.02}))
    assert (edits.text, edits.cost_usd) == ("1. правка", 0.02)
