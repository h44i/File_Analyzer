import argparse
import logging
import sys

from streamstats.analysis import analyze_files
from streamstats.errors import CLI_Config_Error, StreamStatsError
from streamstats.report import write_report


def main():
    parser = argparse.ArgumentParser(
        prog="streamstats",
        description="Потоковый анализатор событий из CSV и JSONL",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="посчитать статистику по файлам",
    )
    analyze_parser.add_argument("INPUT", nargs="+")
    analyze_parser.add_argument("--format", dest="fmt", metavar="FORMAT", required=True)
    analyze_parser.add_argument("--output", metavar="REPORT")
    analyze_parser.add_argument("--skip-invalid", action="store_true")

    args = parser.parse_args()

    # WARNING о пропущенных строках выводятся в консоль
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    try:
        if args.command == "analyze":
            try:
                stats = analyze_files(args.INPUT, args.fmt, args.skip_invalid)
            except FileNotFoundError as e:
                # open() не нашёл входной файл - превращаем стандартную ошибку
                # в нашу, чтобы её поймал except StreamStatsError ниже
                raise CLI_Config_Error(f"Файл не найден: {e.filename}")

            write_report(stats, args.output)

    except StreamStatsError as e:
        print(e, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
