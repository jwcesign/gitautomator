import json
import logging
import os

import openai as oa

LOGGER = logging.getLogger(__name__)


class AIAssistant:
    chatgpt_url = ""
    openai_key = ""

    def __init__(self) -> None:
        self.chatgpt_url = os.getenv("CHATGPT_URL")
        self.openai_key = os.getenv("OPENAI_KEY")

    def get_label(self, context: dict, label_list: list) -> list:
        try:
            openai_client = oa.OpenAI(base_url=self.chatgpt_url, api_key=self.openai_key)
            chat_completion = openai_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Select the GitHub labels that best match the supplied issue or pull request. "
                            "Choose only label names from available_labels. Return one JSON object with "
                            'exactly this shape: {"labels": ["label name"]}. Return {"labels": []} when '
                            "none apply. Do not include Markdown or any other text."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "context": context,
                                "available_labels": label_list,
                            }
                        ),
                    },
                ],
                model="qwen-plus",
                response_format={"type": "json_object"},
                temperature=0,
            )
        except oa.OpenAIError:
            LOGGER.exception("AI label selection request failed")
            return []

        try:
            response = chat_completion.choices[0].message.content
        except (AttributeError, IndexError):
            LOGGER.warning("AI label selection returned no response")
            return []

        try:
            parsed_response = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            LOGGER.warning("AI label selection returned invalid JSON")
            return []

        if not isinstance(parsed_response, dict) or not isinstance(parsed_response.get("labels"), list):
            LOGGER.warning("AI label selection returned an invalid schema")
            return []

        available_names = {
            label["name"]
            for label in label_list
            if isinstance(label, dict) and isinstance(label.get("name"), str)
        }
        selected_names = []
        for label_name in parsed_response["labels"]:
            if (
                isinstance(label_name, str)
                and label_name in available_names
                and label_name not in selected_names
            ):
                selected_names.append(label_name)
        return selected_names

    def check_release_note(self, context: str) -> str:
        openai_client = oa.OpenAI(base_url=self.chatgpt_url, api_key=self.openai_key)
        chat_completion = openai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a github app robot, you should check the PR release note \
                    block is ok or not(only when it's a feature or bugfix for end user, other(like doc, ci and etc) just return ok). \
                        The corresponding block is ````release-note {content} ```. \
                        if it's fine, please return ok, or only return format like 'The release note is \
                            either empty or incomplete, please consider: `{content}`', {content} shouldn't contain the markdown things, and it should be wrapped in ``, not ''"},
                {"role": "user", "content": f"context is: \n{context}"}
            ],
            model="qwen-plus",
        )
        resp = chat_completion.choices[0].message.content
        return resp
