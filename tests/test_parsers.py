import pytest

from streamstats.errors import Invalid_Event_Error, Invalid_Timestamp_Error
from streamstats.parsers import parse_csv, parse_jsonl

GOOD_1 = '{"timestamp": "2026-10-15T10:00:00", "level": "INFO", "source": "api", "message": "ok"}'
GOOD_2 = '{"timestamp": "2026-10-15T11:00:00", "level": "ERROR", "source": "db", "message": "x"}'

CSV_HEADER = "timestamp,level,source,message\n"


# ---------- JSONL ----------


def test_parse_jsonl(tmp_path):
    path = tmp_path / "a.jsonl"
    path.write_text(GOOD_1 + "\n" + GOOD_2 + "\n", encoding="utf-8")

    events = list(parse_jsonl(path))

    assert len(events) == 2
    assert events[0].level == "INFO"
    assert events[1].source == "db"


def test_jsonl_broken_line_default(tmp_path):
    path = tmp_path / "a.jsonl"
    path.write_text(GOOD_1 + "\n" + "{битая строка\n", encoding="utf-8")

    # без skip_invalid битая строка останавливает чтение
    with pytest.raises(Invalid_Event_Error, match="строка 2"):
        list(parse_jsonl(path))


def test_jsonl_broken_line_skip(tmp_path, caplog):
    path = tmp_path / "a.jsonl"
    path.write_text(GOOD_1 + "\n" + "{битая строка\n" + GOOD_2 + "\n", encoding="utf-8")

    events = list(parse_jsonl(path, skip_invalid=True))

    # вместо битой строки - None, а чтение продолжилось дальше
    assert events[1] is None
    assert events[2].source == "db"
    # в лог записан WARNING
    assert "строка 2" in caplog.text


def test_jsonl_bad_timestamp(tmp_path):
    path = tmp_path / "a.jsonl"
    path.write_text(
        '{"timestamp": "вчера", "level": "INFO", "source": "api", "message": "x"}\n',
        encoding="utf-8",
    )

    with pytest.raises(Invalid_Timestamp_Error):
        list(parse_jsonl(path))


def test_jsonl_unknown_level(tmp_path):
    path = tmp_path / "a.jsonl"
    path.write_text(
        '{"timestamp": "2026-10-15T10:00:00", "level": "LOUD", "source": "api", "message": "x"}\n',
        encoding="utf-8",
    )

    with pytest.raises(Invalid_Event_Error, match="неизвестный уровень"):
        list(parse_jsonl(path))


# ---------- CSV ----------


def test_parse_csv(tmp_path):
    path = tmp_path / "a.csv"
    path.write_text(
        CSV_HEADER
        + "2026-10-15T10:00:00,INFO,api,start\n"
        + '2026-10-15T11:00:00,ERROR,db,"timeout, retry"\n',
        encoding="utf-8",
    )

    events = list(parse_csv(path))

    assert len(events) == 2
    assert events[0].source == "api"
    # запятая внутри кавычек не разбивает поле на два
    assert events[1].message == "timeout, retry"


def test_csv_broken_line_default(tmp_path):
    path = tmp_path / "a.csv"
    path.write_text(
        CSV_HEADER + "2026-10-15T10:00:00,INFO,api,ok\n" + "2026-10-15T10:00:00,,api,x\n",
        encoding="utf-8",
    )

    with pytest.raises(Invalid_Event_Error, match="строка 3"):
        list(parse_csv(path))


def test_csv_broken_line_skip(tmp_path):
    path = tmp_path / "a.csv"
    path.write_text(
        CSV_HEADER + "2026-10-15T10:00:00,INFO,api,ok\n" + "2026-10-15T10:00:00,,api,x\n",
        encoding="utf-8",
    )

    events = list(parse_csv(path, skip_invalid=True))

    assert events[0].source == "api"
    assert events[1] is None
