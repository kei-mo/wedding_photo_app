from PIL import Image
from numpy import asarray
import cv2
from scipy import stats
import numpy as np

def get_rgb_from_path(path):
    image  = Image.open(path) # TODO:opencvに書き直す
    image = image.convert("RGB")
    rgb = asarray(image)
    return rgb


def get_bgr_info(img):
    avg_b = int(np.mean(img[:,:,0]))
    avg_g = int(np.mean(img[:,:,1]))
    avg_r = int(np.mean(img[:,:,2]))
    return avg_b, avg_g, avg_r

def get_rgb_info(img):
    avg_r = int(np.mean(img[:,:,0]))
    avg_g = int(np.mean(img[:,:,1]))
    avg_b = int(np.mean(img[:,:,2]))
    return avg_r, avg_g, avg_b



def get_hsv_from_path(path):
    image  = cv2.imread(path)
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
