import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  #'/home/pi/Desktop/ZL-PI/factory_code/'
import cv2
import Camera
import pigpio
import numpy as np 
import time

import ZL_SDK.Z_UartServer as myUart
import ZL_SDK.z_beep as myBeep

cx = 0       # 用于接收识别到的目标区域质心的x坐标
cy = 0       # 用于接收识别到的目标区域质心的y坐标
roi = None   # 用于接收摄像头画面的其中一部分

#引脚定义
PIN_yuntai = 26
PIN_camera = 12

pwm_value1 = 1500
pwm_value2 = 1500


#类实例化
pi = pigpio.pi()

#循迹
def car_xunji():
    global frame, cx, cy, roi

    # 缩放输入帧
    frame = cv2.resize(frame, (320, 240), interpolation=cv2.INTER_CUBIC)

    # 取底部 1/3 区域（保证黑线在视野下部）
    roi = frame[160:240, 0:320]

    # 转灰度
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # 先模糊再自适应阈值（减少反光/砖缝干扰）
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    binary = cv2.adaptiveThreshold(
        blur, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 
        15, 4
    )

    # ---【形态学优化】：去掉细线与孤立点 ---
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)

    # ---【轮廓检测】---
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # 过滤掉太小或太细的噪点区域
        filtered = []
        for c in contours:
            area = cv2.contourArea(c)
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = w / float(h)
            # 黑线一般较长，不是细长条
            if area > 500 and aspect_ratio < 5:
                filtered.append(c)

        if not filtered:
            print("No valid contour found")
            car_run(-150, 150, -150, 150, 150)
            return

        # 选择面积最大的轮廓作为主线
        c = max(filtered, key=cv2.contourArea)
        M = cv2.moments(c)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # 可视化辅助线
            cv2.drawContours(roi, [c], -1, (0, 255, 0), 2)
            cv2.line(roi, (cx, 0), (cx, roi.shape[0]), (255, 0, 0), 2)

            # 偏差计算
            error = 160 - cx

            # 比例控制
            Kp = 1.2
            angularSpeed = int(Kp * error)
            baseSpeed = 250
            leftSpeed = np.clip(baseSpeed + angularSpeed, -400, 400)
            rightSpeed = np.clip(baseSpeed - angularSpeed, -400, 400)

            car_run(leftSpeed, rightSpeed, leftSpeed, rightSpeed, abs(baseSpeed))
        else:
            print("Zero division in moment")
    else:
        print("Line lost, searching...")
        car_run(-150, 150, -150, 150, 150)
  
def car_run(qz_speed,qy_speed,hz_speed,hy_speed,time):
    bus_str = ('#006P{0:0>4d}T{4:0>4d}!#007P{1:0>4d}T{4:0>4d}!#008P{2:0>4d}T{4:0>4d}!#009P{3:0>4d}T{4:0>4d}!'
    .format(1500+qz_speed,1500-qy_speed,1500+hz_speed,1500-hy_speed,time))
    print(bus_str)                                                                                                                                                                
    myUart.uart_send_str(bus_str)

# 串口指令解析,智能转功能       
def parse_cmd(myStr):
    global ai_mode,color_str
    if myStr in run_dict:
        car_mode(myStr)
    if myStr in ai_dict:
        ai_mode = ai_dict[myStr]
        if ai_mode == 0 or ai_mode == 1:
            myCar.car_run(0,0,0,0,0) 
            pi.set_servo_pulsewidth(PIN_camera, 1500)
            pi.set_servo_pulsewidth(PIN_yuntai, 1500)
        elif ai_mode == 2:
            pi.set_servo_pulsewidth(PIN_camera, 2200)
            pi.set_servo_pulsewidth(PIN_yuntai, 1500)
        elif ai_mode == 3:
            pi.set_servo_pulsewidth(PIN_camera, 1000)
            pi.set_servo_pulsewidth(PIN_yuntai, 1500)
    if myStr in color_list:
        color_str = myStr[1:-1]
        
#摄像头上下转动    
def camera_up_down(speed):
    global systick_ms_bak,pwm_value2
    if(int((time.time() * 1000))- systick_ms_bak > 20):
        systick_ms_bak = int((time.time() * 1000))
        pi.set_servo_pulsewidth(PIN_camera, pwm_value2)
        pwm_value2 = pwm_value2 +speed//100
        if pwm_value2 > 2500:
            pwm_value2 = 2500
        if pwm_value2 < 500:
            pwm_value2 = 500
        print(pwm_value2)
        return

# 大循环
if __name__ == '__main__':
    myBeep.setup_beep()       # 蜂鸣器初始化
    myUart.setup_uart(115200) # 设置串口
     # 二维云台初始化
    pi.set_servo_pulsewidth(PIN_camera, 700)
    pi.set_servo_pulsewidth(PIN_yuntai, 1500)
    myUart.uart_send_str('#000P1300T1000!')
    time.sleep(1)
    cam = Camera.Camera()     # 摄像头库实例化    
    cam.camera_open()         # 打开摄像头
    frame = None
    myBeep.beep(3,0.1)        # 蜂鸣器响三声
    # 无限循环
    while 1:
        if cam.frame is not None:
            frame = cam.frame.copy()            
            car_xunji()
            cv2.imshow('roi', cv2.resize(roi, (960, 240)))
        # 如果按了ESC就退出 当然也可以自己设置
        if cv2.waitKey(5) & 0xFF == 27:
            break
    myUart.uart_send_str('#000P1500T1000!')
    cam.camera_close()
    cv2.destroyAllWindows()
