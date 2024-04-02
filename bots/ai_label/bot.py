from github import GithubException,Repository

from bots import bot
from bots.utils import ai_robot


class AILabelBot(bot.GitAutomatorBot):
    def __handle_pr(self):
        labels = self.repo_client.get_labels()
        label_dict = [{'name': label.name, 'color': label.color, 'description': label.description } for label in labels]
        pull_request = self.repo_client.get_pull(self.webhook_body['pull_request']['number'])
        context = f"('pull_request': '{pull_request.title}', 'pull_request_body': '{pull_request.body}')"
        gpt = ai_robot.AIAssistant()
        labels = gpt.get_label(context, label_dict)
        if len(labels) <= 0:
            return

        for label in labels:
            if any(i not in label.keys() for i in ['name', 'color', 'description']):
                continue
            type_label = None
            try:
                type_label = self.repo_client.get_label(label['name'])
            except GithubException as err:
                if err.status != 404:
                    continue
                type_label = self.repo_client.create_label(label['name'], label['color'], label['description'])
            for exist_label in pull_request.get_labels():
                if exist_label.name == label['name']:
                    continue
            pull_request.add_to_labels(type_label)

    def __handle_issue(self):
        labels = self.repo_client.get_labels()
        label_dict = [{'name': label.name, 'color': label.color, 'description': label.description } for label in labels]
        issue = self.repo_client.get_issue(self.webhook_body['issue']['number'])
        context = f"('issue_title': '{issue.title}', 'issue_body': '{issue.body}')"
        gpt = ai_robot.AIAssistant()
        labels = gpt.get_label(context, label_dict)
        if len(labels) <= 0:
            return

        for label in labels:
            if any(i not in label.keys() for i in ['name', 'color', 'description']):
                continue
            type_label = None
            try:
                type_label = self.repo_client.get_label(label['name'])
            except GithubException as err:
                if err.status != 404:
                    continue
                type_label = self.repo_client.create_label(label['name'], label['color'], label['description'])
            for exist_label in issue.get_labels():
                if exist_label.name == label['name']:
                    continue
            issue.add_to_labels(type_label)

    def handle_action(self, event_type: str):
        if event_type == 'issue':
            self.__handle_issue()
        if event_type == 'pull_request':
            self.__handle_pr()

    @property
    def name(self) -> str:
        return 'ailabel'

def new_gitautomator_bot(repo_client: Repository.Repository, json_body: dict, token: str) -> bot.GitAutomatorBot:
    return AILabelBot(repo_client, json_body, token)
