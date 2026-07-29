import unittest
from types import SimpleNamespace
from unittest import mock

import openai

from bots.ai_label.bot import AILabelBot
from bots.utils.ai_robot import AIAssistant


class AIAssistantTest(unittest.TestCase):
    def setUp(self):
        self.available_labels = [
            {"name": "bug", "color": "ff0000", "description": "A bug"},
            {"name": "docs", "color": "0000ff", "description": "Documentation"},
        ]

    @mock.patch("bots.utils.ai_robot.oa.OpenAI")
    def test_valid_response(self, openai_client):
        completion = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content='{"labels": ["bug", "unknown", "bug"]}'
                    )
                )
            ]
        )
        openai_client.return_value.chat.completions.create.return_value = completion

        labels = AIAssistant().get_label(
            {"issue_title": "Broken"},
            self.available_labels,
        )

        self.assertEqual(labels, ["bug"])
        call_args = openai_client.return_value.chat.completions.create.call_args
        self.assertEqual(
            call_args.kwargs["response_format"],
            {"type": "json_object"},
        )
        self.assertEqual(call_args.kwargs["temperature"], 0)

    @mock.patch("bots.utils.ai_robot.oa.OpenAI")
    def test_invalid_json(self, openai_client):
        completion = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="[{'name': 'bug'}]"
                    )
                )
            ]
        )
        openai_client.return_value.chat.completions.create.return_value = completion

        labels = AIAssistant().get_label(
            {"issue_title": "Broken"},
            self.available_labels,
        )

        self.assertEqual(labels, [])

    @mock.patch("bots.utils.ai_robot.oa.OpenAI")
    def test_invalid_schema(self, openai_client):
        completion = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content='{"labels": "bug"}'
                    )
                )
            ]
        )
        openai_client.return_value.chat.completions.create.return_value = completion

        labels = AIAssistant().get_label(
            {"issue_title": "Broken"},
            self.available_labels,
        )

        self.assertEqual(labels, [])

    @mock.patch("bots.utils.ai_robot.oa.OpenAI")
    def test_api_failure(self, openai_client):
        openai_client.return_value.chat.completions.create.side_effect = (
            openai.APIConnectionError(request=mock.Mock())
        )

        with self.assertLogs("bots.utils.ai_robot", level="ERROR"):
            labels = AIAssistant().get_label(
                {"issue_title": "Broken"},
                self.available_labels,
            )

        self.assertEqual(labels, [])

    @mock.patch("bots.utils.ai_robot.oa.OpenAI")
    def test_empty_response(self, openai_client):
        openai_client.return_value.chat.completions.create.return_value = (
            SimpleNamespace(choices=[])
        )

        with self.assertLogs("bots.utils.ai_robot", level="WARNING"):
            labels = AIAssistant().get_label(
                {"issue_title": "Broken"},
                self.available_labels,
            )

        self.assertEqual(labels, [])


class AILabelBotTest(unittest.TestCase):
    @mock.patch("bots.ai_label.bot.ai_robot.AIAssistant")
    def test_adds_only_missing_label(self, assistant):
        bug_label = SimpleNamespace(
            name="bug",
            color="ff0000",
            description="A bug",
        )
        docs_label = SimpleNamespace(
            name="docs",
            color="0000ff",
            description="Documentation",
        )
        repo_client = mock.Mock()
        repo_client.get_labels.return_value = [bug_label, docs_label]
        issue = repo_client.get_issue.return_value
        issue.title = "Broken docs"
        issue.body = "The docs are incorrect"
        issue.get_labels.return_value = [bug_label]
        assistant.return_value.get_label.return_value = [
            "bug",
            "docs",
            "unknown",
        ]
        webhook_body = {"issue": {"number": 42}}

        AILabelBot(repo_client, webhook_body, "token").handle_action("issue")

        issue.add_to_labels.assert_called_once_with(docs_label)
        self.assertFalse(repo_client.create_label.called)


if __name__ == "__main__":
    unittest.main()
