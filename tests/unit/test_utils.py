import unittest
import os
from datetime import date

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from packaging.version import Version

from changelog.utils import ChangelogUtils
from changelog.exceptions import ChangelogDoesNotExistError


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.cl = ChangelogUtils()

    def test_bump_version_major(self):
        self.assertEqual(self.cl.bump_version('0.1.0', 'major'), '1.0.0')

    def test_bump_version_minor(self):
        self.assertEqual(self.cl.bump_version('0.1.0', 'minor'), '0.2.0')

    def test_bump_version_patch(self):
        self.assertEqual(self.cl.bump_version('0.1.0', 'patch'), '0.1.1')

    def test_crunch_lines(self):
        document = [
            "this\n",
            "\n",
            "\n",
            "\n",
            "\n",
            "that\n"
        ]
        self.assertEqual(self.cl.crunch_lines(document), ['this\n', '\n', '\n', 'that\n'])

    def test_crunch_lines_release(self):
        document = [
            "this\n",
            "---\n",
            "\n",
            "\n",
            "\n",
            "that\n"
        ]
        self.assertEqual(self.cl.crunch_lines(document), ['this\n', '---\n', '\n', 'that\n'])

    def test_get_release_suggestion_patch(self):
        with patch.object(ChangelogUtils, 'get_changes', return_value={'changes': ''}):
            CL = ChangelogUtils()
            result = CL.get_release_suggestion()
            self.assertEqual(result, 'patch')

    def test_get_release_suggestion_minor(self):
        with patch.object(ChangelogUtils, 'get_changes', return_value={'new': 'stuff'}):
            CL = ChangelogUtils()
            result = CL.get_release_suggestion()
            self.assertEqual(result, 'minor')

    def test_get_release_suggestion_major(self):
        with patch.object(ChangelogUtils, 'get_changes', return_value={'break': 'stuff'}):
            CL = ChangelogUtils()
            result = CL.get_release_suggestion()
            self.assertEqual(result, 'major')

    def test_update_section(self):
        with patch.object(ChangelogUtils, 'write_changelog') as mock_write:
            sample_data = [
                "## Unreleased\n",
                "---\n",
                "\n",
                "### New\n",
                "\n",
                "### Fixes\n",
                "\n",
                "### Breaks\n",
            ]
            with patch.object(ChangelogUtils, 'get_changelog_data', return_value=sample_data) as mock_read:
                CL = ChangelogUtils()
                CL.update_section("new", 'this is a test')
        mock_write.assert_called_once_with([
            "## Unreleased\n",
            "---\n",
            "\n",
            "### New\n",
            "* this is a test\n",
            "\n",
            "### Fixes\n",
            "\n",
            "### Breaks\n",
        ])

    def test_get_current_version(self):
        sample_data = [
            "## Unreleased\n",
            "---\n",
            "\n",
            "### New\n",
            "\n",
            "### Fixes\n",
            "\n",
            "### Breaks\n",
            "\n",
            "\n",
            "## 0.3.2 - (2017-06-09)\n",
            "---\n",
        ]
        with patch.object(ChangelogUtils, 'get_changelog_data', return_value=sample_data) as mock_read:
            CL = ChangelogUtils()
            result = CL.get_current_version()
        self.assertEqual(result, Version('0.3.2'))

    def test_get_current_version_default(self):
        sample_data = []
        with patch.object(ChangelogUtils, 'get_changelog_data', return_value=sample_data) as mock_read:
            CL = ChangelogUtils()
            result = CL.get_current_version()
        self.assertEqual(result, Version('0.0.0'))

    def test_get_changes(self):
        sample_data = [
            "## Unreleased\n",
            "---\n",
            "\n",
            "### New\n",
            "* added feature x\n",
            "\n",
            "### Fixes\n",
            "* fixed bug 1\n",
            "\n",
            "### Breaks\n",
            "\n",
            "\n",
            "## 0.3.2 - (2017-06-09)\n",
            "---\n",
        ]
        with patch.object(ChangelogUtils, 'get_changelog_data', return_value=sample_data) as mock_read:
            CL = ChangelogUtils()
            result = CL.get_changes()
        self.assertTrue('new' in result)
        self.assertTrue('fix' in result)

    def test_get_new_release_version_patch(self):
        CL = ChangelogUtils()  # Store a copy of original before patching
        test_data = {
            Version('0.0.0+user.1.1.1'): [
                ('major', '1.0.0'),
                ('minor', '0.1.0'),
                ('patch', '0.0.1'),
            ],
            Version('1.1.1'): [
                ('patch', '1.1.2'),
                ('minor', '1.2.0'),
                ('major', '2.0.0'),
            ]
        }
        for version, action_expected in test_data.items():
            with patch.object(ChangelogUtils, 'get_current_version', return_value=version):
                for action, expected in action_expected:
                    self.assertEqual(CL.get_new_release_version(action), expected)

    def test_get_new_release_version_suggest(self):
        CL = ChangelogUtils()  # Store a copy of original before patching
        test_data = {
            Version('0.0.0+user.1.1.1'): [
                ('patch', '0.0.0+user.1.1.2', {'local': 'user.'}),
                ('minor', '0.0.0+user.1.2.0', {'local': 'user.'}),
                ('major', '0.0.0+user.2.0.0', {'local': 'user.'}),
            ],
            Version('1.1.1'): [
                ('patch', '1.1.2', {}),
                ('minor', '1.2.0', {}),
                ('major', '2.0.0', {}),
            ]
        }
        for version, suggestion_expected_kwargs in test_data.items():
            with patch.object(ChangelogUtils, 'get_current_version', return_value=version):
                for suggestion, expected, kwargs in suggestion_expected_kwargs:
                    with patch.object(ChangelogUtils, 'get_release_suggestion', return_value=suggestion):
                        self.assertEqual(
                            CL.get_new_release_version('suggest', **kwargs),
                            expected,
                        )

    def test_get_new_local_release_version(self):
        CL = ChangelogUtils()  # Store a copy of original before patching
        test_data = {
            # standard, typical, normal states
            Version('0.0.0+user.1.1.1'): [
                ('patch', '0.0.0+user.1.1.2'),
                ('minor', '0.0.0+user.1.2.0'),
                ('major', '0.0.0+user.2.0.0'),
            ],
            # no previous local label in version
            Version('0.0.0'): [
                ('major', '0.0.0+user.1.0.0'),
                ('minor', '0.0.0+user.0.1.0'),
                ('patch', '0.0.0+user.0.0.1'),
            ],
            # MIS-MATCHED previous local label in version
            Version('0.0.0+git77afcfd34'): [
                ('major', '0.0.0+user.1.0.0'),
                ('minor', '0.0.0+user.0.1.0'),
                ('patch', '0.0.0+user.0.0.1'),
            ],
            # MALFORMED previous local label in version
            Version('0.0.0+user.FOOBAR'): [
                ('major', '0.0.0+user.1.0.0'),
                ('minor', '0.0.0+user.0.1.0'),
                ('patch', '0.0.0+user.0.0.1'),
            ],
        }
        for version, rtype_expected, in test_data.items():
            with patch.object(ChangelogUtils, 'get_current_version', return_value=version):
                for rtype, expected in rtype_expected:
                    self.assertEqual(
                        CL.get_new_release_version(rtype, local='user.'),
                        expected
                    )


class ChangelogFileOperationTestCase(unittest.TestCase):
    def setUp(self):
        self.CL = ChangelogUtils()
        self.CL.CHANGELOG = 'TEST_CHANGELOG.md'

    def test_initialize_changelog_file(self):
        self.CL.initialize_changelog_file()
        self.assertTrue(os.path.isfile('TEST_CHANGELOG.md'))

    def test_initialize_changelog_file_exists(self):
        self.CL.initialize_changelog_file()
        self.assertTrue(os.path.isfile('TEST_CHANGELOG.md'))
        message = self.CL.initialize_changelog_file()
        self.assertEqual(message, 'TEST_CHANGELOG.md already exists')

    def test_get_changelog_data(self):
        self.CL.initialize_changelog_file()
        data = self.CL.get_changelog_data()
        self.assertTrue(len(data) > 1)

    def test_get_changelog_no_file(self):
        self.assertRaises(ChangelogDoesNotExistError, self.CL.get_changelog_data)

    def test_write_changelog(self):
        self.CL.initialize_changelog_file()
        original = self.CL.get_changelog_data()
        data = original + ["test\n"]
        self.CL.write_changelog(data)
        modified = self.CL.get_changelog_data()
        self.assertEqual(len(original) + 1, len(modified))

    def test_cut_release(self):
        self.CL.initialize_changelog_file()
        self.CL.update_section('new', "this is a test")
        self.CL.cut_release('suggest')
        data = self.CL.get_changelog_data()
        self.assertTrue('## Unreleased\n' in data)
        self.assertTrue('## 0.1.0 - ({})\n'.format(date.today().isoformat()) in data)
        self.CL.update_section('break', "removed a thing")
        self.CL.cut_release('suggest')
        data2 = self.CL.get_changelog_data()
        self.assertTrue('## Unreleased\n' in data2)

    def test_match_version_canonical(self):
        line = "## 0.2.1 - (2017-06-09)"
        self.assertEqual(self.CL.match_version(line), Version('0.2.1'))

    def test_match_version_miss(self):
        line = '### Changes'
        self.assertFalse(self.CL.match_version(line))

    def test_match_version_basic(self):
        line = '## v4.1.3'
        self.assertEqual(self.CL.match_version(line), Version('4.1.3'))

    def test_match_keep_a_changelog(self):
        line = '## [4.1.3] - 2017-06-20'
        self.assertEqual(self.CL.match_version(line), Version('4.1.3'))

    def tearDown(self):
        try:
            os.remove('TEST_CHANGELOG.md')
        except Exception:
            pass
