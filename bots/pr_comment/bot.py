from github import Repository

from bots import bot

class PRCommentBot(bot.GitAutomatorBot):
    def handle_action(self, _: str):
        pull = self.repo_client.get_pull(self.webhook_body['pull_request']['number'])
        body = "Thanks to your contribution, the maintainers will review it as soon as they can!"
        pull.create_issue_comment(body=body)

    @property
    def name(self) -> str:
        return 'prcomment'

def new_gitautomator_bot(repo_client: Repository.Repository, json_body: dict, token: str) -> bot.GitAutomatorBot:
    return PRCommentBot(repo_client, json_body, token)
