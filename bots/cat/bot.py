from github import Repository

from bots import bot

class CatBot(bot.GitAutomatorBot):
    def handle_action(self, _: str):
        comment_lines = self.webhook_body['comment']['body']
        for i in comment_lines.splitlines():
            if not i.startswith('/cat'):
                continue

            body = "GitAutomator works for your repository.\n"
            body += "![funny-cat](https://i.imgur.com/G2iPfel.jpg)"
            issue = self.repo_client.get_issue(self.webhook_body['issue']['number'])
            issue.create_comment(body=body)
            return

    @property
    def name(self) -> str:
        return 'cat'

def new_gitautomator_bot(repo_client: Repository.Repository, json_body: dict, token: str) -> bot.GitAutomatorBot:
    return CatBot(repo_client, json_body, token)
