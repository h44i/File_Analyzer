import json

import pytest

from streamstats.analysis import analyze_files
from streamstats.errors import Unsupported_Format_Error


# помощник: создать JSONL-файл из списка словарей
def write_jsonl(path, events):
    with open(path, "w", encoding="utf-8") as file:
        for event in events:
            file.write(json.dumps(event, ensure_ascii=False) + "\n")


def make_event(ts="2026-10-15T10:00:00", level="INFO", source="api", message="ok"):
    return {"timestamp": ts, "level": level, "source": source, "message": message}


def test_empty_file(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")

    stats = analyze_files([path], "jsonl")

    assert stats["total_events"] == 0
    assert stats["first_timestamp"] is None
    assert stats["last_timestamp"] is None
    assert stats["top_error_sources"] == {}


def test_empty_csv_file(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    assert analyze_files([path], "csv")["total_events"] == 0


def test_statistics(tmp_path):
    path = tmp_path / "a.jsonl"
    # события специально идут не по порядку времени
    write_jsonl(
        path,
        [
            make_event(ts="2026-10-15T10:00:00", level="INFO", source="api"),
            make_event(ts="2026-10-15T09:00:00", level="ERROR", source="db"),
            make_event(ts="2026-10-15T12:00:00", level="CRITICAL", source="db"),
            make_event(ts="2026-10-15T11:00:00", level="ERROR", source="api"),
        ],
    )

    stats = analyze_files([path], "jsonl")

    assert stats["total_events"] == 4
    assert stats["by_level"] == {"DEBUG": 0, "INFO": 1, "WARNING": 0, "ERROR": 2, "CRITICAL": 1}
    assert stats["by_source"] == {"api": 2, "db": 2}
    assert stats["top_error_sources"] == {"db": 2, "api": 1}
    assert stats["first_timestamp"].startswith("2026-10-15T09:00:00")
    assert stats["last_timestamp"].startswith("2026-10-15T12:00:00")


def test_skipped_lines(tmp_path):
    path = tmp_path / "a.jsonl"
    path.write_text(json.dumps(make_event()) + "\nмусор\nещё мусор\n", encoding="utf-8")

    stats = analyze_files([path], "jsonl", skip_invalid=True)

    assert stats["total_events"] == 1
    assert stats["skipped_lines"] == 2


def test_multiple_files(tmp_path):
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    write_jsonl(a, [make_event(source="api"), make_event(source="api")])
    write_jsonl(b, [make_event(source="db", level="ERROR")])

    stats = analyze_files([a, b], "jsonl")

    assert stats["total_events"] == 3
    assert stats["by_source"] == {"api": 2, "db": 1}


def test_unicode(tmp_path):
    path = tmp_path / "u.jsonl"
    write_jsonl(path, [make_event(source="сервис-оплаты", message="Ошибка 🔥")])

    stats = analyze_files([path], "jsonl")

    assert stats["by_source"] == {"сервис-оплаты": 1}


def test_unsupported_format(tmp_path):
    path = tmp_path / "a.xml"
    path.write_text("", encoding="utf-8")

    with pytest.raises(Unsupported_Format_Error):
        analyze_files([path], "xml")
