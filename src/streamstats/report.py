import json


# запись отчёта в JSON-файл, а если файл не указан вывод в консоль
def write_report(stats: dict, output=None) -> None:
    # ensure_ascii=False - русские буквы остаются буквами, indent=2 - отступы
    text = json.dumps(stats, ensure_ascii=False, indent=2)

    if output is None:
        print(text)
    else:
        with open(output, "w", encoding="utf-8") as file:
            file.write(text)
