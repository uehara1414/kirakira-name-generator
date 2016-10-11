import requests
from bs4 import BeautifulSoup
import json
import random
import sqlite3

def is_katakana(word: str):
    if not word:
        return False

    start = b'\xe3\x82\xa1'
    stop = b'\xe3\x83\xb0'
    for char in word:
        if not start < char.encode(encoding='utf8') < stop:
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
        kana = tds[8].text[0]
        try:
            ret[kana].append(kanji)
        except KeyError:
            ret[kana] = list()
    return ret


def to_kanji(word: str):  # todo: ２文字以上のカタカナからの変換も対応する
    ret = ""
    for kana in word:
        ret += random.choice(get_kanjis(kana))
    return ret


def generate_kirakiraname(keyword):
    keyword = correct_word(keyword)
    words = get_words(keyword)
    ret = list()
    for word in words:
        if not is_katakana(word):
            continue
        try:
            ret.append((to_kanji(word), word))
        except:
            pass
    return ret


def get_kanjis(kana):
    return KANJI_DICT[kana]


KANJI_DICT = generate_kanji_dict()


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

if __name__ == '__main__':
    pass
