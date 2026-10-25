import unittest
from unittest import mock

from github import GithubException

from app import ERROR_COMMENT_MARKER, GitHubRepoAction, _public_error_message


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

    def test_reports_github_approval_reason_without_response_data(self):
        failing_bot = mock.Mock()
        failing_bot.name = "approve"
        failing_bot.handle_action.side_effect = GithubException(
            405,
            {
                "message": (
                    "New changes require approval from someone other than "
                    "example-contributor because they were the last pusher. "
                    "token=illustrative-secret"
                ),
                "documentation_url": "https://example.test/?token=illustrative-secret",
                "errors": [{"message": "illustrative-private-response"}],
            },
            {"Authorization": "Bearer illustrative-secret"},
        )
        self.action.action_handler = {
            "issue": {"opened": [mock.Mock(return_value=failing_bot)]}
        }

        with mock.patch.object(
            self.action, "_GitHubRepoAction__init_repo_client"
        ), mock.patch.object(
            self.action, "_GitHubRepoAction__get_enable_plugins", return_value=[]
        ), self.assertLogs("app", level="ERROR"):
            self.action.handle_action()

        body = self.action.repo_client.get_issue.return_value.create_comment.call_args.kwargs["body"]
        self.assertIn("HTTP 405", body)
        self.assertIn(
            "New changes require approval from someone other than the last pusher.",
            body,
        )
        for private_detail in (
            "example-contributor", "illustrative-secret", "illustrative-private-response",
            "Authorization", "example.test", "Traceback",
        ):
            self.assertNotIn(private_detail, body)
        self.assertIn(ERROR_COMMENT_MARKER, body)
        self.assertRegex(body, r"\*\*Reference:\*\* `[0-9a-f]{32}`")

    def test_known_github_reasons_use_public_templates(self):
        cases = (
            (403, "Resource not accessible by integration", "does not have permission"),
            (401, "Bad credentials", "rejected the app credentials"),
            (403, "API rate limit exceeded", "rate limited the request"),
            (405, "At least one approving review is required", "required approving reviews"),
            (405, 'Required status check "illustrative-private-check" is expected', "required status checks"),
            (405, "Pull Request is not mergeable", "cannot be merged in its current state"),
            (422, "Validation Failed", "rejected the request as invalid"),
        )
        for status, message, reason in cases:
            with self.subTest(status=status, message=message):
                public_message = _public_error_message(GithubException(status, {"message": message}))
                self.assertIn(f"HTTP {status}", public_message)
                self.assertIn(reason, public_message)
                self.assertNotIn("illustrative-private-check", public_message)

    def test_unknown_github_response_data_stays_private(self):
        for data in (
            {"message": "Bearer illustrative-secret at https://example.test/private"},
            {"message": {"token": "illustrative-secret"}},
            "illustrative-secret",
            None,
        ):
            with self.subTest(data=data):
                public_message = _public_error_message(GithubException(500, data))
                self.assertIn("HTTP 500", public_message)
                self.assertIn("reference ID", public_message)
                self.assertNotIn("illustrative-secret", public_message)
                self.assertNotIn("example.test", public_message)

    def test_invalid_github_status_stays_private(self):
        for status in ("illustrative-secret", None, 999):
            with self.subTest(status=status):
                public_message = _public_error_message(GithubException(status, {}))
                self.assertNotIn("HTTP", public_message)
                self.assertNotIn("illustrative-secret", public_message)

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
