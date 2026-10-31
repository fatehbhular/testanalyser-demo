from math import isfinite
from pathlib import Path
from pprint import pprint

from defusedxml.ElementTree import parse


def parse_duration(value: str | None) -> float | None:
    if value is None:
        return None

    try:
        duration = float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid test duration: {value!r}") from exc

    if not isfinite(duration) or duration < 0:
        raise ValueError(f"Invalid test duration: {value!r}")

    return duration


def parse_report(report_path: Path) -> list[dict[str, str | float | None]]:
    tree = parse(report_path, forbid_dtd=True)
    root = tree.getroot()

    if root.tag not in {"testsuites", "testsuite"}:
        raise ValueError(f"Unsupported report root: {root.tag}")

    results = []

    for suite in root.iter("testsuite"):
        for testcase in suite.findall("testcase"):
            outcome = "pass"
            message = None

            for tag, label in (
                ("error", "error"),
                ("failure", "fail"),
                ("skipped", "skip"),
            ):
                result = testcase.find(tag)

                if result is not None:
                    outcome = label
                    message = result.get("message")
                    break

            results.append(
                {
                    "suite": suite.get("name"),
                    "classname": testcase.get("classname"),
                    "name": testcase.get("name"),
                    "outcome": outcome,
                    "duration_seconds": parse_duration(testcase.get("time")),
                    "message": message,
                }
            )

    return results


if __name__ == "__main__":
    pprint(parse_report(Path("reports/results.xml")))