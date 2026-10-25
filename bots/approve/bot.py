from github import GithubException, Repository

from bots import bot
from bots.utils import helper

class ApproveBot(bot.GitAutomatorBot):
    def handle_action(self, _: str):
        comment_lines = self.webhook_body['comment']['body']
        for i in comment_lines.splitlines():
            if not i.startswith('/approve'):
                continue

            pull = self.repo_client.get_pull(self.webhook_body['issue']['number'])
            maintainers = helper.get_owners(self.repo_client)
            if len(maintainers) == 0:
                pull.create_issue_comment("Unable to retrieve the maintainers' list. \
                                          Please verify the `.github/gitautomator.yaml` configuration.")
                return
            if self.webhook_body['sender']['login'] in maintainers:
                try:
                    pull.create_review(event="APPROVE")
                except GithubException as error:
                    message = error.data.get("message") if isinstance(error.data, dict) else None
                    # Let GitHub identify self-reviews for the authenticated app.
                    # Every other review failure must still stop the merge.
                    if (
                        error.status != 422
                        or not isinstance(message, str)
                        or message.casefold().strip().rstrip(".") not in {
                            "can not approve your own pull request",
                            "cannot approve your own pull request",
                        }
                    ):
                        raise

                merge_methods = (
                    ('merge', 'allow_merge_commit'),
                    ('squash', 'allow_squash_merge'),
                    ('rebase', 'allow_rebase_merge'),
                )
                for merge_method, setting in merge_methods:
                    if getattr(self.repo_client, setting, False):
                        pull.merge(merge_method=merge_method)
                        return

                pull.create_issue_comment("No pull request merge method is enabled for this repository.")

    @property
    def name(self) -> str:
        return 'approve'

def new_gitautomator_bot(repo_client: Repository.Repository, json_body: dict, token: str) -> bot.GitAutomatorBot:
    return ApproveBot(repo_client, json_body, token)
