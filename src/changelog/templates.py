BASE = """# CHANGELOG

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) and [Keep a Changelog](http://keepachangelog.com/).
"""

UNRELEASED = """
## Unreleased
---

### New

### Changes

### Fixes

### Breaks


"""

INIT = BASE + UNRELEASED

DEFAULT_VERSION = "0.0.0"

RELEASE_LINE = "## {0} - ({1})\n"

DATE_REGEX = r'(?P<date>\d{4}-\d{2}-\d{2})'
LOCAL_REGEX = r'(?P<local>\+[a-zA-Z0-9][a-zA-Z0-9\.]*[a-zA-Z0-9])'
VERSION_REGEX = r'\d+\.\d+\.\d+'
FULL_VERSION_REGEX = r'(?P<version>{version}{local}?)'.format(
    version=VERSION_REGEX,
    local=LOCAL_REGEX,
)

RELEASE_LINE_REGEXES = [
    regex.format(full_version=FULL_VERSION_REGEX, date=DATE_REGEX)
    for regex in [
        r"^##\s{full_version}\s\-\s\({date}\)$",
        r"^##\sv?{full_version}",
        r"^##\s\[{full_version}\]\s\-\s{date}$",
    ]
]
