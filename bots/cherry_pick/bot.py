import shutil
import os
import random

from git import Repo
from github import Repository

from bots import bot

class CherryPickBot(bot.GitAutomatorBot):
    def __clone_repo(self, source_branch: str, cherry_pick_branch: str, path: str):
        owner = self.webhook_body['repository']['owner']['login']
        repo_name = self.webhook_body['repository']['name']
        repo_url = f'https://oauth2:{self.token}@github.com/{owner}/{repo_name}.git'
        repo = Repo.clone_from(repo_url, path)
        repo.git.checkout(source_branch)

        # In order to have a clean branch
        if cherry_pick_branch in [str(b) for b in repo.heads]:
            repo.delete_head(cherry_pick_branch)
        repo.create_head(cherry_pick_branch)
        repo.git.checkout(cherry_pick_branch)

        # Set commit user
        with repo.config_writer() as git_config:
            git_config.set_value("user", "name", "gitautomator[bot]")
            git_config.set_value("user", "email", "161270032+gitautomator[bot]@users.noreply.github.com")

        return repo

    def __handle_cherry_pick_start(self):
        comment_lines = self.webhook_body['comment']['body']
        for i in comment_lines.splitlines():
            if not i.startswith('/cherry-pick'):
                continue

            pull_number = self.webhook_body['issue']['number']
            pull_request = self.repo_client.get_pull(pull_number)
            if not pull_request.merged:
                pull_request.create_issue_comment("Cannot cherry-pick an unmerged PR.")
                return

            target_branch = i.removeprefix('/cherry-pick ').strip()
            cherry_pick_branch = 'cherry-pick-' + str(pull_number) + "-" + target_branch

            path = ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba', 5))
            path = '/tmp/'+path
            try:
                git_repo = self.__clone_repo(target_branch, cherry_pick_branch, path)

                commits = [commit.sha for commit in pull_request.get_commits()]

                try:
                    for commit in commits:
                        git_repo.git.cherry_pick(commit)
                except Exception as err:
                    pull_request.create_issue_comment("This PR cannot be cherry-picked due to potential conflicts. Please handle it manually.")
                    raise err

                git_repo.git.push("origin", cherry_pick_branch, '-f')

                body = f'Cherry pick of #{pull_request.number} on branch {target_branch}'
                self.repo_client.create_pull(title=f'Cherry pick PR({pull_request.number})/{pull_request.title}', body=body, head=cherry_pick_branch, base=target_branch)
            except Exception as err:
                if os.path.exists(path):
                    shutil.rmtree(path)
                raise err

    def __handle_cherry_pick_end(self):
        pull_number = self.webhook_body['pull_request']['number']
        pull_request = self.repo_client.get_pull(pull_number)
        source_branch = self.repo_client.get_git_ref("heads/" + pull_request.head.ref)
        if pull_request.head.ref.startswith('cherry-pick-'):
            source_branch.delete()

    def handle_action(self, _: str):
        if self.webhook_body['action'] == 'closed':
            self.__handle_cherry_pick_end()
            return
        self.__handle_cherry_pick_start()

    @property
    def name(self) -> str:
        return 'cherrypick'

def new_gitautomator_bot(repo_client: Repository.Repository, json_body: dict, token: str) -> bot.GitAutomatorBot:
    return CherryPickBot(repo_client, json_body, token)
