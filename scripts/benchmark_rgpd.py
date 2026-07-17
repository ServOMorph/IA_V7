from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ia_v7.services.commands import SENSITIVE_PLACEHOLDER, anonymize_text


DIFFICULTY_ORDER = ("facile", "moyen", "difficile", "très difficile", "adversarial")
DEFAULT_CORPUS = ROOT / "benchmarks" / "rgpd_corpus.json"
DEFAULT_REPORT = ROOT / "benchmarks" / "rapport_rgpd.md"


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    title: str
    difficulty: str
    exact: bool
    expected_count: int
    actual_count: int
    literal_redacted_count: int
    categories: tuple[str, ...]
    literal_redacted_categories: tuple[str, ...]
    expected_output: str
    actual_output: str
    recommendation: str

    @property
    def issue(self) -> str:
        if self.exact:
            return "conforme"
        if self.expected_count == 0 and self.actual_count:
            return "faux positif"
        if self.literal_redacted_count < self.expected_count:
            return "faux négatif"
        return "anonymisation partielle ou portée incorrecte"


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    corpus_version: int
    cases: tuple[CaseResult, ...]
    thresholds: dict[str, float]
    required_exact_cases: tuple[str, ...]

    @property
    def total_cases(self) -> int:
        return len(self.cases)

    @property
    def exact_cases(self) -> int:
        return sum(case.exact for case in self.cases)

    @property
    def expected_sensitive_count(self) -> int:
        return sum(case.expected_count for case in self.cases)

    @property
    def literal_redacted_count(self) -> int:
        return sum(case.literal_redacted_count for case in self.cases)

    @property
    def exact_case_rate(self) -> float:
        return self.exact_cases / self.total_cases if self.total_cases else 0.0

    @property
    def literal_recall(self) -> float:
        expected = self.expected_sensitive_count
        return self.literal_redacted_count / expected if expected else 1.0

    @property
    def required_exact_cases_met(self) -> bool:
        exact_ids = {case.case_id for case in self.cases if case.exact}
        return set(self.required_exact_cases).issubset(exact_ids)

    @property
    def thresholds_met(self) -> bool:
        return (
            self.exact_case_rate >= self.thresholds["minimum_exact_case_rate"]
            and self.literal_recall >= self.thresholds["minimum_literal_recall"]
            and self.required_exact_cases_met
        )


def load_corpus(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        corpus = json.load(stream)
    if not isinstance(corpus.get("cases"), list) or not corpus["cases"]:
        raise ValueError("Le corpus doit contenir une liste non vide de cas")
    return corpus


def build_expected_output(text: str, sensitive_items: list[dict[str, str]]) -> str:
    spans: list[tuple[int, int]] = []
    for item in sensitive_items:
        value = item["value"]
        occurrences = text.count(value)
        if occurrences != 1:
            raise ValueError(
                f"La valeur attendue {value!r} doit apparaître exactement une fois, "
                f"occurrences trouvées : {occurrences}"
            )
        start = text.index(value)
        spans.append((start, start + len(value)))

    spans.sort()
    for previous, current in zip(spans, spans[1:]):
        if previous[1] > current[0]:
            raise ValueError("Les valeurs sensibles attendues ne doivent pas se chevaucher")

    expected = text
    for start, end in reversed(spans):
        expected = expected[:start] + SENSITIVE_PLACEHOLDER + expected[end:]
    return expected


def run_benchmark(corpus: dict[str, Any]) -> BenchmarkResult:
    seen_ids: set[str] = set()
    cases: list[CaseResult] = []
    for case in corpus["cases"]:
        case_id = case["id"]
        if case_id in seen_ids:
            raise ValueError(f"Identifiant de cas dupliqué : {case_id}")
        seen_ids.add(case_id)
        difficulty = case["difficulty"]
        if difficulty not in DIFFICULTY_ORDER:
            raise ValueError(f"Difficulté inconnue pour {case_id} : {difficulty}")

        sensitive_items = case["expected_sensitive"]
        expected_output = build_expected_output(case["input"], sensitive_items)
        actual_output, actual_count = anonymize_text(case["input"])
        literal_redacted_categories = tuple(
            item["category"]
            for item in sensitive_items
            if item["value"] not in actual_output
        )
        cases.append(
            CaseResult(
                case_id=case_id,
                title=case["title"],
                difficulty=difficulty,
                exact=actual_output == expected_output
                and actual_count == len(sensitive_items),
                expected_count=len(sensitive_items),
                actual_count=actual_count,
                literal_redacted_count=len(literal_redacted_categories),
                categories=tuple(item["category"] for item in sensitive_items),
                literal_redacted_categories=literal_redacted_categories,
                expected_output=expected_output,
                actual_output=actual_output,
                recommendation=case.get("recommendation", ""),
            )
        )

    thresholds = corpus.get("thresholds", {})
    required_exact_cases = tuple(corpus.get("required_exact_cases", ()))
    unknown_required_cases = set(required_exact_cases) - seen_ids
    if unknown_required_cases:
        raise ValueError(
            "Cas obligatoires inconnus : " + ", ".join(sorted(unknown_required_cases))
        )
    return BenchmarkResult(
        corpus_version=int(corpus.get("version", 1)),
        cases=tuple(cases),
        thresholds={
            "minimum_exact_case_rate": float(
                thresholds.get("minimum_exact_case_rate", 0.0)
            ),
            "minimum_literal_recall": float(
                thresholds.get("minimum_literal_recall", 0.0)
            ),
        },
        required_exact_cases=required_exact_cases,
    )


def _percent(value: float) -> str:
    return f"{value * 100:.1f} %".replace(".", ",")


def _markdown_code(text: str) -> str:
    return text.replace("`", "\\`").replace("\n", "\\n")


def render_report(result: BenchmarkResult, corpus_path: Path) -> str:
    lines = [
        "# Rapport du benchmark `/rgpd`",
        "",
        f"Corpus : `{corpus_path.name}` — version {result.corpus_version} — données synthétiques uniquement.",
        "",
        "## Résumé",
        "",
        "| Indicateur | Résultat | Seuil |",
        "|---|---:|---:|",
        f"| Cas exactement conformes | {result.exact_cases}/{result.total_cases} ({_percent(result.exact_case_rate)}) | {_percent(result.thresholds['minimum_exact_case_rate'])} |",
        f"| PII attendues absentes littéralement | {result.literal_redacted_count}/{result.expected_sensitive_count} ({_percent(result.literal_recall)}) | {_percent(result.thresholds['minimum_literal_recall'])} |",
        f"| Cas obligatoires conformes | {sum(case.exact for case in result.cases if case.case_id in result.required_exact_cases)}/{len(result.required_exact_cases)} | 100,0 % |",
        f"| Seuils de non-régression | {'respectés' if result.thresholds_met else 'non respectés'} | — |",
        "",
        "> Le rappel littéral indique qu'une valeur complète n'est plus présente. Il ne garantit pas qu'une PII partiellement anonymisée soit sûre ; la conformité exacte reste l'indicateur principal.",
        "",
        "## Résultats par difficulté",
        "",
        "| Difficulté | Conformes | Total | Taux |",
        "|---|---:|---:|---:|",
    ]

    for difficulty in DIFFICULTY_ORDER:
        difficulty_cases = [case for case in result.cases if case.difficulty == difficulty]
        exact = sum(case.exact for case in difficulty_cases)
        rate = exact / len(difficulty_cases) if difficulty_cases else 0.0
        lines.append(
            f"| {difficulty} | {exact} | {len(difficulty_cases)} | {_percent(rate)} |"
        )

    lines += [
        "",
        "## Résultats par catégorie",
        "",
        "| Catégorie | PII attendues | Absentes littéralement | Rappel littéral |",
        "|---|---:|---:|---:|",
    ]
    expected_by_category = Counter(
        category for case in result.cases for category in case.categories
    )
    redacted_by_category = Counter(
        category
        for case in result.cases
        for category in case.literal_redacted_categories
    )
    for category in sorted(expected_by_category):
        expected = expected_by_category[category]
        redacted = redacted_by_category[category]
        lines.append(
            f"| {category} | {expected} | {redacted} | {_percent(redacted / expected)} |"
        )

    lines += [
        "",
        "## Détail des écarts",
        "",
    ]
    failed_cases = [case for case in result.cases if not case.exact]
    if not failed_cases:
        lines.append("Aucun écart.")
    else:
        for case in failed_cases:
            lines += [
                f"### `{case.case_id}` — {case.title}",
                "",
                f"- Difficulté : {case.difficulty}",
                f"- Type d'écart : {case.issue}",
                f"- Remplacements attendus/obtenus : {case.expected_count}/{case.actual_count}",
                f"- Attendu : `{_markdown_code(case.expected_output)}`",
                f"- Obtenu : `{_markdown_code(case.actual_output)}`",
            ]
            if case.recommendation:
                lines.append(f"- Piste : {case.recommendation}")
            lines.append("")

    recommendations = [
        case.recommendation
        for case in failed_cases
        if case.recommendation
    ]
    lines += ["## Pistes d'amélioration prioritaires", ""]
    if recommendations:
        for recommendation, count in Counter(recommendations).most_common():
            suffix = f" ({count} cas)" if count > 1 else ""
            lines.append(f"- {recommendation}{suffix}")
    else:
        lines.append("Aucune piste issue des cas en échec.")

    lines += [
        "",
        "## Reproduction",
        "",
        "```powershell",
        "python scripts/benchmark_rgpd.py",
        "```",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark synthétique de /rgpd")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus = load_corpus(args.corpus)
    result = run_benchmark(corpus)
    report = render_report(result, args.corpus)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")
    print(
        f"Benchmark /rgpd : {result.exact_cases}/{result.total_cases} cas conformes, "
        f"rappel littéral {_percent(result.literal_recall)}."
    )
    print(f"Rapport écrit : {args.report}")
    return 0 if result.thresholds_met else 1


if __name__ == "__main__":
    raise SystemExit(main())
