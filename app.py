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
from helper import get_hsv_from_path, get_hsv_info,get_bgr_info,get_rgb_from_path
import pickle
import cv2
import copy
import shutil
from PIL import Image


# 画像のアップロード先のディレクトリ
UPLOAD_FOLDER = './uploads'
main_pic_path = './static/img/header.jpg'
orig_pic_path = './static/img/orig.jpg'

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
app.config['ORIG_PIC_PATH'] = orig_pic_path


# global constant
hue_constant = 18
pixel_resolution = 30

# global variable
hue_block = []
full_resolution = (1080, 1920)

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

            # 必要な情報の読み込み
            try:
                with open("rgb_block.pkl","rb") as f:
                    rgb_block = pickle.load(f)
            except:
                raise Exception("perhaps no pkl file.")
            
            rgb_target = np.load('target.npy')
            allocated = np.load('allocated.npy')
    

            # upload された画像のr,g,bの平均を計算
            rgb = get_rgb_from_path(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            rgb = cv2.resize(rgb , (pixel_resolution, pixel_resolution))
            r,g,b = np.mean(rgb[:,:,0]), np.mean(rgb[:,:,1]), np.mean(rgb[:,:,2])

            # 距離を計算
            deltaR, deltaG, deltaB = rgb_block[:,:,0] - r, rgb_block[:,:,1] - g, rgb_block[:,:,2] - b
            dist = np.sqrt(2*deltaR**2 + 4*deltaG**2 + 3*deltaB**2) # 距離の計算　blockw*blockhの二次元行列

            # dist が一定の値以下のblock
            thresh = 1000
            overwrite = dist<thresh # blockw*blockhの二次元行列にboolenが入った形
            overwrite = (overwrite &  np.logical_not(allocated)) #すでに挿入されているところには入れない
            allocated = (overwrite | allocated)
            
            # 挿入
            insert_posy,insert_posx = np.where(overwrite==True) # 置き換える座標を撮ってくる
            
            print(rgb_target.shape, rgb.shape)
            for x,y in zip(insert_posx,insert_posy):
                rgb_target[y*pixel_resolution : (y + 1) * pixel_resolution, \
                            x*pixel_resolution : (x + 1) * pixel_resolution, :] = rgb

            # 画像保存　更新
            bgr_target = cv2.cvtColor(rgb_target, cv2.COLOR_RGB2BGR)
            cv2.imwrite(app.config['MAIN_PIC_PATH'],bgr_target)
            # img = Image.fromarray(hsv)

            img1 = Image.open(app.config['MAIN_PIC_PATH'])
            img1.putalpha(80)
            img2 = Image.open(app.config['ORIG_PIC_PATH'])
            img2.putalpha(250)
            bg = Image.new("RGBA", full_resolution[::-1], (255, 255, 255, 0))
            bg.paste(img2, (0, 0), img2)
            bg.paste(img1, (0, 0), img1)
            bg = bg.convert("RGB")
            bg.save(app.config['MAIN_PIC_PATH'])

            np.save('target.npy',rgb_target)
            np.save('allocated.npy',allocated)
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
            # file.save(app.config['ORIG_PIC_PATH'])
            # hsv = get_hsv_from_path(os.path.join(app.config['UPLOAD_FOLDER'], "header.jpg"))
            # hsv = cv2.resize(hsv , full_resolution)


            rgb = get_rgb_from_path(app.config['MAIN_PIC_PATH'])
            rgb_shape = rgb.shape #(x,y,3)
            scaled_y = round(full_resolution[0] / rgb_shape[0] * rgb_shape[1])
            rgb = cv2.resize(rgb , (scaled_y, full_resolution[0]))
            np.save("target.npy",rgb)
            bgr_target = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            cv2.imwrite(app.config['ORIG_PIC_PATH'],bgr_target)

            h,w,cv = rgb.shape
            wb = w // pixel_resolution
            hb = h // pixel_resolution
            rgb_block = np.empty([hb,wb,3],dtype=int)
            for x in range(wb):
                for y in range(hb):
                    block = rgb[pixel_resolution*y:pixel_resolution*y + pixel_resolution, pixel_resolution*x:pixel_resolution*x+pixel_resolution,    :]
                    avg_b, avg_g, avg_r = get_bgr_info(block)
                    rgb_block[y,x,:] = [avg_r, avg_g, avg_b] 
                with open("rgb_block.pkl", "wb") as f:
                    pickle.dump(rgb_block, f)
            allocated = np.zeros((hb,wb),dtype=bool) # 初期化
            np.save('allocated.npy',allocated)
            shutil.copyfile(app.config['ORIG_PIC_PATH'], app.config['MAIN_PIC_PATH'])
            return redirect(url_for("uploads_file"))

    return render_template("admin.html")

@app.route('/uploads/<filename>')
# ファイルを表示する
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    # webサーバー立ち上げ
    app.run()