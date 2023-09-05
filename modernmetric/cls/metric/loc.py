from modernmetric.cls.base import MetricBase
import pygments
import pygments.lexer
import pygments.lexers
import pygments.token
import pygments.util

from pygount.analysis import (
    white_characters, 
    white_code_words, 
    _delined_tokens,
    _pythonized_comments
)


def _line_parts(tokens, language_id: str):
    line_marks = set()
    white_text = " \f\n\r\t" + white_characters(language_id)
    white_words = white_code_words(language_id)
    for token_type, token_text in tokens:
        # NOTE: Pygments treats preprocessor statements as special comments.
        is_actual_comment = token_type in pygments.token.Comment and token_type not in (
            pygments.token.Comment.Preproc,
            pygments.token.Comment.PreprocFile,
        )
        if is_actual_comment:
            line_marks.add("d")  # 'documentation'
        elif token_type in pygments.token.String:
            line_marks.add("s")  # 'string'
        else:
            is_white_text = (token_text.strip() in white_words) or (token_text.rstrip(white_text) == "")
            if not is_white_text:
                line_marks.add("c")  # 'code'
            
        if token_text.endswith("\n"):
            yield line_marks
            line_marks = set()
    if len(line_marks) >= 1:
        yield line_marks


class MetricBaseLOC(MetricBase):
    METRIC_LOC = "loc"
    METRIC_CLOC = "code_loc"
    METRIC_DLOC = "documentation_loc"
    METRIC_SLOC = "string_loc"
    METRIC_ELOC = "empty_loc"

    metrics = {
        "c": METRIC_CLOC,
        "d": METRIC_DLOC,
        "e": METRIC_ELOC,
        "s": METRIC_SLOC
    }

    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)

    def parse_tokens(self, language, tokens):
        super().parse_tokens(language, [])
        tokens = _delined_tokens(tokens)
        if language.lower() == "python":
            tokens = _pythonized_comments(tokens)
        language_id = language.lower()
        mark_to_count_map = {"c": 0, "d": 0, "e": 0, "s": 0}
        for line_parts in _line_parts(tokens, language_id):
            mark_to_increment = "e"
            for mark_to_check in ("d", "s", "c"):
                if mark_to_check in line_parts:
                    mark_to_increment = mark_to_check
            mark_to_count_map[mark_to_increment] += 1

        self._metrics[MetricBaseLOC.METRIC_LOC] = 0
        for mark_type in mark_to_count_map:
            if MetricBaseLOC.metrics[mark_type] not in self._metrics:
                self._metrics[MetricBaseLOC.metrics[mark_type]] = 0    
            self._metrics[MetricBaseLOC.metrics[mark_type]] += mark_to_count_map[mark_type]
            if mark_type == 'c' or mark_type != 's':
                self._metrics[MetricBaseLOC.METRIC_LOC] += mark_to_count_map[mark_type]
            self._metrics[MetricBaseLOC.metrics[mark_type]] = max(mark_to_count_map[mark_type],1)
        self._metrics[MetricBaseLOC.METRIC_LOC] = max(self._metrics[MetricBaseLOC.METRIC_LOC], 1)
        self._metrics[MetricBaseLOC.METRIC_CLOC] = max(self._metrics[MetricBaseLOC.METRIC_CLOC], 1)
        self._metrics[MetricBaseLOC.METRIC_DLOC] = max(self._metrics[MetricBaseLOC.METRIC_DLOC], 1)
        self._metrics[MetricBaseLOC.METRIC_ELOC] = max(self._metrics[MetricBaseLOC.METRIC_ELOC], 1)
        self._metrics[MetricBaseLOC.METRIC_SLOC] = max(self._metrics[MetricBaseLOC.METRIC_SLOC], 1)
        
        self._internalstore[MetricBaseLOC.METRIC_LOC] = self._metrics[MetricBaseLOC.METRIC_LOC]
        self._internalstore[MetricBaseLOC.METRIC_CLOC] = self._metrics[MetricBaseLOC.METRIC_CLOC]
        self._internalstore[MetricBaseLOC.METRIC_DLOC] = self._metrics[MetricBaseLOC.METRIC_DLOC]
        self._internalstore[MetricBaseLOC.METRIC_ELOC] = self._metrics[MetricBaseLOC.METRIC_ELOC]
        self._internalstore[MetricBaseLOC.METRIC_SLOC] = self._metrics[MetricBaseLOC.METRIC_SLOC]

    def get_results_global(self, value_stores):
        _sum_LOC = sum([x[MetricBaseLOC.METRIC_LOC] for x in self._get_all_matching_store_objects(value_stores)])
        _sum_CLOC = sum([x[MetricBaseLOC.METRIC_CLOC] for x in self._get_all_matching_store_objects(value_stores)])
        _sum_DLOC = sum([x[MetricBaseLOC.METRIC_DLOC] for x in self._get_all_matching_store_objects(value_stores)])
        _sum_ELOC = sum([x[MetricBaseLOC.METRIC_ELOC] for x in self._get_all_matching_store_objects(value_stores)])
        _sum_SLOC = sum([x[MetricBaseLOC.METRIC_SLOC] for x in self._get_all_matching_store_objects(value_stores)])
        return { 
            MetricBaseLOC.METRIC_LOC: _sum_LOC,
            MetricBaseLOC.METRIC_CLOC: _sum_CLOC,
            MetricBaseLOC.METRIC_DLOC: _sum_DLOC,
            MetricBaseLOC.METRIC_ELOC: _sum_ELOC,
            MetricBaseLOC.METRIC_SLOC: _sum_SLOC
        }