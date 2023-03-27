import os
import tqdm
import json
import asyncio

from pydantic import BaseModel

from abstract import FileEngineBase, TranslateEngineBase
from content_tools import ContentTools


class Context(BaseModel):
    wait_content: list[tuple[int, int, list[str]]]
    work_content: dict[int, tuple[int, int, list[str]]] = dict()
    finish_content: list[tuple[int, int, list[str]]] = list()

    all_index: int


class BText(FileEngineBase):
    def __init__(self, engine: TranslateEngineBase, book_name: str, prompt: str, resume: bool):
        self.token_max_limit = 2000
        self.loop = asyncio.get_event_loop()

        self.book_name = book_name
        self.translate_model = engine
        self.prompt = prompt
        self.prompt_token_count = self.translate_model.count_token(prompt)

        if not resume:
            self.origin_content = ContentTools.auto_format_content(
                self._load_file())
            self.origin_length = len(self.origin_content)
        self._prepare_content(resume)

        self.pbar = tqdm.tqdm(total=self.content.all_index)
        self.pbar.update(len(self.content.finish_content))

    def _load_file(self):
        try:
            with open(self.book_name, "r", encoding="utf-8") as f:
                return f.read()
        except:
            raise Exception("can not load file")

    def _save_file(self, content: str):
        try:
            book = self.book_name.split(".")[:-1]
            book.append("translate_finish.txt")
            with open(".".join(book), "w", encoding="utf-8") as f:
                f.write(content)
        except:
            raise Exception("can not load file")

    def _save_status(self):
        try:
            with open(f"{self.book_name}.temp.json", "w", encoding="utf-8") as f:
                return f.write(json.dumps(self.content.dict(), ensure_ascii=False))
        except:
            raise Exception("can not load file")

    def _save_check(self):
        if len(self.content.work_content) != 0 or len(self.content.wait_content) != 0:
            print("Save Status...")
            self._save_status()
        else:
            print("Save File...")
            self.content.finish_content.sort(key=lambda x: x[0])
            content = "\n\n".join(
                [j for i in self.content.finish_content for j in i[2]])
            content = ContentTools.chinese_format(content)
            self._save_file(content)
            os.remove(f"{self.book_name}.temp.json")

    def _count_token(self, index: int):
        now_token_count = self.translate_model.count_token(
            self.origin_content[index])
        if index+1 < self.origin_length:
            next_token_count = self.translate_model.count_token(
                self.origin_content[index+1])
        else:
            next_token_count = 0
        return now_token_count, next_token_count

    def _split_content(self) -> list[tuple[int, int, list[str]]]:
        print("Loading Content...")

        index = 0
        split_content = list()
        temp_content = list()
        token_count = self.prompt_token_count
        pbar = tqdm.tqdm(total=self.origin_length)

        for i in range(self.origin_length):
            pbar.update(1)
            now_token_count, next_token_count = self._count_token(i)
            temp_content.append(self.origin_content[i])

            if next_token_count != 0 and token_count + now_token_count + next_token_count < self.token_max_limit:
                token_count += now_token_count
                continue

            split_content.append((index, token_count, temp_content.copy()))
            token_count = self.prompt_token_count
            temp_content = list()
            index += 1

        print("Load Finish.")
        pbar.clear()
        pbar.close()
        return split_content

    def _prepare_content(self, resume: bool):
        if resume:
            with open(f"{self.book_name}.temp.json", "r", encoding="utf-8") as f:
                self.content = Context(**json.load(f))
        else:
            split_content = self._split_content()
            self.content = Context(
                wait_content=split_content,
                all_index=len(split_content)
            )

    async def _get_translate_content(self, prepare_content: list[str]) -> str:
        detect_check = 5
        translate_content = ""
        temp = [
            "請務必翻譯成繁體中文！",
            "Please translate into Traditional Chinese!",
        ]
        prompt_strengthen = []
        while detect_check > 0:
            print("detect_check:", 5-detect_check, end="\r")
            translate_content = await self.translate_model.translate(
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
            prompt_strengthen.append(temp[detect_check % 2])

        if detect_check == 0:
            raise Exception("can not detect language")

        return translate_content

    async def _translate(self, running_id: int, prepare_content: tuple[int, int, list[str]]) -> list[str]:
        print(
            f"{running_id} Pool Running Sequence : {prepare_content[0]} - Token {prepare_content[1]}")
        translate_content = await self._get_translate_content(prepare_content[2])
        translate_content = ContentTools.translate_chinese_convert(
            translate_content)
        translate_content = ContentTools.auto_format_content(
            translate_content)
        print("prepare_content:", "".join(prepare_content[2]))
        print("translate_content:", "".join(translate_content))
        return translate_content

    async def _run_translate_pool(self, running_id: int):
        count = 0
        while True:
            print(f"{running_id} Pool Running Count : {count}")
            print(len(self.content.wait_content))
            if len(self.content.wait_content) == 0:
                print(f"{running_id} Pool Close.")
                return None

            prepare_content = self.content.wait_content.pop()
            self.content.work_content[prepare_content[0]] = prepare_content

            try:
                self.pbar.update(1)
                result = await self._translate(running_id, prepare_content)
            except (KeyboardInterrupt, asyncio.CancelledError):
                print(f"{running_id} Pool Close.")
                self.content.wait_content.append(prepare_content)
                return None
            except Exception as e:
                print(e)
                self.content.wait_content.append(prepare_content)
                continue
            else:
                self.content.finish_content.append((
                    prepare_content[0],
                    prepare_content[1],
                    result
                ))
                print(f"{running_id} Pool Finish.")
            finally:
                del self.content.work_content[prepare_content[0]]
                self._save_status()

    async def translate(self, count: int):
        try:
            await asyncio.gather(*[
                self.loop.create_task(
                    self._run_translate_pool(i)
                )
                for i in range(count)
            ])
        finally:
            self._save_check()
            self.pbar.close()
