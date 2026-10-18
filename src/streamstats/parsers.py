import csv
import json
import logging

from streamstats.errors import Invalid_Event_Error, Invalid_Timestamp_Error
from streamstats.models import create_event

# оба парсера - генераторы: читают файл по одной строке и отдают события


# чтение JSONL: каждая строка файла - отдельный JSON-объект
def parse_jsonl(path, skip_invalid=False):
    with open(path, encoding="utf-8") as file:
        # читаем файл построчно
        for line_number, line in enumerate(file, start=1):
            # пустые строки пропускаем
            if line.strip() == "":
                continue

            place = f"{path}, строка {line_number}"

            try:
                event = json_line_to_event(line, place)
            except (Invalid_Event_Error, Invalid_Timestamp_Error) as e:
                if not skip_invalid:
                    raise
                logging.warning("строка пропущена: %s", e)
                event = None

            yield event


# превращение одной строки JSONL в событие
def json_line_to_event(line: str, place: str):
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        raise Invalid_Event_Error(f"{place}: некорректный JSON")

    # строка может быть правильным JSON, но не объектом, например [1, 2]
    if not isinstance(data, dict):
        raise Invalid_Event_Error(f"{place}: ожидался JSON-объект")

    return create_event(data, place)


# чтение CSV: первая строка - заголовок с названиями колонок
def parse_csv(path, skip_invalid=False):
    with open(path, encoding="utf-8", newline="") as file:
        # DictReader читает файл построчно и отдаёт каждую строку словарём
        reader = csv.DictReader(file)

        for line_number, row in enumerate(reader, start=2):
            place = f"{path}, строка {line_number}"

            try:
                event = create_event(row, place)
            except (Invalid_Event_Error, Invalid_Timestamp_Error) as e:
                if not skip_invalid:
                    raise
                logging.warning("строка пропущена: %s", e)
                event = None

            yield event
