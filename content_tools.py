
import re
import tiktoken

from typing import Union
from langdetect import detect

class ContentTools:

    @staticmethod
    def auto_format_content(content: Union[str, list[str]]) -> list[str]:
        if isinstance(content, str):
            result = content.split("\n")
        else:
            result = content
        result = ContentTools.scan_content(result)
        return result

    @staticmethod
    def scan_content(content: list) -> list[str]:
        result = list()
        for i in content:
            i = i.strip()
            if len(i) != 0:
                result.append(i)
        return result

    @staticmethod
    def count_token(content: str) -> int:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        num_tokens = len(encoding.encode(content))
        return num_tokens

    @staticmethod
    def check_article_langdetect(content) -> bool:
        lang = detect(content)
        print("detect lang:", lang)
        if lang.find("zh") != -1:
            return True
        return False

    @staticmethod
    def chinese_format(content: str) -> str:
        content = content.replace("“", "「")
        content = content.replace("”", "」")
        content = content.replace("‘", "『")
        content = content.replace("’", "』")
        content = content.replace("」", "」\n")
        content = content.replace("』", "』\n")
        content = content.replace("）", "）\n")
        content = re.sub(r'(?<=。)(?![^「」]*」)', '\n', content)
        content = re.sub("\.+", "……", content)
        content = "\n".join(ContentTools.auto_format_content(content))
        content = re.sub("\n+", "\n\n", content)
        return content