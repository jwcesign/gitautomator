import unittest
from unittest import mock

from bots.utils.helper import ConfigurationError, get_enable_plugin


class EnablePluginTest(unittest.TestCase):
    def test_missing_or_empty_plugins(self):
        repo_client = mock.Mock()

        for content in (b"owners:\n- example-user\n", b"plugins:\n"):
            with self.subTest(content=content):
                repo_client.get_contents.return_value.decoded_content = content
                self.assertEqual(get_enable_plugin(repo_client), [])

    def test_rejects_invalid_plugins(self):
        repo_client = mock.Mock()

        for content in (b"plugins: cat\n", b"plugins: false\n"):
            with self.subTest(content=content):
                repo_client.get_contents.return_value.decoded_content = content
                with self.assertRaises(ConfigurationError):
                    get_enable_plugin(repo_client)


if __name__ == "__main__":
    unittest.main()
