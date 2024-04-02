from github import Repository

from bots import bot

class PRReactorBot(bot.GitAutomatorBot):
    @property
    def name(self) -> str:
        return 'prreact'

    def handle_action(self, _: str):
        issue = self.repo_client.get_issue(self.webhook_body['pull_request']['number'])
        issue.create_reaction('heart')

def new_gitautomator_bot(repo_client: Repository.Repository, json_body: dict, token: str) -> bot.GitAutomatorBot:
    return PRReactorBot(repo_client, json_body, token)
