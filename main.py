
from file_engine import BText
from translate_engine import ChatGPT


def main():
    book_name = "temp.txt"
    before_lang = "Japanese"
    translation_expert = "Japanese light novels"
    lang = "Traditional Chinese"
    system_command_message = ChatGPT.get_translation_system_command_message(
        before_lang, translation_expert, lang
    )
    prompt = f"""
I will provide an \"{before_lang}\" article, Request your assistance in translating the following article into \"{lang}\".
And taking into account the surrounding text and context to ensure accurate and appropriate translation without any logical errors.
Please maintain the original meaning of the article and use the storytelling style typical of "{translation_expert}".
Do not add any additional text in the translation.
Be faithful or accurate in translation.
Make the translation readable or intelligible.
Kindly provide only the translated content and omit the original text.
Please use notation: 「」.
Again, translated into \"{lang}\".
If the answer is not complete, please add the <<NOT_FINISH>> tag at the end.
example:
A:```
新生アドラー軍に【源神殿】に発生した仮面の幻影達。双方ともが間違いなく、高レベルハンターでも容易く相手をする事などできない、恐るべき相手だ。
「やれやれ、今回ばかりはもう終わりかと思ったよ」
額を腕で拭う。快適だったおかげで汗はかいていなかった。
「こら、ヨワニンゲンッ！　何全てを終わらせた雰囲気出しているんだ、です！　全く何も解決していないだろ、です！」
「目的だった解呪も行えていません。乱入者があったのは予想外でしたし、助かったことは間違いないですが――」
ラピスが僕に冷ややかな（いつも通りである事は言うまでもない）視線を向けて言う。
```
Q:```
新生阿德拉軍隊，還有『源神殿』顯現的假面幻影。兩邊都無疑是高等級獵人無法輕易戰勝的可怕對手。
「呀嘞呀嘞，這次我是真的以為要完了」
我擦了擦額頭。因為很舒適所以沒有出汗。
「喂，弱雞人類！你怎麼就散發出全部結束的氛圍的說！這根本什麼都沒解決好嗎，的說！」
「原本的目的是解咒，已經沒法進行了。有人亂入我是沒想到的，不過她們無疑幫了個大忙——」
拉碧絲向我投來冰冷的視線（不用說一直都是這樣的了）然後說。
```
Below is the content: \n
    """
    open_ai_api_key = ""
    translate_engine = ChatGPT(open_ai_api_key, system_command_message)
    book = BText(translate_engine, book_name, prompt, False)
    book.make_bilingual_book()


if __name__ == "__main__":
    main()
