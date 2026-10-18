import json
import sys

from streamstats.__main__ import main

GOOD = '{"timestamp": "2026-10-15T10:00:00", "level": "ERROR", "source": "db", "message": "x"}'


# запускает main() и возвращает код выхода
def run(argv):
    # main() берёт аргументы из sys.argv - это список слов командной строки,
    # sys.argv[0] - имя программы, поэтому подставляем его первым
    old_argv = sys.argv
    sys.argv = ["streamstats"] + argv

    # при ошибке main() вызывает sys.exit(2), а sys.exit бросает SystemExit,
    # ловим его, чтобы тест не завершился вместе с программой
    try:
        main()
    except SystemExit as e:
        return e.code
    finally:
        # возвращаем настоящий sys.argv, чтобы не мешать другим тестам
        sys.argv = old_argv

    # main() дошла до конца без sys.exit - успех
    return 0


def test_cli_report(tmp_path):
    inp = tmp_path / "in.jsonl"
    out = tmp_path / "report.json"
    inp.write_text(GOOD + "\n" + GOOD + "\n", encoding="utf-8")

    code = run(["analyze", str(inp), "--format", "jsonl", "--output", str(out)])

    assert code == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total_events"] == 2
    assert report["top_error_sources"] == {"db": 2}


def test_cli_broken_line(tmp_path, capsys):
    inp = tmp_path / "in.jsonl"
    out = tmp_path / "report.json"
    inp.write_text(GOOD + "\n" + "мусор\n", encoding="utf-8")

    code = run(["analyze", str(inp), "--format", "jsonl", "--output", str(out)])

    assert code == 2
    # в сообщении есть файл и номер строки
    error = capsys.readouterr().err
    assert "in.jsonl" in error
    assert "строка 2" in error
    # отчёт не создан
    assert not out.exists()


def test_cli_skip_invalid(tmp_path):
    inp = tmp_path / "in.jsonl"
    out = tmp_path / "report.json"
    inp.write_text(GOOD + "\n" + "мусор\n", encoding="utf-8")

    code = run(["analyze", str(inp), "--format", "jsonl", "--skip-invalid", "--output", str(out)])

    assert code == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total_events"] == 1
    assert report["skipped_lines"] == 1


def test_cli_multiple_csv_files(tmp_path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    out = tmp_path / "report.json"
    header = "timestamp,level,source,message\n"
    a.write_text(header + "2026-10-15T10:00:00,ERROR,db,x\n", encoding="utf-8")
    b.write_text(header + "2026-10-15T11:00:00,INFO,api,y\n", encoding="utf-8")

    code = run(["analyze", str(a), str(b), "--format", "csv", "--output", str(out)])

    assert code == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total_events"] == 2


def test_cli_unicode(tmp_path):
    inp = tmp_path / "in.jsonl"
    out = tmp_path / "report.json"
    event = {
        "timestamp": "2026-10-15T10:00:00",
        "level": "INFO",
        "source": "платежи",
        "message": "🔥",
    }
    inp.write_text(json.dumps(event, ensure_ascii=False) + "\n", encoding="utf-8")

    assert run(["analyze", str(inp), "--format", "jsonl", "--output", str(out)]) == 0
    # в отчёте русские буквы, а не п...
    assert "платежи" in out.read_text(encoding="utf-8")


def test_cli_missing_file(tmp_path):
    assert run(["analyze", str(tmp_path / "nope.csv"), "--format", "csv"]) == 2


def test_cli_unsupported_format(tmp_path):
    inp = tmp_path / "in.jsonl"
    inp.write_text(GOOD + "\n", encoding="utf-8")

    assert run(["analyze", str(inp), "--format", "xml"]) == 2


def test_cli_help():
    # --help печатает справку и завершает программу с кодом 0
    assert run(["--help"]) == 0
