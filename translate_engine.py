
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
        self.system_command_message = {
            "role": "system",
            "content": system_command_message
        }
        self.message_record = []
        self.continue_count = 0

    def _check_is_max_token(self, messages: list[dict[str, str]]):
        num_tokens = 0
        for message in messages:
            num_tokens += self.count_token(message.get("content", ""))
        print("Check tokens:", num_tokens)
        return num_tokens > 4000

    def _is_translate_finish(self, response_message: str) -> Optional[bool]:
        if response_message.find("<<NOT_FINISH>>") != -1:
            print("Is Not Finish!!")
            return False
        elif response_message.find("<<FINISH>>") != -1:
            print("Is Finish.")
            return True
        print("Is Failed!!!!!")
        return None

    def _record_message(self, message: dict[str, str]):
        self.message_record.append(message)

    def _handle_false_finish(self, translate_content: str):
        self._record_message({
            "role": "assistant",
            "content": translate_content
        })
        continue_message = self.create_messages(
            "Continue",
            add_last_recode_index=len(self.message_record),
            is_add_system_command_message=False,
        )
        translate_content = translate_content.replace("<<NOT_FINISH>>", "")
        return translate_content + self.translate(continue_message)

    def _finish_check(self, translate_content: str, origin_message: list[dict[str, str]]):
        self.continue_count += 1
        is_finish = self._is_translate_finish(translate_content)
        if is_finish is None:
            return self.translate(origin_message)
        elif is_finish is False:
            return self._handle_false_finish(translate_content)
        else:
            self.message_record = []
            self.continue_count = 0
            return translate_content.replace("<<FINISH>>", "")

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

    def translate(self, messages: list[dict[str, str]]) -> str:
        '''
        You can call 'create_messages' to retrieve messages.
        '''

        if self.continue_count == 0:
            self.message_record = messages
        elif self.continue_count > 5:
            return "I can't translate this text. Please try again."

        print("Continue count:", self.continue_count,
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

        return self._finish_check(t_text, messages)
