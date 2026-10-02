import unittest
from unittest import mock

from app import ERROR_COMMENT_MARKER, GitHubRepoAction


class GitHubRepoActionErrorReportingTest(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "action": "opened",
            "issue": {"number": 42},
        }
        self.action = GitHubRepoAction(self.payload)
        self.action.repo_client = mock.Mock()
        self.action.token = "installation-token"

    def test_reports_safe_error(self):
        failing_bot = mock.Mock()
        failing_bot.name = "broken"
        failing_bot.handle_action.side_effect = RuntimeError(
            "token installation-token for @maintainer at "
            "https://oauth2:secret@example.com using ghp_example"
        )
        healthy_bot = mock.Mock()
        healthy_bot.name = "healthy"

        self.action.action_handler = {
            "issue": {
                "opened": [
                    mock.Mock(return_value=failing_bot),
                    mock.Mock(return_value=healthy_bot),
                ]
            }
        }

        with mock.patch.object(
            self.action,
            "_GitHubRepoAction__init_repo_client",
        ), mock.patch.object(
            self.action,
            "_GitHubRepoAction__get_enable_plugins",
            return_value=[],
        ), self.assertLogs("app", level="ERROR"):
            self.action.handle_action()

        issue = self.action.repo_client.get_issue.return_value
        issue.create_comment.assert_called_once()
        body = issue.create_comment.call_args.kwargs["body"]
        self.assertIn("GitAutomator `broken` failed", body)
        self.assertIn("An unexpected internal error occurred", body)
        self.assertIn(ERROR_COMMENT_MARKER, body)
        self.assertRegex(body, r"\*\*Reference:\*\* `[0-9a-f]{32}`")
        self.assertNotIn("installation-token", body)
        self.assertNotIn("oauth2:secret", body)
        self.assertNotIn("ghp_example", body)
        self.assertNotIn("@maintainer", body)
        healthy_bot.handle_action.assert_called_once_with("issue")

    def test_no_target_skips_comment(self):
        action = GitHubRepoAction({"action": "opened"})
        action.repo_client = mock.Mock()
        action.token = "token"
        action.type = "issue"
        failing_bot = mock.Mock()
        failing_bot.name = "broken"
        failing_bot.handle_action.side_effect = RuntimeError("failure")
        action.action_handler = {
            "issue": {"opened": [mock.Mock(return_value=failing_bot)]}
        }

        with mock.patch.object(
            action,
            "_GitHubRepoAction__init_repo_client",
        ), mock.patch.object(
            action,
            "_GitHubRepoAction__get_enable_plugins",
            return_value=[],
        ), self.assertLogs("app", level="ERROR"):
            action.handle_action()

        action.repo_client.get_issue.assert_not_called()

    def test_reports_config_error(self):
        bot_factory = mock.Mock()
        self.action.action_handler = {
            "issue": {"opened": [bot_factory]}
        }

        with mock.patch.object(
            self.action,
            "_GitHubRepoAction__init_repo_client",
        ), mock.patch.object(
            self.action,
            "_GitHubRepoAction__get_enable_plugins",
            side_effect=ValueError("invalid plugin configuration"),
        ), self.assertLogs("app", level="ERROR"):
            self.action.handle_action()

        issue = self.action.repo_client.get_issue.return_value
        body = issue.create_comment.call_args.kwargs["body"]
        self.assertIn("GitAutomator `dispatcher` failed", body)
        self.assertNotIn("invalid plugin configuration", body)
        bot_factory.assert_not_called()

    def test_ignores_error_comment(self):
        payload = {
            "action": "created",
            "comment": {
                "body": ERROR_COMMENT_MARKER,
                "html_url": "https://example.test/org/repo/issues/42#comment",
            },
            "issue": {"number": 42},
        }
        action = GitHubRepoAction(payload)

        with mock.patch.object(
            action,
            "_GitHubRepoAction__init_repo_client",
        ) as init_repo_client:
            action.handle_action()

        init_repo_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
