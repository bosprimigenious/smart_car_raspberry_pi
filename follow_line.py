#!/usr/bin/python
# -*- coding: UTF-8 -*-

import RPi.GPIO as GPIO
import time
import sys

sys.path.append("/home/pi/Desktop/ZL-PI/")
import ZL_SDK.Z_UartServer as myUart


# 初始化GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# 红外传感器引脚（单传感器）
IR_PIN =11  # GPIO引脚号

# 电机控制参数
TURN_SPEED = 500
TURN_TIME = 200  # ms
BACK_TIME = 100  # ms


def init():
    GPIO.setup(IR_PIN, GPIO.IN)


def get_ir_value():

    return GPIO.input(IR_PIN)


def car_run(speed_l1, speed_r1, speed_l2, speed_r2, run_time):
    """控制小车运动"""
    cmd = "#006P{0:0>4d}T{4:0>4d}!#007P{1:0>4d}T{4:0>4d}!#008P{2:0>4d}T{4:0>4d}!#009P{3:0>4d}T{4:0>4d}!".format(
        1500 + speed_l1, 1500 - speed_r1, 1500 + speed_l2, 1500 - speed_r2, run_time
    )
    myUart.uart_send_str(cmd)
    time.sleep(run_time / 1000.0)


def follow_line():
    """循迹主逻辑"""
print(value)

def follow_line():
    """循迹主逻辑"""
    try:
        init()
        myUart.setup_uart(115200)

        print("输入w开始小车运行")
        start_input = input().strip().lower()

        if start_input == "w":
            print("开始循迹... (按Ctrl+C停止)")

            while True:
                ir_value = get_ir_value()

                if ir_value == 0:  # 检测到黑胶线边缘
                    # 沿着黑胶线左侧走 - 向右微调
                    car_run(300, 300 + 100, 300, 300 + 100, 50)
                    time.sleep( 0.01)  
                    car_run(300, 300 + 100, 300, 300 + 100, 50)
                else:  # 检测到瓷砖
                    # 沿着黑胶线右侧走 - 向左微调
                    car_run(300 + 100, 300, 300 + 100, 300, 50)
                    time.sleep( 0.01)  
                    car_run(300 + 100, 300, 300 + 100, 300, 50)
    except KeyboardInterrupt:
        lym_carrun.destroy()
        GPIO.cleanup()
        print("循迹结束")


if __name__ == "__main__":
    follow_line()
