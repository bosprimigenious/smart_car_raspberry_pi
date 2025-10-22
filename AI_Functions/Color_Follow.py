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

# 要识别的颜色字典
color_dist = {
             'RED':   {'Lower': np.array([0, 80, 80]), 'Upper': np.array([10, 255, 255])},
             'GREEN': {'Lower': np.array([35, 43, 35]), 'Upper': np.array([90, 255, 255])},
             'BLUE':  {'Lower': np.array([90, 50, 50]), 'Upper': np.array([120, 255, 255])},
             'YELLOW':  {'Lower': np.array([20, 50, 50]), 'Upper': np.array([34, 255, 255])},
             }

width = 320            # 摄像头画面宽
hight = 240            # 摄像头画面高

c_x = 0                # 用于存储目标颜色区域的中心点的x坐标
c_y = 0                # 用于存储目标颜色区域的中心点的y坐标
c_h = 0                # 用于存储目标颜色区域的高
c_w = 0                # 用于存储目标颜色区域的宽

# 颜色跟随
def color_follow(color):
    global frame,c_x,c_y,c_h,c_w,follow_step,systick_ms_color,next_time,count,yt_flag
    # 将图片缩放到 320*240 
    frame = cv2.resize(frame, (width,hight), interpolation=cv2.INTER_CUBIC) 
    #1-高斯滤波GaussianBlur() 让图片模糊
    frame = cv2.GaussianBlur(frame,(5,5),0)   
    #2-转换HSV的样式 以便检测
    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV) 
    #3-查找字典
    mask = cv2.inRange(hsv, color_dist[color]['Lower'], color_dist[color]['Upper']) 
    #4-腐蚀图像
    mask = cv2.erode(mask,None,iterations=2)
    #5-膨胀
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))       
    #6-边缘检测
    cnts = cv2.findContours(mask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2]                    
    # 通过边缘检测来确定所识别物体的位置信息得到相对坐标
    if len(cnts) >0:
        cnt = max(cnts,key=cv2.contourArea)
        rect = cv2.minAreaRect(cnt)
        # 获取最小外接矩形的4个顶点
        box = cv2.boxPoints(rect)
        cv2.drawContours(frame, [np.int0(box)], -1, (0, 255, 255), 2) #绘制轮廓        
        # 获取坐标 长宽 角度
        c_x, c_y = rect[0]
        c_h, c_w = rect[1]
        area = c_h * c_w
        if 10 < c_h < 150 and 10 < c_w < 150:
            if 120 < c_x < 200 and 4000 < area < 10000:
                car_run(0,0,0,0,0)
            else:
                if c_x < 120 or c_x > 200:
                    angularSpeed = int(((160 - c_x)*5))
                    car_run(-angularSpeed,angularSpeed,-angularSpeed,angularSpeed,abs(angularSpeed))
                else:             
                    if area < 4000 or area > 10000:
                        linearSpeed = int((10000-area)/30) 
                        car_run(linearSpeed,linearSpeed,linearSpeed,linearSpeed,abs(linearSpeed))
                 
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
    myUart.uart_send_str('#000P1500T1000!')
    #myUart.uart_send_str('#006P1800T0000!')
    # 无限循环
    while 1:
        if cam.frame is not None:
            frame = cam.frame.copy()
            color_follow('GREEN')       
            cv2.imshow('frame', frame)
        # 如果按了ESC就退出 当然也可以自己设置
        if cv2.waitKey(5) & 0xFF == 27:
            break
    myUart.uart_send_str('#255P1500T1000!')  # 云台舵机复位
    cam.camera_close()        # 关闭摄像头
    cv2.destroyAllWindows()   # 释放资源
