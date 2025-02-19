import os
import json
from modernmetric.fp import file_process
from modernmetric.cls.modules import get_modules_metrics, get_modules_calculated
from pathlib import Path
from modernmetric.__main__ import main as modernmetric


class MockArgs:
    """Mock args class for testing"""

    def __init__(self):
        self.ignore_lexer_errors = True
        self.dump = False
        self.halstead_bug_predict_method = "new"
        self.maintenance_index_calc_method = "default"
        self.warn_compiler = None
        self.coverage = None
        self.warn_duplication = None
        self.warn_functional = None
        self.warn_standard = None
        self.warn_security = None


def test_scan_self():
    """Test that modernmetric can scan its own codebase"""

    # Get modernmetric's root directory
    root_dir = Path(__file__).parent.parent / "modernmetric"

    # Get all files
    python_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    assert len(python_files) > 0, "No Python files found to analyze"

    # Process files
    args = MockArgs()
    importer = {}
    results = []

    expected_metrics = {}
    for file in python_files:
        result = file_process(file, args, importer)
        results.append(result)

        # Print metrics for debugging
        print(f"Metrics for {file}: {result[0]}")

        # Skip files with no metrics
        if not result[0]:
            continue

        # Test individual file metrics
        expected_metrics = {
            "cyclomatic_complexity": int,
            "loc": int,
            "code_loc": int,
            "documentation_loc": int,
            "string_loc": int,
            "empty_loc": int,
            "comment_ratio": float,
            "halstead_volume": float,
            "halstead_difficulty": float,
            "halstead_effort": float,
            "halstead_timerequired": float,
            "operands_sum": int,
            "operands_uniq": int,
            "operators_sum": int,
            "operators_uniq": int,
        }

        for metric, expected_type in expected_metrics.items():
            assert metric in result[0], f"Missing metric: {metric}"
            assert isinstance(result[0][metric], expected_type), (
                f"Metric {metric} has wrong type. Expected {expected_type}, "
                f"got {type(result[0][metric])}"
            )

            # sanity checks
            if expected_type in (int, float):
                assert result[0][metric] >= 0, f"Metric {metric} should be non-negative"

    # Test aggregate metrics
    overall_metrics = get_modules_metrics(args, **importer)
    overall_calc = get_modules_calculated(args, **importer)

    overall_results = {}
    for metric in overall_metrics:
        overall_results.update(metric.get_results_global([x[4] for x in results]))

    for calc in overall_calc:
        overall_results.update(calc.get_results(overall_results))

    # Test expected aggregate results
    for metric, expected_type in expected_metrics.items():
        assert metric in overall_results, f"Missing aggregate metric: {metric}"
        assert isinstance(overall_results[metric], expected_type), (
            f"Aggregate metric {metric} has wrong type. "
            f"Expected {expected_type}, "
            f"got {type(overall_results[metric])}"
        )

        # Verify aggregate values make sense
        if expected_type in (int, float):
            assert (
                overall_results[metric] >= 0
            ), f"Aggregate metric {metric} should be non-negative"

            # For metrics that should sum up
            if metric in [
                "loc",
                "code_loc",
                "documentation_loc",
                "string_loc",
                "empty_loc",
            ]:
                file_sum = sum(result[0][metric] for result in results if result[0])
                assert (
                    overall_results[metric] == file_sum
                ), f"Aggregate {metric} should equal sum of individual values"


def test_filelist_scan():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(curr_dir)
    stats_input_file = os.path.join(project_root, "testfiles", "samplefilelist.json")
    stats_output_file = os.path.join(curr_dir, "test.stats.json")
    custom_args = [f"--file={stats_input_file}", f"--output={stats_output_file}"]
    modernmetric(custom_args=custom_args, license_identifier="unit_test")
    with open(stats_output_file, "r") as f:
        stats = json.load(f)
    files = stats["files"]
    assert files is not None
    assert files["testfiles/test.c"]["loc"] == 25
    assert files["testfiles/test.c"]["cyclomatic_complexity"] == 0
    assert stats["overall"]["loc"] == 179
    os.remove(stats_output_file)


def main():
    """Run the self-scan test"""
    test_scan_self()
    print("All tests passed successfully!")


if __name__ == "__main__":
    main()
