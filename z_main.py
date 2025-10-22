#!/usr/bin/python3
# -*- coding:utf-8 -*-
#导入模块
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  #'/home/Desktop/ZL-PI/'
import threading
import cv2
import time
import pigpio
import numpy as np
import Camera
import MjpgServer
from web_button_dict import *
# 导入flask框架所需要的包，模块
from flask import Flask, request, render_template, Response
from rpi_ws281x import Adafruit_NeoPixel, Color

import car_run as myCar
import ZL_SDK.z_led as myLed                   # 导入控制led灯的模块
import ZL_SDK.z_beep as myBeep                 # 导入控制有源蜂鸣器的模块
import ZL_SDK.Z_UartServer as myUart           # 导入串口收发数据的模块
import ZL_SDK.Z_lirc as myLirc

import AI_Functions.Color_Follow as CFollow    # 导入颜色跟随模块
import AI_Functions.Face_Follow as FFollow     # 导入人脸跟随模块
import AI_Functions.QRD_run as QRDrun          # 导入二维码标签交互模块
import AI_Functions.car_tracking as car_t   # 导入视觉寻迹模块

import Ultrasonic_sensor as myCsb
import Nterval_Follow as NF
import Obstacle_Avoidance as OA

# LED 配置:
LED_COUNT      = 9      # 要控制LED的数量.
LED_PIN        = 18      # GPIO接口 (PWM编码).
LED_BRIGHTNESS = 255    # 设置LED亮度 (0-255)
#以下LED配置无需修改
LED_FREQ_HZ    = 800000  # LED信号频率（以赫兹为单位）（通常为800khz）
LED_DMA        = 10       # 用于生成信号的DMA通道（尝试10）
LED_INVERT     = False   # 反转信号（使用NPN晶体管电平移位时）
#引脚定义
PIN_yuntai = 26
PIN_camera = 12

pwm_value1 = 1500
pwm_value2 = 1500


#类实例化
pi = pigpio.pi()
# 固定写法
app = Flask(__name__)

# 全局变量定义
ai_mode = 0
systick_ms_led = 0
systick_ms_bak = 0
webpage_get_ok = 0                             # 用于判断网页发送过来的数据格式    
webpage_receive_buf = ''                       # 用于接收保存网页发送过来的数据
response_mode_flag = 0                         # 渲染网页时要用到的机器人模式：0是遥控模式，1是智能模式



run_dict = {"$TZ!":0,"$QJ!":1,"$HT!":2,"$ZZ!":3,"$YZ!":4,
            "$ZXQY!":5,"$ZPY!":6,"$ZXHY!":7,
            "$YXQY!":8,"$YPY!":9,"$YXHY!":10   
            }

lirc_dist = {
            'POWER':'$FW!','+':'$QJ!','PREV':'$ZZ!','PLAY/STOP':'$TZ!','NEXT':'$YZ!','-':'$HT!',
            '1':'$ZYBZ!','2':'$GSMS!',
            }

ai_dict = {"$FW!":0,
           "$SJGS!":1,
           "$SJXJ!":2,
           "$RLSB!":3,
           "$GSMS!":4,
           "$ZYBZ!":5,
           "$CU!":6,
           "$CD!":7,
           "$CL!":8,
           "$CR!":9,
           "$TZ!":10
            }

# 要识别的颜色字典
color_dist = {
             'RED':   {'Lower': np.array([0, 80, 80]), 'Upper': np.array([10, 255, 255])},
             'GREEN': {'Lower': np.array([35, 43, 35]), 'Upper': np.array([90, 255, 255])},
             'BLUE':  {'Lower': np.array([90, 50, 50]), 'Upper': np.array([120, 255, 255])},
             'YELLOW':  {'Lower': np.array([20, 50, 50]), 'Upper': np.array([34, 255, 255])},
             }


color_list = ['$RED!','$GREEN!','$BLUE!','$YELLOW!']


color_str = color_list[1]
color_str = color_str[1:-1]

# 用于接收网页按钮和键盘按键发来的数据
self_cmd_text = None

# 进入的首个网页
@app.route('/', methods=['GET','POST'])
def webpage_main():
    global webpage_get_ok, webpage_receive_buf, response_mode_flag, self_cmd_text
    webpage_mode = 0
    if request.form.get('self_cmd_text'):
        self_cmd_text = request.form.get('self_cmd_text')
        if webpage_get_ok == 0:
            webpage_receive_buf = self_cmd_text
            uart_get_ok = 0
            if webpage_mode == 0:
                if webpage_receive_buf.find('{') >= 0:
                    webpage_mode = 1
                elif webpage_receive_buf.find('$') >= 0:
                    webpage_mode = 2
                elif webpage_receive_buf.find('#') >= 0:
                    webpage_mode = 3
            if webpage_mode == 1:
                if webpage_receive_buf.find('}') >= 0:
                    uart_get_ok = 1
                    webpage_mode = 0
            elif webpage_mode == 2:
                if webpage_receive_buf.find('!') >= 0:
                    uart_get_ok = 2
                    webpage_mode = 0
            elif webpage_mode == 3:
                if webpage_receive_buf.find('!') >= 0:
                    uart_get_ok = 3
                    webpage_mode = 0
            webpage_get_ok = uart_get_ok
            return "ok"     
    if request.form.get('webpage_func_mode') == webpage_func_mode_dict['webpage_mode']['remote_mode']:
        response_mode_flag = 0
    elif request.form.get('webpage_func_mode') == webpage_func_mode_dict['webpage_mode']['ai_mode']:
        response_mode_flag = 1
        
    if response_mode_flag:
        response_dict = webpage_func_mode_dict['webpage_ai_button_dict']
    else:
        response_dict = webpage_func_mode_dict['webpage_remote_button_dict']
    return render_template("index.html",response_dict=response_dict)   # 返回网页

# 要执行的flask线程函数
def flask_thread():
    app.run(host='192.168.12.1', port=8090)   # 该地址为树莓派的IP地址，端口任意设（也可以用本机的IP地址:127.0.0.2,port:8081）

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

def car_mode(myStr):
    car_mode = run_dict[myStr]
    run_time = 0
    if car_mode == 0:
        myCar.car_run(0,0,0,0,0)                         #停止
    elif car_mode == 1:
        myCar.car_run(600,600,600,600,run_time)          #前进
    elif car_mode == 2:
        myCar.car_run(-600,-600,-600,-600,run_time)      #后退
    elif car_mode == 3:
        myCar.car_run(-600,600,-600,600,run_time)        #左转
    elif car_mode == 4:
        myCar.car_run(600,-600,600,-600,run_time)        #右转
    elif car_mode == 5:
        myCar.car_run(0,600,600,0,run_time)              #左斜前移
    elif car_mode == 6:
        myCar.car_run(-600,600,600,-600,run_time)        #左平移
    elif car_mode == 7:
        myCar.car_run(-600,0,0,-600,run_time)            #左斜后退
    elif car_mode == 8:
        myCar.car_run(600,0,0,600,run_time)              #右斜前移
    elif car_mode == 9:
        myCar.car_run(600,-600,-600,600,run_time)        #右平移
    elif car_mode == 10:
        myCar.car_run(0,-600,-600,0,run_time)            #右斜后移
        
# LED灯循坏闪烁
def loop_led():
    global systick_ms_led
    if int((time.time() * 1000)) - systick_ms_led > 500:
        systick_ms_led = int((time.time() * 1000))
        myLed.flip()

# 对网页发过来的数据进行处理
def loop_webpage():
    global webpage_get_ok, webpage_receive_buf
    # 如果网页发送过来了数据
    if webpage_get_ok:
        #print(webpage_receive_buf)
        myUart.uart_get_ok = webpage_get_ok
        # 将网页数据赋值给串口数据处进行处理
        myUart.uart_receive_buf = webpage_receive_buf
        # 然后将网页接收数据赋值为空
        webpage_receive_buf = ''
        webpage_get_ok = 0

# 串口检测，串口接收数据之后进行的处理
def loop_uart():
    if myUart.uart_get_ok == 2:
        myBeep.beep(1, 0.1)
        parse_cmd(myUart.uart_receive_buf)
        myUart.uart_receive_buf = ''
        myUart.uart_get_ok = 0
    elif myUart.uart_get_ok == 1 or myUart.uart_get_ok == 3:
        myUart.uart_send_str(myUart.uart_receive_buf)
        myUart.uart_receive_buf = ''
        myUart.uart_get_ok = 0

def loop_ai_run():
    global frame,ai_mode,color_str
    if ai_mode == 0:
        QRDrun.frame = frame
        QRDrun.qrd_detect()
        frame = QRDrun.frame 
    elif ai_mode == 1:
        CFollow.frame = frame
        CFollow.color_follow(color_str)
        frame = CFollow.frame
    elif ai_mode == 2:
        car_t.frame = frame
        car_t.car_xunji()
        frame = car_t.frame
    elif ai_mode == 3:
        FFollow.frame = frame
        FFollow.face_follow()
        frame = FFollow.frame
    elif ai_mode == 4:
        NF.nterval_follow()
    elif ai_mode == 5:
        OA.obstacle_avoidance()
    elif ai_mode == 6:
        camera_up_down(-500)
    elif ai_mode == 7:
        camera_up_down(500)
    elif ai_mode == 8:
        camera_l_r(500)
    elif ai_mode == 9:
        camera_l_r(-500) 
  
#控制RGB灯亮起
def rgb_show(x):
    if x == 0:
        for i in range(0,strip.numPixels()):  
            strip.setPixelColor(i, Color(0,0,0))
            strip.show()
    elif x == 1:
        for i in range(0,strip.numPixels()):  
            strip.setPixelColor(i, Color(255,0,0))
            strip.show()
    elif x == 2:
        for i in range(0,strip.numPixels()):  
            strip.setPixelColor(i, Color(0,255,0))
            strip.show()
    elif x == 3:
        for i in range(0,strip.numPixels()):  
            strip.setPixelColor(i, Color(0,0,255))
            strip.show()

#开机RGB灯闪烁
def setup_show(): 
    rgb_show(1)
    time.sleep(1)
    rgb_show(2)
    time.sleep(2)
    rgb_show(3)
    time.sleep(2)   
    rgb_show(0)

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

#摄像头左右转动    
def camera_l_r(speed):
    global systick_ms_bak,pwm_value1
    if(int((time.time() * 1000))- systick_ms_bak > 20):
        systick_ms_bak = int((time.time() * 1000))        
        pi.set_servo_pulsewidth(PIN_yuntai, pwm_value1)
        pwm_value1 = pwm_value1 + speed//100
        if pwm_value1 > 2500:
            pwm_value1 = 2500
        if pwm_value1 < 500:
            pwm_value1 = 500
        print(pwm_value1)
        return 

def loop_lirc():
    global ai_mode
    myLirc.lircEvent()
    if myLirc.button_value in lirc_dist:
        myBeep.beep(1,0.1)
        myStr = lirc_dist[myLirc.button_value]
        parse_cmd(myStr)
        #print(group_Str)
        myLirc.button_value = ''

# 创建flask线程
flask_task = threading.Thread(target=flask_thread, args=())

# 程序入口
if __name__ == '__main__':
    time.sleep(5)               # 延时5秒
    myLed.setup_led()           # led初始化
    myBeep.setup_beep()         # 蜂鸣器初始化
    
    myCsb.setup_sensor(23,22)   # 初始化超声波
    myUart.setup_uart(115200)   # 设置串口
    threading.Thread(target=MjpgServer.startMjpgServer,
                     daemon=True).start()  # mjpg流服务器
    frame = None
    loading_picture = cv2.imread('/home/pi/Desktop/ZL-PI/loading.jpg')
    cam = Camera.Camera()       # 相机读取
    cam.camera_open()           # 打开摄像头  
    flask_task.start()          # 开启flask线程
    # 创建NeoPixel对象
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # 初始化库
    strip.begin()
    setup_show()
    # 二维云台初始化
    pi.set_servo_pulsewidth(PIN_camera, 1500)
    pi.set_servo_pulsewidth(PIN_yuntai, 1500)
    
    myBeep.beep(3, 0.1)         # 发出哔哔哔作为开机声音
    # 异常处理
    try:
        while 1:                # 无限循环
            if cam.frame is not None:
                frame = cam.frame.copy()
                loop_ai_run()
                MjpgServer.img_show = frame
            else:
                MjpgServer.img_show = loading_picture
            loop_led()
            loop_uart()
            loop_lirc()
            loop_webpage()      # 对网页发送过来的数据进行处理       
    except KeyboardInterrupt:
        cam.camera_close()
        cv2.destroyAllWindows()
