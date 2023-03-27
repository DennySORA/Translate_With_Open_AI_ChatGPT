
import re
import opencc

from typing import Union
from langdetect import detect


class ContentTools:

    @staticmethod
    def translate_chinese_convert(content: str) -> str:
        converter = opencc.OpenCC('s2twp.json')
        return converter.convert(content)

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
    def check_article_langdetect(content) -> bool:
        lang = detect(content)
        print("detect lang:", lang)
        if lang.find("zh") != -1:
            return True
        return False

    @staticmethod
    def chinese_format(content: str) -> str:
        replacements = [
            ("“", "「"),
            ("”", "」"),
            ("‘", "『"),
            ("’", "』"),
            ("」", "」\n"),
            ("』", "』\n"),
            ("）", "）\n"),
            ("<<START>>", ""),
            ("<<FINISH>>", "")
        ]
        for i in replacements:
            content = content.replace(i[0], i[1])

        replacements_re = [
            (r'(?<=。)(?![^「」]*」)', '\n'),
            ("\.+", "……"),
            (r"\n+」","」"),
            (r"\n+』","』")
        ]
        for i in replacements_re:
            content = re.sub(i[0], i[1], content)

        content = "\n".join(ContentTools.auto_format_content(content))
        content = re.sub("\n+", "\n\n", content)
        return content
