#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
sys.path.append('/home/pi/Desktop/ZL-PI/')
import os
import serial
import time
import threading
import ZL_SDK.Z_UartServer as myUart
import time




myUart.setup_uart(115200)

def car_run(speed_l1,speed_r1,speed_l2,speed_r2,time):
    textSrt = '#006P{0:0>4d}T{4:0>4d}!#007P{1:0>4d}T{4:0>4d}!#008P{2:0>4d}T{4:0>4d}!#009P{3:0>4d}T{4:0>4d}!'.format(1500+speed_l1,1500-speed_r1,1500+speed_l2,1500-speed_r2,time)
    myUart.uart_send_str(textSrt)
car_run(-400,400,-400,400,2000)
time.sleep(1)
myUart.uart_send_str('#006P1500T1000!#007P1500T1000!#008P1500T1000!#009P1500T1000!')

