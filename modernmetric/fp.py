import chardet
import os
import sys
import time
from typing import Optional

from pygments import lexers
from pygments_tsx.tsx import patch_pygments
from cachehash.main import Cache

from modernmetric.cls.modules import get_modules_calculated
from modernmetric.cls.modules import get_modules_metrics
from modernmetric.cls.importer.filtered import FilteredImporter
import modernmetric.config as config

patch_pygments()

start_time = time.time()


def print_time(msg, start_time=start_time):
    elapsed_time = time.time() - start_time
    print(f"{msg} took {elapsed_time:.2f} seconds")


def handle_rejected_file(_file, _args, old_file, err=None):
    _lexer = None
    res = {}
    store = {}
    lexer_name = "unknown"
    try:
        _lexer = lexers.get_lexer_for_filename(_file)
        lexer_name = _lexer.name
        if err:
            raise err
    except Exception as e:
        if not _args.ignore_lexer_errors:
            raise e

    return (res, old_file, lexer_name, [], store)


def file_process(_file, _args, _importer, cache: Optional[Cache] = None):
    print_time("Starting file process")
    old_file = _file
    _file = os.path.abspath(_file)
    _lexer = None
    """Process a file, using cachehash if available"""
    # Try to get cached result first
    if cache is not None and not getattr(_args, "no_cache", False):
        print_time("Checking cache")
        try:
            cached_result = cache.get(_file)
            if (
                cached_result is not None
                and isinstance(cached_result, dict)
                and cached_result.get("res")
                and cached_result.get("file")
                and cached_result.get("lexer_name")
                and cached_result.get("tokens")
                and cached_result.get("store")
            ):
                return (
                    cached_result["res"],
                    cached_result["file"],
                    cached_result["lexer_name"],
                    cached_result["tokens"],
                    cached_result["store"],
                )
        except Exception as e:
            print(f"Cache error: {e}", file=sys.stderr)

    res = {}
    store = {}

    try:
        if os.path.getsize(_file) > config.MAX_FILE_SIZE:
            return handle_rejected_file(
                _file, _args, old_file, err=ValueError("File too large")
            )
        with open(_file, "rb") as i:
            print_time("Reading file")
            _cnt = i.read()
            print_time("File read")
            sample = _cnt[0 : min(config.ENCODING_SAMPLE_SIZE, len(_cnt))]
            try:
                _enc = chardet.detect(sample)["encoding"] or "utf-8"
                print_time(f"Encoding detected: {_enc}")
                _cnt = _cnt.decode(_enc).encode("utf-8")
            except Exception as e:
                return handle_rejected_file(
                    _file, _args, old_file, err=ValueError("Encoding detection failed")
                )
        print_time("file re-encoded")
        _lexer = None
        sample = _cnt[0 : min(config.ENCODING_SAMPLE_SIZE, len(_cnt))]
        try:
            print_time("Trying guess_lexer_for_filename")
            _lexer = lexers.guess_lexer_for_filename(_file, str(sample))
        except Exception as e1:
            try:
                print_time("Trying guess_lexer")
                _lexer = lexers.guess_lexer(sample)
            except Exception as e2:
                try:
                    print_time("Trying get_lexer_for_filename")
                    _lexer = lexers.get_lexer_for_filename(_file)
                except Exception as e3:
                    print_time("Failing")
                    if _args.ignore_lexer_errors:
                        return (res, old_file, "unknown", [], store)
                    else:
                        print("Processing unknown file type: " + _file, file=sys.stderr)
                        print(e1)
                        print(e2)
                        raise e3

        if os.path.getsize(_file) == 0:
            return (res, old_file, _lexer.name, [], store)

        _localImporter = {k: FilteredImporter(v, _file) for k, v in _importer.items()}
        tokens = list(_lexer.get_tokens(str(_cnt)))

        if _args.dump:
            for x in tokens:
                print("{}: {} -> {}".format(_file, x[0], str(x[1])))
        else:
            _localMetrics = get_modules_metrics(_args, **_localImporter)
            _localCalc = get_modules_calculated(_args, **_localImporter)

            for x in _localMetrics:
                x.parse_tokens(_lexer.name, tokens)
                res.update(x.get_results())
                store.update(x.get_internal_store())

            for x in _localCalc:
                res.update(x.get_results(res))
                store.update(x.get_internal_store())

        result = (res, old_file, _lexer.name, tokens, store)
        resDict = {
            "res": res,
            "file": old_file,
            "lexer_name": _lexer.name,
            "tokens": tokens,
            "store": store,
        }

        # Store in cache if available
        if cache is not None and not getattr(_args, "no_cache", False):
            cache.set(_file, resDict)

        return result

    except Exception as e:
        print(f"Error processing file {_file}: {e}", file=sys.stderr)
        tokens = []
        name = "None"
        if _lexer:
            name = _lexer.name
        return (res, old_file, name, tokens, store)
