import os
import json
from flask import Flask, render_template, request, send_from_directory

from kirakiraname import generate_kirakiraname, generate_kanji_db

generate_kanji_db()

app = Flask(__name__, static_url_path='/static')

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == 'GET':
        return render_template("index.html")
    elif request.method == 'POST':
        word = request.form.get("word", "")
        names = list()
        for name, kana in generate_kirakiraname(word):
            names.append({"name": name, "kana": kana})
        return render_template("kirakiraname.html", names=names)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(port=port)