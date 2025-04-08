import argparse
import json
import textwrap
from multiprocessing import Pool, TimeoutError
from functools import partial
import sys
from typing import Union
from pathlib import Path
from cachehash.main import Cache

from modernmetric.cls.importer.pick import importer_pick
from modernmetric.cls.modules import get_additional_parser_args
from modernmetric.cls.modules import get_modules_calculated
from modernmetric.cls.modules import get_modules_metrics
from modernmetric.cls.modules import get_modules_stats
from modernmetric.fp import file_process
from modernmetric.license import report


def ArgParser(custom_args=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="modernmetric",
        description="Calculate code metrics in various languages",
        epilog=textwrap.dedent(
            """
        Currently you could import files of the following types for --warn_* or --coverage  # noqa: E501

        Following information can be read

            <file> = full path to file
            <content> = either a string
            <severity> = optional severity

            Note: you could also add a single line, then <content>
                has to be a number reflecting to total number of findings

        File formats

        csv: CSV file of following line format
             <file>,<content>,<severity>

        json: JSON file
             <file>: {
                 "content": <content>,
                 "severity": <severity>
             }
        """
        ),
    )
    parser.add_argument(
        "--output_file", default=None, help="File to write the output to"
    )
    parser.add_argument(
        "--warn_compiler",
        default=None,
        help="File(s) holding information about compiler warnings",
    )
    parser.add_argument(
        "--warn_duplication",
        default=None,
        help="File(s) holding information about code duplications",
    )
    parser.add_argument(
        "--warn_functional",
        default=None,
        help="File(s) holding information about static code analysis findings",
    )
    parser.add_argument(
        "--warn_standard",
        default=None,
        help="File(s) holding information about language standard violations",
    )
    parser.add_argument(
        "--warn_security",
        default=None,
        help="File(s) File(s) holding information about found security issue",
    )
    parser.add_argument(
        "--coverage",
        default=None,
        help="File(s) with compiler warningsFile(s) holding information about testing coverage",
    )  # noqa: E501
    parser.add_argument(
        "--dump", default=False, action="store_true", help="Just dump the token tree"
    )
    parser.add_argument("--jobs", type=int, default=1, help="Run x jobs in parallel")
    parser.add_argument(
        "--ignore_lexer_errors", default=True, help="Ignore unparseable files"
    )

    parser.add_argument(
        "--file", type=str, help="Path to the JSON file list of file paths"
    )

    parser.add_argument(
        "files", metavar="file", type=str, nargs="*", help="List of file paths"
    )

    # Add cachehash arguments
    parser.add_argument(
        "--cache-dir",
        default=".modernmetric_cache",
        help="Directory to store cache files (default: .modernmetric_cache)",
    )

    parser.add_argument(
        "--cache-db",
        default="modernmetric.db",
        help="SQLite database file for caching (default: modernmetric.db)",
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Disable result caching"
    )

    get_additional_parser_args(parser)

    if custom_args:
        RUNARGS = parser.parse_args(custom_args)
    else:
        RUNARGS = parser.parse_args()

    file_paths = RUNARGS.files
    input_file = RUNARGS.file

    if (
        not file_paths and not input_file
    ):  # No file passed in, read filelist from command line  # noqa: E501
        raise Exception(
            "No filelist provided. Provide path to file list with --file=<path>"
        )  # noqa: E501

    if input_file:
        with open(input_file) as file:
            data = json.load(file)
            if isinstance(data, dict) and "files" in data:
                for file in data["files"]:
                    RUNARGS.files.append(file["path"])
            elif isinstance(data, list):
                if all(isinstance(item, dict) and "path" in item for item in data):
                    for file in data:
                        RUNARGS.files.append(file["path"])
                else:
                    RUNARGS.files.extend(data)
    return RUNARGS


# process_file returns (res, _file, _lexer.name, tokens, store)
RES_KEY_RES = 0
RES_KEY_FILE = 1
RES_KEY_LEXER = 2
RES_KEY_TOKENS = 3
RES_KEY_STORE = 4


def process_file(f, args, importer):
    db_path = Path(Path.home(), args.cache_dir, args.cache_db)
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
    cache = None if args.no_cache else Cache(db_path, "modernmetric")
    return file_process(f, args, importer, cache)


# custom_args is an optional list of strings args,
# e.g. ["--file=path/to/filelist.json"]
def main(custom_args=None, license_identifier: Union[int, str] = None):

    if license_identifier:
        report(identifier=license_identifier, product="modernmetric")
    if custom_args:
        _args = ArgParser(custom_args)
    else:
        _args = ArgParser()
    _result = {"files": {}, "overall": {}}

    # Get importer
    _importer = {}
    _importer["import_compiler"] = importer_pick(_args, _args.warn_compiler)
    _importer["import_coverage"] = importer_pick(_args, _args.coverage)
    _importer["import_duplication"] = importer_pick(_args, _args.warn_duplication)
    _importer["import_functional"] = importer_pick(_args, _args.warn_functional)
    _importer["import_security"] = importer_pick(_args, _args.warn_standard)
    _importer["import_standard"] = importer_pick(_args, _args.warn_security)
    # sanity check
    _importer = {k: v for k, v in _importer.items() if v}

    # instance metric modules
    _overallMetrics = get_modules_metrics(_args, **_importer)
    _overallCalc = get_modules_calculated(_args, **_importer)

    stores = []
    # process_file_fn = partial(process_file, args=_args, importer=_importer)

    # file_count = 1
    total_files = len(_args.files)

    timeout_seconds = 360

    with Pool(processes=_args.jobs) as pool:
        # Submit all tasks asynchronously
        async_results = [
            pool.apply_async(process_file, args=(file, _args, _importer))
            for file in _args.files
        ]

        for idx, async_result in enumerate(async_results, start=1):
            try:
                file_result = async_result.get(timeout=timeout_seconds)
                stores.append(file_result[RES_KEY_STORE])
                _result["files"][file_result[RES_KEY_FILE]] = file_result[RES_KEY_RES]
            except TimeoutError:
                print(
                    f"\rTimeout processing file {idx} of {total_files}", file=sys.stderr
                )
                # Log the file that timed out
                print(f"Timeout processing file: {async_result}", file=sys.stderr)
                continue
            except Exception as e:
                # Handle any other exceptions that occur during processing
                print(
                    f"\rError processing file {idx} of {total_files}, {async_result}: {e}",
                    file=sys.stderr,
                )
                continue

            print(
                f"\rModernMetric analyzing file {idx} of {total_files}",
                file=sys.stderr,
                end="",
            )
            sys.stderr.flush()

    for y in _overallMetrics:
        _result["overall"].update(y.get_results_global([x for x in stores]))
    for y in _overallCalc:
        _result["overall"].update(y.get_results(_result["overall"]))
    for m in get_modules_stats(_args, **_importer):
        _result = m.get_results(_result, "files", "overall")
    if _args.dump:
        # Output
        print(json.dumps(_result, indent=2, sort_keys=True))
    if _args.output_file:
        with open(_args.output_file, "w") as f:
            f.write(json.dumps(_result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
