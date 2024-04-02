from github import Repository

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
                if '[bot]' not in pull.user.login:
                    pull.create_review(event="APPROVE")
                pull.merge()

    @property
    def name(self) -> str:
        return 'approve'

def new_gitautomator_bot(repo_client: Repository.Repository, json_body: dict, token: str) -> bot.GitAutomatorBot:
    return ApproveBot(repo_client, json_body, token)
