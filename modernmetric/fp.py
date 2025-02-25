import sys
import chardet
import json
from typing import Optional
from pygments import lexers
from pygments_tsx.tsx import patch_pygments
from cachehash.main import Cache

from modernmetric.cls.modules import get_modules_calculated
from modernmetric.cls.modules import get_modules_metrics
from modernmetric.cls.importer.filtered import FilteredImporter

patch_pygments()


def file_process(_file, _args, _importer, cache: Optional[Cache] = None):
    """Process a file, using cachehash if available"""
    # Try to get cached result first
    if cache is not None and not getattr(_args, "no_cache", False):
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
        _lexer = lexers.get_lexer_for_filename(_file)
    except Exception as e:
        if _args.ignore_lexer_errors:
            # Printing to stderr since we write results to STDOUT
            print("Processing unknown file type: " + _file, file=sys.stderr)
            return (res, _file, "unknown", [], store)
        else:
            raise e

    try:
        with open(_file, "rb") as i:
            _cnt = i.read()
            _enc = chardet.detect(_cnt)
            _cnt = _cnt.decode(_enc["encoding"]).encode("utf-8")

        _localImporter = {k: FilteredImporter(v, _file) for k, v in _importer.items()}
        tokens = list(_lexer.get_tokens(_cnt))

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

        result = (res, _file, _lexer.name, tokens, store)
        resDict = {
            "res": res,
            "file": _file,
            "lexer_name": _lexer.name,
            "tokens": tokens,
            "store": store,
        }

        # Store in cache if available
        if cache is not None and not getattr(_args, "no_cache", False):
            cache.set(_file, json.dumps(resDict))

        return result

    except Exception as e:
        print(f"Error processing file {_file}: {e}", file=sys.stderr)
        tokens = []
        return (res, _file, _lexer.name, tokens, store)
