import random

from github import Repository

from bots import bot
from bots.utils import helper

class PRReviewRequestBot(bot.GitAutomatorBot):
    def handle_action(self, _: str):
        maintainers = helper.get_owners(self.repo_client)
        pr_creator = self.webhook_body['sender']['login']
        if pr_creator in maintainers:
            maintainers.remove(pr_creator)

        if len(maintainers) == 0:
            return
        if len(maintainers) > 2:
            maintainers = random.sample(maintainers, 2)
        pull_request = self.repo_client.get_pull(self.webhook_body['pull_request']['number'])
        pull_request.create_review_request(reviewers=maintainers)

    @property
    def name(self) -> str:
        return 'prreviewrequest'

def new_gitautomator_bot(repo_client: Repository.Repository, json_body: dict, token: str) -> bot.GitAutomatorBot:
    return PRReviewRequestBot(repo_client, json_body, token)
