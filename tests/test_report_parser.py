from inspect_report import parse_report

from xml.etree.ElementTree import ParseError

import pytest
from defusedxml.common import DTDForbidden

def test_parse_report_extracts_all_outcomes(tmp_path):
    report = tmp_path / "results.xml"
    report.write_text(
        """
        <testsuites>
            <testsuite name="example">
                <testcase classname="ExampleTests" name="passes" time="0.125" />
                <testcase classname="ExampleTests" name="fails">
                    <failure message="Expected value did not match" />
                </testcase>
                <testcase classname="ExampleTests" name="errors">
                    <error message="Setup failed" />
                </testcase>
                <testcase classname="ExampleTests" name="skips">
                    <skipped message="Feature unavailable" />
                </testcase>
            </testsuite>
        </testsuites>
        """,
        encoding="utf-8",
    )

    results = parse_report(report)

    assert len(results) == 4

    by_name = {result["name"]: result for result in results}

    assert by_name["passes"] == {
        "suite": "example",
        "classname": "ExampleTests",
        "name": "passes",
        "outcome": "pass",
        "duration_seconds": 0.125,
        "message": None,
    }

    assert by_name["fails"]["outcome"] == "fail"
    assert by_name["fails"]["message"] == "Expected value did not match"

    assert by_name["errors"]["outcome"] == "error"
    assert by_name["errors"]["message"] == "Setup failed"

    assert by_name["skips"]["outcome"] == "skip"
    assert by_name["skips"]["message"] == "Feature unavailable"


def test_parse_report_rejects_malformed_xml(tmp_path):
    report = tmp_path / "malformed.xml"
    report.write_text(
        "<testsuites><testsuite></testsuites>",
        encoding="utf-8",
    )

    with pytest.raises(ParseError):
        parse_report(report)


def test_parse_report_rejects_dtd(tmp_path):
    report = tmp_path / "unsafe.xml"
    report.write_text(
        """\
<!DOCTYPE testsuite [
    <!ENTITY example "entity content">
]>
<testsuite name="example">
    <testcase name="sample">&example;</testcase>
</testsuite>
""",
        encoding="utf-8",
    )

    with pytest.raises(DTDForbidden):
        parse_report(report)


def test_parse_report_rejects_unsupported_root(tmp_path):
    report = tmp_path / "unsupported.xml"
    report.write_text("<document />", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported report root"):
        parse_report(report)

def test_parse_report_supports_standalone_testsuite(tmp_path):
    report = tmp_path / "standalone.xml"
    report.write_text(
        """
        <testsuite name="standalone">
            <testcase classname="ExampleTests" name="passes" time="0.250" />
        </testsuite>
        """,
        encoding="utf-8",
    )

    results = parse_report(report)

    assert results == [
        {
            "suite": "standalone",
            "classname": "ExampleTests",
            "name": "passes",
            "outcome": "pass",
            "duration_seconds": 0.250,
            "message": None,
        }
    ]

@pytest.mark.parametrize(
    ("time_attribute", "expected"),
    [
        ('time="0.125"', 0.125),
        ('time="0"', 0.0),
        ("", None),
    ],
)
def test_parse_report_normalises_duration(tmp_path, time_attribute, expected):
    report = tmp_path / "duration.xml"
    report.write_text(
        f"""
        <testsuite name="example">
            <testcase name="sample" {time_attribute} />
        </testsuite>
        """,
        encoding="utf-8",
    )

    results = parse_report(report)

    assert results[0]["duration_seconds"] == expected


@pytest.mark.parametrize("duration", ["invalid", "", "-1", "NaN", "inf"])
def test_parse_report_rejects_invalid_duration(tmp_path, duration):
    report = tmp_path / "duration.xml"
    report.write_text(
        f"""
        <testsuite name="example">
            <testcase name="sample" time="{duration}" />
        </testsuite>
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid test duration"):
        parse_report(report)