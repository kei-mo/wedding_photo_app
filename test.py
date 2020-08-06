def get_hsv_info(hsv):

# avg_s = np.mean(np.ravel(hsv[:,:,1]))
avg_s = np.mean(hsv[:,:,1])
avg_v = np.mean(hsv[:,:,2])
hue_list = hsv[:,:,0].ravel() // 10 # hueをとってきて一次元化
