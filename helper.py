from PIL import Image
from numpy import asarray
import cv2
from scipy import stats
import numpy as np
def get_hsv_from_path(path):
    image  = Image.open(path)
    data = asarray(image)
    hsv = cv2.cvtColor(data, cv2.COLOR_BGR2HSV)
    return hsv

def get_hsv_info(hsv, hue_constant: int):
    size_3d_array = hsv.shape
    total_pixel = size_3d_array[0]*size_3d_array[1]	# ピクセル数
    hue_category_list = []		# 各ピクセルのhue_categoryをリストで記憶
    s = 0
    v = 0
    denom = 180 / hue_constant
    for i in range(size_3d_array[0]):
        for j in range(size_3d_array[1]):
            hsv_px = hsv[i,j,:]
            s = s + hsv_px[1]	# sをたす
            v = v + hsv_px[2]	# vをたす
            hue_px = hsv_px[0]
            hue_category_px = hue_px // denom
            hue_category_list.append(hue_category_px)	# hue_categoryのリストを追加
    avg_s = s/total_pixel
    avg_v = v/total_pixel
    array_hue_category_list = np.array(hue_category_list)
    hue_category = int(stats.mode(array_hue_category_list).mode[0])	
    return hue_category, avg_s, avg_v
