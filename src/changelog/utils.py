import os
import re
from datetime import date

from packaging.version import Version

from changelog.exceptions import ChangelogDoesNotExistError
from changelog.templates import (
    DEFAULT_VERSION,
    INIT,
    RELEASE_LINE,
    RELEASE_LINE_REGEXES,
    UNRELEASED,
    VERSION_REGEX,
)


class ChangelogUtils:
    CHANGELOG = 'CHANGELOG.md'
    SECTIONS = {
        'new': "### New\n",
        'fix': "### Fixes\n",
        'change': '### Changes\n',
        'break': "### Breaks\n"
    }
    REVERSE_SECTIONS = {v: k for k, v in SECTIONS.items()}

    def initialize_changelog_file(self):
        """
        Creates a changelog if one does not already exist
        """
        if os.path.isfile(self.CHANGELOG):
            return "{} already exists".format(self.CHANGELOG)
        with open(self.CHANGELOG, 'w') as changelog:
            changelog.write(INIT)
        return "Created {}".format(self.CHANGELOG)

    def get_changelog_data(self):
        """
        Gets all of the lines from the current changelog
        """
        if not os.path.isfile(self.CHANGELOG):
            raise ChangelogDoesNotExistError
        with open(self.CHANGELOG, 'r') as changelog:
            data = changelog.readlines()
        return data

    def write_changelog(self, line_list):
        """
        writes the lines out to the changelog
        """
        with open(self.CHANGELOG, 'w') as changelog:
            changelog.writelines(line_list)

    def update_section(self, section, message):
        """Updates a section of the changelog with message"""
        data = self.get_changelog_data()
        i = data.index(self.SECTIONS[section]) + 1
        data.insert(i, "* {}\n".format(message))
        self.write_changelog(data)

    def get_current_version(self):
        """Gets the Current Application Version Based on Changelog"""
        data = self.get_changelog_data()
        for line in data:
            version = self.match_version(line)
            if version is not None:
                return version
        return Version(DEFAULT_VERSION)

    def get_changes(self):
        """Get the list of chances since the last release"""
        data = self.get_changelog_data()
        changes = {}
        reading = False
        section = None
        for line in data:
            if line in ['---\n', '\n']:
                continue
            if self.match_version(line):
                break
            if reading:
                if line in self.REVERSE_SECTIONS:
                    section = self.REVERSE_SECTIONS[line]
                    continue
                else:
                    changes[section] = line.strip().lstrip("* ")
                    continue
            if line == "## Unreleased\n":
                reading = True
                continue

        return changes

    def get_release_suggestion(self):
        """Suggests a release type"""
        changes = self.get_changes()
        if 'break' in changes:
            return "major"
        elif 'new' in changes:
            return "minor"
        return "patch"

    def get_new_release_version(self, release_type, local=None):
        """
        Returns the version of the new release
        """
        current = self.get_current_version()
        if release_type not in ['major', 'minor', 'patch']:
            release_type = self.get_release_suggestion()

        version = DEFAULT_VERSION if local else current.base_version
        version_in_local = False

        if local and current.local and local in current.local:
            version_in_local = re.search(VERSION_REGEX, current.local)
            if version_in_local:
                version = version_in_local.group()

        new_version = self.bump_version(version, release_type)
        if local:
            if version_in_local:
                new_local = re.sub(VERSION_REGEX, new_version, current.local)
            else:
                new_local = local + new_version
            new_version = '+'.join([current.base_version, new_local])

        return new_version

    def cut_release(self, release_type="suggest", local=None):
        """Cuts a release and updates changelog"""
        new_version = self.get_new_release_version(release_type, local=local)
        changes = self.get_changes()
        data = self.get_changelog_data()
        output = []
        unreleased_position = 0
        reading = True
        for i, line in enumerate(data):
            if self.match_version(line):
                reading = False
            if line == "## Unreleased\n":
                unreleased_position = i
                line = RELEASE_LINE.format(new_version, date.today().isoformat())
            if reading and line in self.REVERSE_SECTIONS and self.REVERSE_SECTIONS[line] not in changes:
                continue
            output.append(line)
        output.insert(unreleased_position, UNRELEASED)
        output = self.crunch_lines(output)
        self.write_changelog(output)

    def crunch_lines(self, line_list):
        """
        Removes triplicate blank lines from changelog to prevent it from getting too long
        """
        i = 2
        while i < len(line_list):
            here = line_list[i]
            minus_1 = line_list[i - 1]
            minus_2 = line_list[i - 2]
            if here == minus_1 == minus_2 == "\n":
                line_list.pop(i)
            elif minus_2 == '---\n' and here == minus_1 == '\n':
                line_list.pop(i)
            else:
                i += 1
        return line_list

    def bump_version(self, version, release_type):
        """
        Bumps a version number based on release_type
        """
        x, y, z = version.split(".")
        if release_type == "major":
            x = int(x) + 1
            y = z = 0
        elif release_type == "minor":
            y = int(y) + 1
            z = 0
        else:
            z = int(z) + 1
        return "{}.{}.{}".format(x, y, z)

    def match_version(self, line):
        """
        Matches a line vs the list of version strings.
        Returns matched groups dictionary or None.
        """
        for regex in RELEASE_LINE_REGEXES:
            match = re.match(regex, line)
            if match:
                return Version(match.group('version'))
