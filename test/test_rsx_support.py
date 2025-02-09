import os
import json
from modernmetric.__main__ import main as modernmetric_main


def test_rsx_support(tmp_path):
    # Create a temporary output file in the test directory
    output_file = tmp_path / "rsx_test_output.json"

    # Get path to the sample RSX file
    current_dir = os.path.dirname(__file__)
    test_file = os.path.join(current_dir, "fixtures", "Sample.rsx")

    # Run modernmetric on the .rsx file
    modernmetric_main(custom_args=[
        test_file,
        "--output_file", str(output_file)
    ])

    # Verify output exists and contains expected data
    assert output_file.exists()
    with open(output_file) as f:
        result = json.load(f)
        assert "files" in result
        assert any(f.endswith("Sample.rsx") for f in result["files"])
