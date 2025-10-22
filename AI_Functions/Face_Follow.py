# 导入模块
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  #'/home/pi/Desktop/ZL-PI/factory_code/'
import cv2
import Camera
import numpy as np
import time

import ZL_SDK.Z_UartServer as myUart
import ZL_SDK.z_beep as myBeep


# 模型位置
modelFile = "/home/pi/Desktop/ZL-PI/AI_Functions/models/res10_300x300_ssd_iter_140000_fp16.caffemodel"
configFile = "/home/pi/Desktop/ZL-PI/AI_Functions/models/deploy.prototxt"
net = cv2.dnn.readNetFromCaffe(configFile, modelFile)

conf_threshold = 0.6

# 
def face_follow():
    global frame
    #将图片缩放到 320*240
    frame = cv2.resize(frame, (320,240), interpolation = cv2.INTER_CUBIC) 
    img_h, img_w = frame.shape[:2] 
    blob = cv2.dnn.blobFromImage(frame, 1, (150, 150), [104, 117, 123], False, False)
    net.setInput(blob)
    detections = net.forward() #计算识别
    f_x = 0
    f_y = 0
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]        
        if confidence > conf_threshold:           
            #识别到的人脸的各个坐标转换未缩放前的坐标
            x1 = int(detections[0, 0, i, 3] * img_w)
            y1 = int(detections[0, 0, i, 4] * img_h)
            x2 = int(detections[0, 0, i, 5] * img_w)
            y2 = int(detections[0, 0, i, 6] * img_h)             
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2, 8) #将识别到的人脸框出
            
            f_x = x1+(x2-x1)/2
            f_y = y1+(y2-y1)/2
            print('face_x:{},face_y:{}'.format(f_x,f_y)) 
    
def car_run(qz_speed,qy_speed,hz_speed,hy_speed,time):
    bus_str = ('#006P{0:0>4d}T{4:0>4d}!#007P{1:0>4d}T{4:0>4d}!#008P{2:0>4d}T{4:0>4d}!#009P{3:0>4d}T{4:0>4d}!'
    .format(1500+qz_speed,1500-qy_speed,1500+hz_speed,1500-hy_speed,time))
    print(bus_str)                                                                                                                                                                
    myUart.uart_send_str(bus_str)


# 程序入口
if __name__ == '__main__':
    myBeep.setup_beep()       # 蜂鸣器初始化
    myUart.setup_uart(115200) # 设置串口
    cam = Camera.Camera()     # 摄像头库实例化
    cam.camera_open()         # 打开摄像头
    frame = None              # 用于接收摄像头拍摄到的每一帧画面
    time.sleep(1)             # 延时1妙
    myBeep.beep(3, 0.1)       # 蜂鸣器响三声
    myUart.uart_send_str('#000P1700T1000!')
    # 无限循环
    while 1:
        if cam.frame is not None:
            frame = cam.frame.copy()
            face_follow()
            cv2.imshow('frame', frame)
        # 如果按了ESC就退出 当然也可以自己设置
        if cv2.waitKey(5) & 0xFF == 27:
            break
    myUart.uart_send_str('#255P1500T1000!')  # 云台舵机复位
    cam.camera_close()        # 关闭摄像头
    cv2.destroyAllWindows()   # 释放资源
