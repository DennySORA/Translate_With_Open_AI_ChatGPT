
import openai
import tiktoken

from typing import Optional

from abstract import TranslateEngineBase


class ChatGPT(TranslateEngineBase):
    def __init__(
        self,
        key: str,
        system_command_message: str,
        *args,
        **kwargs,
    ):
        super().__init__(key, system_command_message)
        self.key = key
        self.current_key_index = 0
        self.system_command_message = {
            "role": "system", "content": system_command_message
        }
        self.message_record = []
        self.result_message = ""

    @staticmethod
    def get_translation_system_command_message(before_lang: str, translation_expert: str, lang: str) -> str:
        return f"you are a \"{before_lang} translation\" expert specialized in translating \"{translation_expert}\" into \"{lang}\"."

    def check_is_max_token(self, messages: list[dict[str, str]]):
        num_tokens = 0
        for message in messages:
            num_tokens += self.count_token(message.get("content", ""))
        print("Check tokens:", num_tokens)
        return num_tokens > 4000

    def count_token(self, content: str) -> int:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        num_tokens = len(encoding.encode(content))
        return num_tokens

    def record_message(self, message: dict[str, str]):
        self.message_record.append(message)

    def check_is_finish(self, response_message: str) -> Optional[dict[str, str]]:
        if response_message.find("<<NOT_FINISH>>") == -1:
            return None
        print("Is Not Finish!!")
        return {"role": "assistant", "content": response_message}

    def create_messages(
        self,
            message: str,
            add_last_recode_index: int = 0,
            is_add_system_command_message: bool = True,
    ) -> list[dict[str, str]]:
        if add_last_recode_index == 0:
            results = [{"role": "user", "content": message}]
        else:
            results = [
                *self.message_record[-add_last_recode_index:],
                {"role": "user", "content": message}
            ]
        if is_add_system_command_message:
            results = [self.system_command_message, *results]
        if self.check_is_max_token(results):
            raise Exception("Max token reached")
        return results

    def translate(self, messages: list[dict[str, str]], continue_count: int = 0) -> str:
        '''
        You can call 'create_messages' to retrieve messages.
        '''

        if continue_count == 0:
            self.message_record = messages
        elif continue_count > 5:
            return "I can't translate this text. Please try again."

        print("Continue count:", continue_count,
              "Messages Len:", len(messages))

        openai.api_key = self.key
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        t_text = (
            completion["choices"][0]
            .get("message")
            .get("content")
            .encode("utf8")
            .decode()
        )

        is_finish = self.check_is_finish(t_text)
        if is_finish is not None:
            self.record_message(is_finish)
            t_text = t_text.replace("<<NOT_FINISH>>", "")
            return t_text + self.translate(
                self.create_messages(
                    "Continue",
                    add_last_recode_index=len(self.message_record),
                    is_add_system_command_message=False,
                ),
                continue_count=continue_count + 1,
            )
        self.message_record = []
        return t_text
