import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  #'/home/pi/Desktop/ZL-PI/factory_code/'
import cv2
import time
from math import *
import pyzbar.pyzbar as pyzbar
import Camera

import ZL_SDK.Z_UartServer as myUart
import ZL_SDK.z_beep as myBeep

img_w = 320        # 摄像头画面宽
img_h = 240        # 摄像头画面高

barcodeData = ''   # 二维码信息内容

q_x = 0            # 用于存储二维码左上角x坐标
q_y = 0            # 用于存储二维码左上角y坐标
q_h = 0            # 用于存储二维码高
q_w = 0            # 用于存储二维码宽

# MP3播报指令
voice_dict = {            
            '$TZ!':'#030P1540T1000!','$FW!':'#030P1541T1000!',
            '$QJ!':'#030P1545T1000!','$HT!':'#030P1546T1000!', '$ZZ!':'#030P1547T1000!','$YZ!':'#030P1548T1000!',
            }

run_dict = {"$TZ!":0,"$QJ!":1,"$HT!":2,"$ZZ!":3,"$YZ!":4,
            "$ZXQY!":5,"$ZPY!":6,"$ZXHY!":7,
            "$YXQY!":8,"$YPY!":9,"$YXHY!":10   
            }

# 二维码识别
def qrd_detect():
    global frame, q_x, q_y, q_h, q_w, kms_x, kms_y, barcodeData#, data
    # 将图片缩放到 320*240
    frame = cv2.resize(frame, (img_w, img_h), interpolation=cv2.INTER_CUBIC) 
    # 转为灰度图像
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # 解析图片信息
    barcodes = pyzbar.decode(gray)
    for barcode in barcodes:
        # 提取二维码的边界框的位置
        (q_x, q_y, q_w, q_h) = barcode.rect
        # 画出图像中二维码的边界框
        cv2.rectangle(gray, (q_x, q_y), (q_x + q_w, q_y + q_h), (0, 0, 255), 2)
        # 二维码数据为字节对象，所以如果我们想在输出图像上画出来，就需要先将它转换成字符串
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        # 绘出图像上二维码的数据和二维码类型
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(frame, text, (q_x, q_y - 10), cv2.FONT_HERSHEY_SIMPLEX,.5, (0, 0, 125), 2)
        #print('q_x', q_x, 'q_y', q_y, 'barcodeData', barcodeData)
        # mp3播报
        if barcodeData in voice_dict:
            mp3_play(barcodeData)
            time.sleep(0.5)
        # 解析动作组
        if barcodeData in run_dict:
            myBeep.beep(1, 0.1)
            car_mode(barcodeData)
        else:
            myUart.uart_send_str('#030P1521T0000!')
            
# MP3播报
def mp3_play(myStr):
    mpStr = voice_dict[myStr]
    myUart.uart_send_str(mpStr) 

def car_mode(myStr):
    global run_time
    car_mode = run_dict[myStr]
    run_time = 1000
    if car_mode == 0:
        car_run(0,0,0,0,0)
    elif car_mode == 1:
        car_run(600,600,600,600,run_time)
    elif car_mode == 2:
        car_run(-600,-600,-600,-600,run_time)
    elif car_mode == 3:
        car_run(-600,600,-600,600,run_time)
    elif car_mode == 4:
        car_run(600,-600,600,-600,run_time)
    elif car_mode == 5:
        car_run(0,600,600,0,run_time)
    elif car_mode == 6:
        car_run(-600,600,600,-600,run_time)
    elif car_mode == 7:
        car_run(0,-600,0,-600,run_time)
    elif car_mode == 8:
        car_run(600,0,0,600,run_time)
    elif car_mode == 9:
        car_run(600,-600,-600,600,run_time)
    elif car_mode == 10:
        car_run(-600,0,0,-600,run_time)

def car_run(qz_speed,qy_speed,hz_speed,hy_speed,time):
    bus_str = ('#006P{0:0>4d}T{4:0>4d}!#007P{1:0>4d}T{4:0>4d}!#008P{2:0>4d}T{4:0>4d}!#009P{3:0>4d}T{4:0>4d}!'
    .format(1500+qz_speed,1500-qy_speed,1500+hz_speed,1500-hy_speed,time))
    print(bus_str)                                                                                                                                                                
    myUart.uart_send_str(bus_str)



# 程序入口
if __name__ == '__main__':
    myBeep.setup_beep()        # 蜂鸣器初始化
    myUart.setup_uart(115200)  # 设置串口
    time.sleep(1)
    # 摄像头库实例化
    cam = Camera.Camera()
    # 打开摄像头
    cam.camera_open()
    frame = None
    # 发出哔哔哔作为开机声音
    myBeep.beep(3, 0.1)
    # 无限循环
    while 1:
        if cam.frame is not None:  
            frame = cam.frame.copy()     # 摄像头画面每一帧
            qrd_detect()                 # 二维码识别
            cv2.imshow("camera", frame)  # 显示画面
            
        # 如果按了ESC就退出 当然也可以自己设置
        if cv2.waitKey(5) & 0xFF == 27:
            break
    myUart.uart_send_str(AGC.myList[2])
    myUart.uart_send_str('#000P1500T1000!#001P1500T1000!')
    cam.camera_close()         # 关闭摄像头
    cv2.destroyAllWindows()    # 释放资源
