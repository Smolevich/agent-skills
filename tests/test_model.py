import numpy as np

from jev_score.model import fit, grade, leave_one_out, loo_report, percentile, predict


def driven_by_first_feature(n: int = 40) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    x = rng.random((n, 5))
    y = 3 * x[:, 0] + 0.1 * rng.standard_normal(n)
    return x, y


def test_fit_ranks_posts_by_the_feature_that_drives_reach():
    x, y = driven_by_first_feature()
    model = fit(x, y)
    low, high = np.full(5, 0.5), np.full(5, 0.5)
    low[0], high[0] = 0.1, 0.9
    assert predict(model, high)[0] > predict(model, low)[0]


def test_loo_finds_strong_posts_when_signal_exists():
    x, y = driven_by_first_feature()
    report = loo_report(y, leave_one_out(x, y))
    assert report.spearman > 0.8


def test_constant_feature_does_not_break_fit():
    x, y = driven_by_first_feature()
    x[:, 1] = 1.0
    assert np.isfinite(predict(fit(x, y), x[0])[0])


def test_percentile_is_share_of_weaker_posts():
    assert percentile(5.0, np.array([1.0, 2.0, 6.0, 7.0])) == 0.5


def test_equal_values_count_as_half_not_as_stronger():
    assert percentile(3.0, np.array([3.0, 3.0, 3.0, 3.0])) == 0.5


def test_grade_stays_within_one_to_ten():
    assert (grade(0.0), grade(0.55), grade(1.0)) == (1, 6, 10)
