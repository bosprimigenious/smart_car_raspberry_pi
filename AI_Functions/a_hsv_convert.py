#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  #'/home/pi/Desktop/ZL-PI/factory_code/'
import cv2
import numpy as np

import Camera
#import ZL_SDK.Z_UartServer as myUart

img_w = 640   # 摄像头画面宽
img_h = 480   # 摄像头画面高


def nothing(*arg):
    pass
 
#icol = (28, 46, 98, 63, 211, 255)    # Green
icol = (18, 0, 196, 36, 255, 255)    # Yellow
#icol = (76,78, 18, 136, 223, 242)    # Blue
#icol = (0, 100, 80, 10, 255, 255)    # Red
cv2.namedWindow('colorTest')
# Lower range colour sliders.
cv2.createTrackbar('lowHue', 'colorTest', icol[0], 180, nothing)
cv2.createTrackbar('lowSat', 'colorTest', icol[1], 255, nothing)
cv2.createTrackbar('lowVal', 'colorTest', icol[2], 255, nothing)
# Higher range colour sliders.
cv2.createTrackbar('highHue', 'colorTest', icol[3], 180, nothing)
cv2.createTrackbar('highSat', 'colorTest', icol[4], 255, nothing)
cv2.createTrackbar('highVal', 'colorTest', icol[5], 255, nothing)

def hsv_convert(frame):
    frame = cv2.resize(frame, (320,240), interpolation=cv2.INTER_CUBIC) #将图片缩放到 320*240 
    # Get HSV values from the GUI sliders.
    lowHue = cv2.getTrackbarPos('lowHue', 'colorTest')
    lowSat = cv2.getTrackbarPos('lowSat', 'colorTest')
    lowVal = cv2.getTrackbarPos('lowVal', 'colorTest')
    highHue = cv2.getTrackbarPos('highHue', 'colorTest')
    highSat = cv2.getTrackbarPos('highSat', 'colorTest')
    highVal = cv2.getTrackbarPos('highVal', 'colorTest')

    # Blur methods available, comment or uncomment to try different blur methods.
    frameBGR = cv2.GaussianBlur(frame, (5, 5), 0)

    # Convert the frame to HSV colour model.
    hsv = cv2.cvtColor(frameBGR, cv2.COLOR_BGR2HSV)
    
    # HSV values to define a colour range.
    colorLow = np.array([lowHue,lowSat,lowVal])
    colorHigh = np.array([highHue,highSat,highVal])
    mask = cv2.inRange(hsv, colorLow, colorHigh)
    # Show the first mask
    #cv2.imshow('mask-plain', mask)
 
    kernal = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernal)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernal)
 
    return mask

# 程序入口
if __name__ == '__main__':
    #myUart.setup_uart(115200) # 设置串口
    cam = Camera.Camera()     # 摄像头库实例化
    cam.camera_open()         # 打开摄像头

    while 1:
        if cam.frame is not None:
            frame = cam.frame.copy()
            cv2.line(frame, (int(img_w/2)-10, int(img_h/2)), (int(img_w/2)+10, int(img_h/2)), (0, 0, 255), 1)
            cv2.line(frame, (int(img_w/2),int(img_h/2)-10), (int(img_w/2), int(img_h/2)+10), (0, 0, 255), 1) 
            cv2.imshow('frame', frame)
            frame = hsv_convert(frame)
            cv2.imshow('colortest', frame)
        # 如果按了ESC就退出 当然也可以自己设置
        if cv2.waitKey(5) & 0xFF == 27: 
            break
    cam.camera_close()
    cv2.destroyAllWindows()
