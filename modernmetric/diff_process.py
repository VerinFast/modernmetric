import sys
from pygments import lexers
from modernmetric.cls.modules import get_modules_calculated, get_modules_metrics
from modernmetric.cls.importer.filtered import FilteredImporter


def process_diff_content(_content, _file, _args, _importer):
    res = {}
    store = {}

    try:
        _lexer = lexers.get_lexer_for_filename(_file)
    except Exception as e:
        if _args.ignore_lexer_errors:
            print("Processing unknown file type: " + _file, file=sys.stderr)
            return (res, _file, "unknown", [], store)
        else:
            raise e

    try:
        _localImporter = {k: FilteredImporter(v, _file) for k, v in _importer.items()}
        tokens = list(_lexer.get_tokens(_content))

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
    except Exception:
        tokens = []

    return (res, _file, _lexer.name, tokens, store)
