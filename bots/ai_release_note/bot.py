from github import Repository

from bots import bot
from bots.utils import ai_robot


class AIReleaseNoteBot(bot.GitAutomatorBot):
    def handle_action(self, _: str):
        pull_request = self.repo_client.get_pull(self.webhook_body['pull_request']['number'])
        context = f"('pull_request': '{pull_request.title}', 'pull_request_body': '{pull_request.body}')"
        gpt = ai_robot.AIAssistant()
        release_note = gpt.check_release_note(context)
        if release_note.lower() == 'ok':
            return
        pull_request.create_issue_comment(body=release_note)

    @property
    def name(self) -> str:
        return 'aireleasenote'

def new_gitautomator_bot(repo_client: Repository.Repository, json_body: dict, token: str) -> bot.GitAutomatorBot:
    return AIReleaseNoteBot(repo_client, json_body, token)
