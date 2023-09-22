import subprocess
import setuptools

import os
import datetime


# Get the version from the git tag, and write to VERSION.
ref = None
if "GITHUB_REF" in os.environ:
    ref = os.environ["GITHUB_REF"]

if ref and ref is not None and ref.startswith("refs/tags/"):
    version = ref.replace("refs/tags/", "")
else:
    version = datetime.datetime.now().strftime("%Y.%m.%d%H%M%S")

print(version)

_long_description = "See https://github.com/startupos/modernmetric for documentation"  # noqa:E501
_long_description_content_type = "text/plain"
try:
    _long_description = subprocess.check_output(
        ["pandoc", "--from", "markdown", "--to", "rst", "README.md"]
    ).decode("utf-8")
    _long_description_content_type = "text/x-rst"
except (subprocess.CalledProcessError, FileNotFoundError):
    pass

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="modernmetric",
    version=version,
    author="Jason Nichols",
    author_email="jason@startupos.dev",
    description="Calculate code metrics in various languages",
    long_description=_long_description,
    long_description_content_type=_long_description_content_type,
    url="https://github.com/startupos/modernmetric",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "modernmetric = modernmetric.__main__:main",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Quality Assurance",
    ],
)
