import os
import json
from modernmetric.__main__ import main as modernmetric_main
from pygments import lex
from pygments_tsx.tsx import ToolScriptLexer


def test_rsx_support(tmp_path):
    # Create a temporary output file in the test directory
    output_file = tmp_path / "rsx_test_output.json"

    # Get path to the sample RSX file
    current_dir = os.path.dirname(__file__)
    test_file = os.path.join(current_dir, "fixtures", "Sample.rsx")

    # Run modernmetric on the .rsx file
    modernmetric_main(custom_args=[test_file, "--output_file", str(output_file)])

    # Verify output exists and contains expected data
    assert output_file.exists()
    with open(output_file) as f:
        result = json.load(f)
        assert "files" in result
        assert any(f.endswith("Sample.rsx") for f in result["files"])


def test_rsx_lexer():
    # Get path to the sample RSX file
    current_dir = os.path.dirname(__file__)
    test_file = os.path.join(current_dir, "fixtures", "Sample.rsx")

    # Read the RSX file
    with open(test_file, "r") as f:
        code = f.read()

    # Create lexer and get tokens
    lexer = ToolScriptLexer()
    tokens = list(lex(code, lexer))

    # Test for RSX-specific components
    rsx_components = ["Container", "Text", "Table", "Button"]
    found_components = []

    for token_type, value in tokens:
        if value in rsx_components:
            found_components.append(value)
            print(f"Token: {token_type} -> {value}")

    # Verify all expected components were found
    assert set(found_components) == set(rsx_components), (
        f"Not all RSX components were found. Expected {rsx_components}, "
        f"got {found_components}"
    )

    # Test basic syntax elements
    code_elements = {
        "function": False,
        "const": False,
        "return": False,
        "MainToolScript": False,
    }

    for _, value in tokens:
        if value in code_elements:
            code_elements[value] = True

    # Verify basic syntax elements were found
    assert all(
        code_elements.values()
    ), f"Missing required code elements. Status: {code_elements}"

    assert (
        lexer.name == "ToolScript"
    ), f"Incorrect lexer name. Expected 'ToolScript', got '{lexer.name}'"
