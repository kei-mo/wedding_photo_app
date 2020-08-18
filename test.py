from helper import *
import cv2

main_pic_path = './static/img/header.jpg'
image  = cv2.imread(main_pic_path)
data = asarray(image)
# Window name in which image is displayed 
window_name = 'image'
cv2.imshow(window_name, data) 
cv2.waitKey(0)  
cv2.destroyAllWindows()  

# main_pic_path = './static/img/header.jpg'
# hsv = get_hsv_from_path(main_pic_path)
# cv2.imshow(hsv)
# img_target2 = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
# cv2.imwrite(app.config['MAIN_PIC_PATH'],img_target2)