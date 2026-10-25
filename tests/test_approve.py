import unittest
from unittest import mock

from github import GithubException

from bots.approve.bot import ApproveBot


class ApproveBotTest(unittest.TestCase):
    def setUp(self):
        self.repo = mock.Mock()
        self.repo.allow_merge_commit = True
        self.repo.allow_squash_merge = False
        self.repo.allow_rebase_merge = False
        self.pull = self.repo.get_pull.return_value
        self.payload = {
            "comment": {"body": "/approve"},
            "issue": {"number": 42},
            "sender": {"login": "example-maintainer"},
        }
        self.bot = ApproveBot(self.repo, self.payload, "illustrative-token")
        owners = mock.patch(
            "bots.approve.bot.helper.get_owners", return_value=["example-maintainer"]
        )
        owners.start()
        self.addCleanup(owners.stop)

    def test_approves_human_and_other_bot_authors_before_merging(self):
        for author in ("example-contributor", "dependabot[bot]", "renovate[bot]"):
            with self.subTest(author=author):
                self.pull.reset_mock()
                self.pull.user.login = author
                self.bot.handle_action("pull_request")
                self.assertEqual(
                    self.pull.mock_calls,
                    [
                        mock.call.create_review(event="APPROVE"),
                        mock.call.merge(merge_method="merge"),
                    ],
                )

    def test_only_self_review_rejection_allows_merge_without_new_review(self):
        self.pull.user.login = "example-configured-app[bot]"
        for message in (
            "Can not approve your own pull request",
            "Cannot approve your own pull request.",
        ):
            with self.subTest(message=message):
                self.pull.reset_mock()
                self.pull.create_review.side_effect = GithubException(422, {"message": message})
                self.bot.handle_action("pull_request")
                self.pull.create_review.assert_called_once_with(event="APPROVE")
                self.pull.merge.assert_called_once_with(merge_method="merge")

    def test_other_review_errors_stop_the_merge(self):
        for status, data in (
            (403, {"message": "Resource not accessible by integration"}),
            (422, {"message": "Validation Failed"}),
            (422, {"message": {"token": "illustrative-secret"}}),
            (422, None),
            (403, {"message": "Can not approve your own pull request"}),
        ):
            with self.subTest(status=status, data=data):
                self.pull.reset_mock()
                error = GithubException(status, data)
                self.pull.create_review.side_effect = error
                with self.assertRaises(GithubException) as raised:
                    self.bot.handle_action("pull_request")
                self.assertIs(raised.exception, error)
                self.pull.merge.assert_not_called()

    def test_non_maintainer_cannot_approve_or_merge(self):
        self.payload["sender"]["login"] = "example-untrusted-user"
        self.bot.handle_action("pull_request")
        self.pull.create_review.assert_not_called()
        self.pull.merge.assert_not_called()


if __name__ == "__main__":
    unittest.main()
