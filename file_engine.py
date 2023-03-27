import os
import tqdm

from abstract import FileEngineBase, TranslateEngineBase
from content_tools import ContentTools


class BText(FileEngineBase):
    def __init__(self, engine: TranslateEngineBase, book_name: str, prompt: str, resume: bool):
        self.book_name = book_name
        self.translate_model = engine
        self.prompt = prompt
        self.prompt_token_count = ContentTools.count_token(self.prompt)

        self.book_path = os.path.abspath(self.book_name)
        self.bin_path = f"{self.book_path}.temp.bin"

        self.origin_content = ContentTools.auto_format_content(
            self.load_file(self.book_path))
        self.origin_length = len(self.origin_content)

        self.resume = resume
        if self.resume:
            self.content_to_save = ContentTools.auto_format_content(
                self.load_file(self.bin_path))
            self.save_index = int(self.content_to_save[0])
            self.content_to_save = self.content_to_save[1:]
        else:
            self.content_to_save = list()
            self.save_index = 0

    def translate(self):
        all_token_count = 0
        index = 0
        token_count = self.prompt_token_count
        prepare_content = list()
        pbar = tqdm.tqdm(total=self.origin_length)
        try:
            for i in range(self.origin_length):
                pbar.update(1)
                if index < self.save_index:
                    index += 1
                    continue

                now_token_count, next_token_count = self.check_token_count(
                    token_count, i)

                prepare_content.append(self.origin_content[i])
                index += 1
                if self.origin_length-1 == i:
                    pass
                elif token_count + now_token_count + next_token_count < 1500:
                    token_count += now_token_count
                    continue

                print("\n", "all_token_count", all_token_count,
                      "Start token:", token_count + now_token_count)
                all_token_count += token_count + now_token_count

                translate_content = self.get_translate_content(prepare_content)

                translate_content = ContentTools.translate_chinese_convert(translate_content)

                translate_content = ContentTools.auto_format_content(
                    translate_content)

                print("prepare_content:", prepare_content)
                print("translate_content:", translate_content)

                self.content_to_save.extend(translate_content)
                self.save_index = index
                prepare_content = list()
                token_count = self.prompt_token_count
                self._save_all()
        except (KeyboardInterrupt, Exception) as e:
            print(e)
            print("you can resume it next time")
            self.content_to_save.insert(0, str(self.save_index))
            self.save_file(self.bin_path, "\n".join(self.content_to_save))
        finally:
            pbar.close()
            name = self.book_name.split(".")[0]
            temp = ContentTools.chinese_format("\n".join(self.content_to_save))
            self.save_file(f"{name}_bilingual.txt", temp)

    def _save_all(self):
        self.save_file(self.bin_path, str(self.save_index) +
                       "\n"+"\n".join(self.content_to_save))
        name = self.book_name.split(".")[0]
        temp = ContentTools.chinese_format("\n".join(self.content_to_save))
        self.save_file(f"{name}_bilingual.txt", temp)

    def get_translate_content(self, prepare_content: list[str]) -> str:
        detect_check = 5
        translate_content = ""
        temp = [
            "請務必翻譯成繁體中文！",
            "Please translate into Traditional Chinese!",
        ]
        prompt_strengthen = []
        while detect_check > 0:
            print("detect_check:", 5-detect_check, end="\r")
            translate_content = self.translate_model.translate(
                self.translate_model.create_messages(
                    "\n".join([
                        *prompt_strengthen,
                        self.prompt,
                        *prepare_content
                    ])
                )
            )

            detect_check -= 1
            if ContentTools.check_article_langdetect(translate_content):
                break
            print(translate_content)
            prompt_strengthen.append(temp[detect_check % 2])

        if detect_check == 0:
            raise Exception("can not detect language")

        return translate_content

    def check_token_count(self, token_count, i):
        now_token_count = self.translate_model.count_token(
            self.origin_content[i])
        if i+1 < self.origin_length:
            next_token_count = self.translate_model.count_token(
                self.origin_content[i+1])
        else:
            next_token_count = 0

        print("token_count", token_count, "now_token_count:",
              now_token_count, "next_token_count", next_token_count, "                  ", end="\r")

        return now_token_count, next_token_count

    def load_file(self, book_path):
        try:
            with open(book_path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            raise Exception("can not load file")

    def save_file(self, book_path, content):
        try:
            with open(book_path, "w", encoding="utf-8") as f:
                f.write(content)
        except:
            raise Exception("can not save file")
