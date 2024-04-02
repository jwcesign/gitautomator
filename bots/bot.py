import abc

from github import Repository

class GitAutomatorBot(metaclass=abc.ABCMeta):
    repo_client = None
    webhook_body = None
    token = None

    def __init__(self, repo_client: Repository.Repository, json_body: dict, token: str):
        self.webhook_body = json_body
        self.repo_client = repo_client
        self.token = token

    @abc.abstractmethod
    def handle_action(self, event_type: str):
        pass

    @abc.abstractproperty
    def name(self):
        pass
