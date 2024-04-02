from github import Repository

from bots import bot

class PRLabelBot(bot.GitAutomatorBot):
    def handle_action(self, _: str):
        pull = self.repo_client.get_pull(self.webhook_body['pull_request']['number'])
        if pull.title.startswith('fix'):
            bug_label = self.repo_client.get_label('bug')
            if bug_label is not None:
                pull.add_to_labels(bug_label)
        if pull.title.startswith('doc'):
            doc_label = self.repo_client.get_label('documentation')
            if doc_label is not None:
                pull.add_to_labels(doc_label)
        if pull.title.startswith('feat'):
            en_label = self.repo_client.get_label('enhancement')
            if en_label is not None:
                pull.add_to_labels(en_label)

    @property
    def name(self) -> str:
        return 'prlabel'

def new_gitautomator_bot(repo_client: Repository.Repository, json_body: dict, token: str) -> bot.GitAutomatorBot:
    return PRLabelBot(repo_client, json_body, token)
