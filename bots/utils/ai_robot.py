import os
import json

import openai as oa

class AIAssistant:
    chatgpt_url = ""
    openai_key = ""

    def __init__(self) -> None:
        self.chatgpt_url = os.getenv("CHATGPT_URL")
        self.openai_key = os.getenv("OPENAI_KEY")

    def get_label(self, context: str, label_list: list) -> dict:
        openai_client = oa.OpenAI(base_url=self.chatgpt_url, api_key=self.openai_key)
        chat_completion = openai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a github app robot, you should return which label \
                    should choose base on the context and the label's list I give. \
                        Remeber only return format like(cloud be multiple items or empty if you don't know): \
                            [{labe_name, label color, label description}, more...]"},
                {"role": "user", "content": f"context is: \n{context}\n label's list ls:\n{json.dumps(label_list)}"}
            ],
            model="gpt-4",
        )
        resp = chat_completion.choices[0].message.content
        return json.loads(resp)

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
            model="gpt-4",
        )
        resp = chat_completion.choices[0].message.content
        return resp
