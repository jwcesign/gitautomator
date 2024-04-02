import os

from flask import Flask, request
from github import Github,GithubIntegration,Repository

import bots.pr_react.bot as prreact
import bots.pr_label.bot as prlabel
import bots.pr_comment.bot as prcomment
import bots.label.bot as label
import bots.approve.bot as approve
import bots.cherry_pick.bot as cherrypick
import bots.pr_review_request.bot as prreviewrequest
import bots.cat.bot as cat
import bots.ai_label.bot as ailabel
import bots.ai_release_note.bot as aireleasenote
import bots.utils.helper as bothelper

app = Flask(__name__)

# PR: comment(add), open
# Issue: comment(add), open
class GitHubRepoAction:
    type = ""
    action = ""
    json_body = ""
    repo_client: Repository.Repository = None
    token = ""
    action_handler = {
        'pull_request': {
            'comment': {
                label.new_gitautomator_bot,
                approve.new_gitautomator_bot,
                cherrypick.new_gitautomator_bot,
                cat.new_gitautomator_bot,
            },
            'opened': {
                prreact.new_gitautomator_bot,
                prlabel.new_gitautomator_bot,
                prcomment.new_gitautomator_bot,
                prreviewrequest.new_gitautomator_bot,
                ailabel.new_gitautomator_bot,
                aireleasenote.new_gitautomator_bot,
            },
            "merged": {
                cherrypick.new_gitautomator_bot
            }
        },
        'issue': {
            'comment': {
                label.new_gitautomator_bot,
                cat.new_gitautomator_bot,
            },
            'opened': {
                ailabel.new_gitautomator_bot,
            }
        }
    }

    def __init__(self, payload):
        self.json_body = payload
        keys = payload.keys()
        if 'action' not in keys:
            return

        if payload['action'] == "created" and 'comment' in keys:
            self.action = 'comment'
            url = payload['comment']['html_url']
            self.type = 'issue'
            if '/pull/' in url:
                self.type = "pull_request"
            return

        if 'pull_request' in keys and payload['action'] == 'closed':
            if payload['pull_request']['merged_at'] is not None:
                self.action = 'merged'
                self.type = "pull_request"
                return

        if 'pull_request' in keys:
            self.type = "pull_request"
        elif 'issue' in keys:
            self.type = 'issue'
        self.action = payload['action']

    def handle_action(self):
        if self.type not in self.action_handler.keys():
            return
        if self.action not in self.action_handler[self.type].keys():
            return

        self.__init_repo_client()
        enable_plugins = self.__get_enable_plugins()
        for bot_func in self.action_handler[self.type][self.action]:
            bot = bot_func(self.repo_client, self.json_body, self.token)
            if len(enable_plugins) > 0 and bot.name not in enable_plugins:
                continue
            bot.handle_action(self.type)

    def __init_repo_client(self) -> str:
        app_id = os.getenv('APP_ID')
        app_key = None
        with open('/etc/gitautomator/app.pem', 'r', encoding='utf-8') as app_cer_file:
            app_key = app_cer_file.read()

        git_integration = GithubIntegration(app_id, app_key)
        owner = self.json_body['repository']['owner']['login']
        repo_name = self.json_body['repository']['name']
        self.token = git_integration.get_access_token(
                git_integration.get_repo_installation(owner, repo_name).id
            ).token
        git_connection = Github(self.token)
        self.repo_client = git_connection.get_repo(f"{owner}/{repo_name}")

    def __get_enable_plugins(self) -> list:
        return bothelper.get_enable_plugin(self.repo_client)


@app.route("/", methods=['POST'])
def handler():
    payload = request.json
    action = GitHubRepoAction(payload)
    action.handle_action()
    return "ok"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
