from collections import Counter

from streamstats.errors import Unsupported_Format_Error
from streamstats.parsers import parse_csv, parse_jsonl


# подсчёт статистики по одному или нескольким файлам
def analyze_files(paths: list, fmt: str, skip_invalid=False) -> dict:
    # выбор парсера по формату
    if fmt == "csv":
        parser = parse_csv
    elif fmt == "jsonl":
        parser = parse_jsonl
    else:
        raise Unsupported_Format_Error(f"Неподдерживаемый формат: {fmt}")

    total = 0
    by_level = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
    by_source = Counter()
    error_sources = Counter()
    first = None
    last = None
    skipped = 0

    # одни и те же счётчики для всех файлов - так статистика объединяется
    for path in paths:
        for event in parser(path, skip_invalid):
            # None - строка была битой и её пропустили
            if event is None:
                skipped += 1
                continue

            total += 1
            by_level[event.level] += 1
            by_source[event.source] += 1

            if event.level in ("ERROR", "CRITICAL"):
                error_sources[event.source] += 1

            # события в файле не обязательно идут по порядку,
            # поэтому ищем самую раннюю и самую позднюю метку
            if first is None or event.timestamp < first:
                first = event.timestamp
            if last is None or event.timestamp > last:
                last = event.timestamp

    return {
        "total_events": total,
        "by_level": by_level,
        "by_source": dict(by_source),
        "top_error_sources": dict(error_sources.most_common(5)),
        "first_timestamp": first.isoformat() if first else None,
        "last_timestamp": last.isoformat() if last else None,
        "skipped_lines": skipped,
    }
