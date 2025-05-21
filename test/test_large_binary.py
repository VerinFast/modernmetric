import json
import os
import time

import httpx

from modernmetric.__main__ import main as modernmetric

# NODE_24_ZIP_URL = "https://github.com/nodejs/node/archive/refs/tags/v24.0.0.zip"
NODE_24_ZIP_URL = "https://nodejs.org/dist/v24.0.0/node-v24.0.0-linux-s390x.tar.xz"
TMP_PATH = "testfiles/node_24.zip"


def download_file(url, filepath):
    if os.path.exists(filepath):
        print(f"File {filepath} already exists. Skipping download.")
        return
    print(f"Downloading {url} to {filepath}")

    # Use httpx to download the file
    start_time = time.time()
    with open(filepath, "wb") as file:
        with httpx.stream("GET", url) as response:
            for chunk in response.iter_bytes():
                file.write(chunk)
    duration = time.time() - start_time
    print(f"Download completed in {duration:.2f} seconds")


def test_filelist_scan():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    download_file(NODE_24_ZIP_URL, TMP_PATH)
    start_time = time.time()
    project_root = os.path.dirname(curr_dir)
    stats_input_file = os.path.join(project_root, "testfiles", "samplefilelist2.json")
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
    duration = time.time() - start_time
    print(f"Big binary scan took: {duration:.2f} seconds")
    assert duration < 100, "Scan took too long for large binary file"
