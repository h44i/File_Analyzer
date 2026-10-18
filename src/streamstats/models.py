from dataclasses import dataclass
from datetime import datetime

from streamstats.errors import Invalid_Event_Error, Invalid_Timestamp_Error

# допустимые уровни события
LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

# обязательные поля события
FIELDS = ("timestamp", "level", "source", "message")


# одно проверенное событие
@dataclass
class Event:
    timestamp: datetime
    level: str
    source: str
    message: str


# превращение строки ISO 8601 в datetime
def parse_timestamp(value, place: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        # ValueError - строка не в формате ISO 8601, TypeError - вообще не строка
        raise Invalid_Timestamp_Error(f"{place}: неверная временная метка {value}")

    return timestamp


# проверка словаря из файла и создание события
def create_event(data: dict, place: str) -> Event:
    # place - где находится строка, например "logs.jsonl, строка 3"

    # все обязательные поля есть
    for field in FIELDS:
        if data.get(field) is None:
            raise Invalid_Event_Error(f"{place}: нет поля {field}")

    level = data["level"]
    source = data["source"]
    message = data["message"]

    # level - один из допустимых уровней
    if level not in LEVELS:
        raise Invalid_Event_Error(f"{place}: неизвестный уровень {level}")

    # source - непустая строка
    if not isinstance(source, str) or source.strip() == "":
        raise Invalid_Event_Error(f"{place}: source должен быть непустой строкой")

    # message - строка
    if not isinstance(message, str):
        raise Invalid_Event_Error(f"{place}: message должен быть строкой")

    # timestamp - ISO 8601
    timestamp = parse_timestamp(data["timestamp"], place)

    return Event(timestamp, level, source, message)
