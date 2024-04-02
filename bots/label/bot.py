from github import GithubException,Repository

from bots import bot


class LabelBot(bot.GitAutomatorBot):
    def handle_action(self, _: str):
        comment_lines = self.webhook_body['comment']['body']
        issue = self.repo_client.get_issue(self.webhook_body['issue']['number'])
        unknown_labels = []
        for i in comment_lines.splitlines():
            if not i.startswith('/label '):
                continue
            label = i.removeprefix('/label ')
            type_label = None
            try:
                type_label = self.repo_client.get_label(label)
            except GithubException as err:
                if err.status != 404:
                    return
                unknown_labels.append(label)
                continue
            if type_label is not None:
                issue.add_to_labels(type_label)

        if len(unknown_labels) > 0:
            resp = []
            for i in unknown_labels:
                resp.append("`" + i + "`")
            unknown_labels = ','.join(resp)
            body = f'Unknown labels: {unknown_labels}, please add them for this repository.'
            issue.create_comment(body)

    @property
    def name(self) -> str:
        return 'label'

def new_gitautomator_bot(repo_client: Repository.Repository, json_body: dict, token: str) -> bot.GitAutomatorBot:
    return LabelBot(repo_client, json_body, token)
