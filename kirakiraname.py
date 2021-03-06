import requests
from bs4 import BeautifulSoup
import json
import random

import jaconv


class KanjiNotFoundError(BaseException):
    pass


def is_hiragana(word: str):
    if not word:
        return False

    start1 = b'\xe3\x81\x81'
    stop1 = b'\xe3\x82\xbf'

    start2 = b'\xe3\x82\x80'
    stop2 = b'\xe3\x82\x93'

    for char in word:
        if not ( start1 < char.encode(encoding='utf8') < stop1 or start2 < char.encode(encoding='utf8') < stop2):
            return False
    return True


def to_katakana(word: str):
    if not word:
        return ""

    return jaconv.hira2kata(word)


def is_katakana(word: str):
    if not word:
        return False

    start = b'\xe3\x82\xa1'
    stop = b'\xe3\x83\xb0'
    n = b'\xe3\x83\xb3'
    for char in word:
        if not (start < char.encode(encoding='utf8') < stop or char.encode(encoding='utf8') == n):
            return False
    return True


def get_blinks(word):  # todo: 500 以上のワードも取得するようにする
    if not word:
        return set()

    url = "https://ja.wikipedia.org/w/api.php"
    params = {
        "format": "json",
        "action": "query",
        "list": "backlinks",
        "bltitle": word,
        "bllimit": 500
    }
    res= requests.get(url, params=params)

    results = json.loads(res.text)
    ret = set()
    for link in results["query"]["backlinks"]:
        ret.add(link["title"])
    return ret


def get_links(word): # todo: 500 以上のワードも取得するようにする
    if not word:
        return set()

    url = "https://ja.wikipedia.org/w/api.php"
    params = {
        "format": "json",
        "action": "query",
        "prop": "links",
        "titles": word,
        "pllimit": 500
    }

    ret = requests.get(url, params=params)
    results = json.loads(ret.text)

    ret = set()
    for x in results["query"]["pages"].values():
        for link in x["links"]:
            ret.add(link["title"])
    return ret


def get_words(word):
    a = get_blinks(word)
    b = get_links(word)

    return a and b


def generate_kanji_dict():
    url = "https://ja.wikipedia.org/wiki/%E5%B8%B8%E7%94%A8%E6%BC%A2%E5%AD%97%E4%B8%80%E8%A6%A7"
    ret = requests.get(url)
    soup = BeautifulSoup(ret.text, "lxml")

    table = soup.find_all("table", class_="sortable")[0]

    trs = table.find_all("tr")[1:]
    ret = dict()

    for tr in trs:
        tds = tr.find_all('td')
        kanji = tds[1].text[0]

        for yomi in tds[8].text.split("、"):
            if is_katakana(yomi):
                if not yomi in ret:
                    ret[yomi] = list()
                ret[yomi].append(kanji)

                if len(yomi) == 1:
                    continue

                if not yomi[0] in ret:
                    ret[yomi[0]] = list()
                ret[yomi[0]].append(kanji)

            if is_hiragana(yomi):
                yomi = to_katakana(yomi)
                if not yomi in ret:
                    ret[yomi] = list()
                ret[yomi].append(kanji)
                continue

            if '-' in yomi:
                yomi = to_katakana(yomi.split('-')[0])
                if not yomi in ret:
                    ret[yomi] = list()
                ret[yomi].append(kanji)

    return ret


def to_kanji(word: str):
    if len(word) == 0:
        return ''

    if len(word) == 1:
        try:
            return choice_kanji(word)
        except KeyError:
            raise KanjiNotFoundError

    if len(word) == 2:
        try:
            return choice_kanji(word)
        except KeyError:
            w1 = to_kanji(word[0])
            w2 = to_kanji(word[1])
            return w1 + w2

    if len(word) == 3:
        try:
            return choice_kanji(word)
        except KeyError:
            try:
                w1 = to_kanji(word[:2])
                w2 = to_kanji(word[2:])
            except KeyError:
                w1 = to_kanji(word[1:])
                w2 = to_kanji(word[:1])
            return w1 + w2

    try:
        w1 = to_kanji(word[:3])
        w2 = to_kanji(word[3:])
        return w1 + w2
    except KeyError:
        try:
            w1 = to_kanji(word[:2])
            w2 = to_kanji(word[2:])
            return w1 + w2
        except KeyError:
            w1 = to_kanji(word[:1])
            w2 = to_kanji(word[1:])
            return w1 + w2


def generate_kirakiraname(keyword):
    keyword = correct_word(keyword)
    words = get_words(keyword)
    ret = list()
    for word in words:
        if not is_katakana(word):
            continue
        try:
            ret.append((to_kanji(word), word))
        except KanjiNotFoundError:
            pass
    return ret


def get_kanjis(kana):
    return KANJI_DICT[kana]

def choice_kanji(kana):
    return random.choice(KANJI_DICT[kana])


def correct_word(word):
    """wikipedia に存在しないワードのとき、そのワードを一番関連性のありそうな記事のワードに置き換える"""
    url = "https://ja.wikipedia.org/w/index.php"
    params = {
        "search": word
    }

    res = requests.get(url, params=params)

    soup = BeautifulSoup(res.text, "lxml")

    if not "検索結果" in soup.find("title").text:
        return soup.find("title").text.split()[0]

    if soup.find("p", class_="mw-search-nonefound"):
        return ""  # 検索結果なし

    result = soup.find("div", class_="mw-search-result-heading")

    title = result.find("a").get("title")

    return title


KANJI_DICT = generate_kanji_dict()


if __name__ == '__main__':
    print(to_kanji("ドラゴン"))
