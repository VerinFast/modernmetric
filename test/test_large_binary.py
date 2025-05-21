import json
import os
import time

import httpx

from modernmetric.__main__ import main as modernmetric

NODE_24_ZIP_URL = "https://github.com/nodejs/node/archive/refs/tags/v24.0.0.zip"
TMP_PATH = "testfiles/node_24.zip"


def download_file(url, filepath):
    print(f"Downloading {url} to {filepath}")
    with httpx.stream("GET", url, follow_redirects=True) as response:
        with open(filepath, "wb") as file:
            print(f"Response status code: {response.status_code}")
            if response.status_code == 302:
               # Handle redirection
                location = response.headers.get("Location")
                print(f"Redirected to {location}")
            if response.status_code != 200:
                raise Exception(f"Failed to download file: {response.status_code}")
            if response.headers.get("Content-Length"):
                total_length = int(response.headers.get("Content-Length"))
                print(f"Total length: {total_length} bytes")
            else:
                total_length = None
            if total_length:
                downloaded = 0
                for chunk in response.iter_raw():
                    file.write(chunk)
                    downloaded += len(chunk)
                    done = int(50 * downloaded / total_length)
                    print(f"\r[{'#' * done}{'.' * (50 - done)}] {downloaded}/{total_length} bytes", end="")
            else:
                print("No Content-Length header, downloading without progress")
                # If no content length is provided, just download the file
                # without showing progress
                for chunk in response.iter_raw():
                    file.write(chunk)

def wait_until_file_stable(path, timeout=30):
    last_size = -1
    start = time.time()
    while time.time() - start < timeout:
        try:
            current_size = os.path.getsize(path)
            if current_size == last_size:
                return
            last_size = current_size
        except FileNotFoundError:
            pass
        time.sleep(0.5)
    raise TimeoutError("File did not become stable")

def test_large_binary_scan():
    start_time = time.time()
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    download_file(NODE_24_ZIP_URL, TMP_PATH)
    wait_until_file_stable(TMP_PATH)
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
    assert duration < 300, "Scan took too long for large binary file"
