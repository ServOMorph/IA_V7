from __future__ import annotations

from pathlib import Path

from scripts.benchmark_rgpd import (
    DIFFICULTY_ORDER,
    load_corpus,
    render_report,
    run_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "benchmarks" / "rgpd_corpus.json"


def test_rgpd_benchmark_corpus_is_valid_and_complete():
    corpus = load_corpus(CORPUS_PATH)
    result = run_benchmark(corpus)

    assert result.total_cases >= 25
    assert {case.difficulty for case in result.cases} == set(DIFFICULTY_ORDER)
    assert len({case.case_id for case in result.cases}) == result.total_cases
    assert result.expected_sensitive_count > result.total_cases
    assert result.required_exact_cases


def test_rgpd_benchmark_meets_non_regression_thresholds():
    result = run_benchmark(load_corpus(CORPUS_PATH))

    assert result.thresholds_met, (
        f"conformité exacte={result.exact_case_rate:.1%}, "
        f"rappel littéral={result.literal_recall:.1%}, "
        f"cas obligatoires={result.required_exact_cases_met}"
    )


def test_rgpd_benchmark_report_exposes_failures_and_recommendations():
    result = run_benchmark(load_corpus(CORPUS_PATH))
    report = render_report(result, CORPUS_PATH)

    assert "# Rapport du benchmark `/rgpd`" in report
    assert "## Détail des écarts" in report
    assert "## Résultats par catégorie" in report
    assert "## Pistes d'amélioration prioritaires" in report
    assert "données synthétiques uniquement" in report
    assert any(not case.exact for case in result.cases)
