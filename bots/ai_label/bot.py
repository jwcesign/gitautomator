from github import Repository

from bots import bot
from bots.utils import ai_robot


class AILabelBot(bot.GitAutomatorBot):
    def __add_labels(self, target, context: dict):
        available_labels = list(self.repo_client.get_labels())
        label_details = [
            {
                'name': label.name,
                'color': label.color,
                'description': label.description,
            }
            for label in available_labels
        ]
        selected_names = ai_robot.AIAssistant().get_label(context, label_details)
        selected_labels = {
            label.name: label
            for label in available_labels
            if label.name in selected_names
        }
        existing_names = {label.name for label in target.get_labels()}

        for label_name in selected_names:
            if label_name not in existing_names and label_name in selected_labels:
                target.add_to_labels(selected_labels[label_name])

    def __handle_pr(self):
        pull_request = self.repo_client.get_pull(self.webhook_body['pull_request']['number'])
        context = {
            'pull_request_title': pull_request.title,
            'pull_request_body': pull_request.body,
        }
        self.__add_labels(pull_request, context)

    def __handle_issue(self):
        issue = self.repo_client.get_issue(self.webhook_body['issue']['number'])
        context = {
            'issue_title': issue.title,
            'issue_body': issue.body,
        }
        self.__add_labels(issue, context)

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
