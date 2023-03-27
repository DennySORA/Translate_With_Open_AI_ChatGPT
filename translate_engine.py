
import openai
import tiktoken

from typing import Optional, Any

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
            "role": "system",
            "content": system_command_message
        }
        self.message_record = []
        self.result_message = ""

    def _check_is_max_token(self, messages: list[dict[str, str]]):
        num_tokens = 0
        for message in messages:
            num_tokens += self.count_token(message.get("content", ""))
        print("Check tokens:", num_tokens)
        return num_tokens > 4000

    def _is_translate_finish(self, response_message: str) -> bool:
        if response_message.find("<<NOT_FINISH>>") == -1:
            return True
        print("Is Not Finish!!")
        return False

    def _record_message(self, message: dict[str, str]):
        self.message_record.append(message)

    def count_token(self, content: str) -> int:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        num_tokens = len(encoding.encode(content))
        return num_tokens

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
        if self._check_is_max_token(results):
            raise Exception("Max token reached")
        return results

    def _finish_check(self, translate_content: str, continue_count: int):
        is_finish = self._is_translate_finish(translate_content)
        if is_finish is False:
            self._record_message({
                "role": "assistant",
                "content": translate_content
            })
            translate_content = translate_content.replace("<<NOT_FINISH>>", "")
            return translate_content + self.translate(
                self.create_messages(
                    "Continue",
                    add_last_recode_index=len(self.message_record),
                    is_add_system_command_message=False,
                ),
                continue_count=continue_count + 1,
            )
        self.message_record = []
        return translate_content

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
        completion: Any = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        t_text = (
            completion.get("choices")[0]
            .get("message")
            .get("content")
            .encode("utf8")
            .decode()
        )

        return self._finish_check(t_text, continue_count)
