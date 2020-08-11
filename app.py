import os
# request フォームから送信した情報を扱うためのモジュール
# redirect  ページの移動
# url_for アドレス遷移
from flask import Flask, request, redirect, url_for, render_template, current_app
# ファイル名をチェックする関数
from werkzeug.utils import secure_filename
# 画像のダウンロード
from flask import send_from_directory
# from livereload import Server, shell
import numpy as np
from helper import get_hsv_from_path, get_hsv_info
import pickle
import cv2
import copy

# 画像のアップロード先のディレクトリ
UPLOAD_FOLDER = './uploads'
main_pic_path = './static/img/header.jpg'

# アップロードされる拡張子の制限
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'gif'])

app = Flask(__name__)
# remember to use DEBUG mode for templates auto reload
# https://github.com/lepture/python-livereload/issues/144
app.debug = True
# print(app.wsgi_app) -> <bound method Flask.wsgi_app of <Flask 'app'>>
# server = Server(app.wsgi_app)

# server.watch('./uploads', )
# server.serve(watch)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAIN_PIC_PATH'] = main_pic_path

# global constant
hue_constant = 18
pixel_resolution = 30

# global variable
hue_block = []

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

def allwed_file(filename):
    # .があるかどうかのチェックと、拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# http://127.0.0.1:5000をルートとして、("")の中でアクセスポイント指定
# @app.route("hoge")などで指定すると、http://127.0.0.1:5000/hogeでの動作を記述できる。
@app.route('/', methods=['GET', 'POST'])
def uploads_file():
    # リクエストがポストかどうかの判別
    if request.method == 'POST':
        # ファイルがなかった場合の処理
        if 'file' not in request.files:
            flash('ファイルがありません')
            return redirect(request.url)
        # データの取り出し
        file = request.files['file']
        # ファイル名がなかった時の処理
        if file.filename == '':
            flash('ファイルがありません')
            return redirect(request.url)
        # ファイルのチェック
        if file and allwed_file(file.filename):
            # 危険な文字を削除（サニタイズ処理）
            filename = secure_filename(file.filename)
            # ファイルの保存
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            with open("target.npy", "rb") as f:
                hsv_target = np.load(f)
            try:
                with open("hue_block.pkl", "rb") as f:
                    hue_block = pickle.load(f)
            except:
                raise Exception("perhaps no pkl file.")
            hsv = get_hsv_from_path(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            hsv = cv2.resize(hsv , (pixel_resolution, pixel_resolution))
            # TODO:target.npyの更新
            hue, s, v = get_hsv_info(hsv, hue_constant)
            for i,j,avg_s,avg_v in hue_block[hue]:
                hsv_target[i*pixel_resolution : (i + 1) * pixel_resolution, \
                            j*pixel_resolution : (j + 1) * pixel_resolution, :] = hsv
            # 画像のhue, sat, briを計算
            # 正方形にする
            # hue_blockの対象カテゴリを最新の画像で置換
            # アップロード後のページに転送
            hsv_target = np.array(hsv_target)

                    # cv2.cvtColor
            img_target2 = cv2.cvtColor(hsv_target, cv2.COLOR_HSV2BGR)
            cv2.imwrite(app.config['MAIN_PIC_PATH'],img_target2)
            # img = Image.fromarray(hsv)
            return render_template("index.html")
    if request.method == 'GET':
        print(current_app)
        print(dir(current_app))
        # target.npyを画像にする下に手渡す
        return render_template("index.html")


@app.route('/preview', methods=['GET', 'POST'])
def preview():
    return render_template("preview.html")

@app.route('/admin', methods=['GET', 'POST'])
def set_target():
    # リクエストがポストかどうかの判別
    if request.method == 'POST':
        # ファイルがなかった場合の処理
        if 'file' not in request.files:
            flash('ファイルがありません')
            return redirect(request.url)
        # データの取り出し
        file = request.files['file']
        # ファイル名がなかった時の処理
        if file.filename == '':
            flash('ファイルがありません')
            return redirect(request.url)
        # ファイルのチェック
        if file and allwed_file(file.filename):
            # 危険な文字を削除（サニタイズ処理）
            filename = secure_filename(file.filename)
            # ファイルの保存
            file.save(app.config['MAIN_PIC_PATH'])
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], "original_target.jpg"))
            hsv = get_hsv_from_path(app.config['MAIN_PIC_PATH'])
            # hsv = get_hsv_from_path(os.path.join(app.config['UPLOAD_FOLDER'], "header.jpg"))

            with open("target.npy", "wb") as f:
                np.save(f, hsv)
            # target.npyを使ってhue_blockの作成
            max_0dim = hsv.shape[0] // pixel_resolution
            max_1dim = hsv.shape[1] // pixel_resolution
            hue_block = [[] for _ in range(hue_constant)]
            for i in range(max_0dim):
                for j in range(max_1dim):
                    block_hsv = hsv[i*pixel_resolution : (i + 1) * pixel_resolution, \
                                    j*pixel_resolution : (j + 1) * pixel_resolution, :]
                    hue_category, avg_s, avg_v = get_hsv_info(block_hsv, hue_constant)
                    hue_block[hue_category].append((i,j,avg_s,avg_v))
            with open("hue_block.pkl", "wb") as f:
                pickle.dump(hue_block, f)

            return redirect(url_for("uploads_file"))
    return render_template("admin.html")

@app.route('/uploads/<filename>')
# ファイルを表示する
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    # webサーバー立ち上げ
    app.run()