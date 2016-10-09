import os
from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return 'テスト'


@app.route('/hello/<name>')
def hello(name=''):
    if name == '':
        name = 'ななしさん'
    return render_template('hello.html', name=name)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(port=port)