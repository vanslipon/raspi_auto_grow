#!/usr/bin/env python3

'''
Script to run a humidity sensor and a 5 volts water pump

Note:
Have to set pin to "IN", since taking away 3,3V (from raspi),
it isn't enough to turn off the relays with setting pin to LOW
'''

import RPi.GPIO as gp
import time
from datetime import datetime
from multiprocessing import Process
import rag_telegram_bot as rtb


# Pins used for water pump and humidity sensor
PUMP_PIN = 18
HUMID_SENS_PIN = 21
HUMID_SENS_RELAY_PIN = 26

# Check interval time in seconds
CHECK_INTERVAL_IN_SECONDS = 10
# How long the water pump will pump in one run in seconds
PUMP_TIME = 10

# Variable to monitor sensor dying
watered_in_row = 0
# When watered in row >, warning will be triggered
WARNING_THRESHOLD = 5
# When watered_in_row >, script is turned off
ERROR_THRESHOLD = 10

# Setting up the pins
gp.setmode(gp.BCM)
gp.setup(HUMID_SENS_PIN, gp.IN)
gp.setup(HUMID_SENS_RELAY_PIN, gp.IN)


def soil_is_dry():
    '''Checks if the soil is dry or moist.

    Returns:
        boolean -- True if dry, else False
    '''
    # Activating humidity sensor relay
    gp.setup(HUMID_SENS_RELAY_PIN, gp.OUT)
    gp.output(HUMID_SENS_RELAY_PIN, gp.HIGH)
    time.sleep(0.5)
    # Reading sensor pin
    humid = gp.input(HUMID_SENS_PIN)
    # Deactivating humidity sensor relay to take away voltage
    # from sensor
    gp.setup(HUMID_SENS_RELAY_PIN, gp.IN)
    return humid


def run_pump():
    '''Activating the water pump for `PUMP_TIME` seconds.
    '''
    # Activating pump (HIGH / LOW is not enough for 5v relays)
    gp.setup(PUMP_PIN, gp.OUT)
    gp.output(PUMP_PIN, gp.HIGH)
    # Waiting for water to flow
    time.sleep(PUMP_TIME)
    # Deactivating pump
    gp.setup(PUMP_PIN, gp.IN)


if __name__ == '__main__':
    p = Process(target=rtb.start_tb_listener())
    p.run()
    while(True):
        if watered_in_row < ERROR_THRESHOLD:
            if soil_is_dry():
                watered_in_row += 1
                if watered_in_row < WARNING_THRESHOLD:
                    log_str = str(datetime.now()) + \
                        ' Soil seems to be dry, watering the plant now.'
                else:
                    log_str = str(datetime.now()) + \
                        ' Soil seems to be dry, watering the plant now.\n' + \
                        '[WARNING] Watered' + str(watered_in_row) + \
                        'times in a row, humidity sensor might be defect!'
                run_pump()
            else:
                watered_in_row = 0
                log_str = str(datetime.now()) + \
                    ' Soil seems to be humid, won\'t water the plant.'
        else:
            log_str = str(datetime.now()) + ' [ERROR] Watered' + \
                str(watered_in_row) + \
                'times in a row, humidity sensor seems to be defect!'
        print(log_str)
        rtb.send_message(log_str)
        time.sleep(CHECK_INTERVAL_IN_SECONDS)
