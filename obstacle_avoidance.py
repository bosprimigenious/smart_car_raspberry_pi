#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
sys.path.append('/home/pi/Desktop/ZL-PI/')
import os
import serial
import time
import threading
import ZL_SDK.Z_UartServer as myUart
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
import time
import time

count = None
control = None
dis = None

def text_prompt(msg):
  try:
    return raw_input(msg)
  except NameError:
    return input(msg)

def distance():
    global TRIG, ECHO
    GPIO.output(TRIG, 0)
    time.sleep(0.000002)
    GPIO.output(TRIG, 1)
    time.sleep(0.00001)
    GPIO.output(TRIG, 0)
    while GPIO.input(ECHO) == 0:
        pass
    time1 = time.time()
    while GPIO.input(ECHO) == 1:
        pass
    time2 = time.time()
    during = time2 - time1
    dis = during * 340 / 2 * 100
    if dis > 999:
        return 500
    return dis




myUart.setup_uart(115200)

def car_run(speed_l1,speed_r1,speed_l2,speed_r2,time):
    textSRT ='#006P{0:0>4d}T{4:0>4d}!#007P{1:0>4d}T{4:0>4d}!#008P{2:0>4d}T{4:0>4d}!#009P{3:0>4d}T{4:0>4d}!'.format(1500+speed_l1,1500-speed_r1,1500+speed_l2,1500-speed_r2, time)    
    myUart.uart_send_str(textSrt)

def setup_sensor(TRIG_PIN, ECHO_PIN):
    global TRIG, ECHO
    TRIG = TRIG_PIN
    ECHO = ECHO_PIN
    GPIO.setup(TRIG, GPIO.OUT, initial=0)
    GPIO.setup(ECHO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

setup_sensor(23, 22)
count = 0
control = text_prompt('please input "w" to make car run')
while control == 'w':
  while count < 3:
    dis = distance()
    car_run(400,400,400,400,1000)
    if dis < 20:
      count = count + 1
      if count != 3:
        car_run(-600,600,-600,600,450)
        time.sleep(1000/1000)
      else:
        myUart.uart_send_str('#006P1500T1000!#007P1500T1000!#008P1500T1000!#009P1500T1000!')
        time.sleep(1000/1000)

