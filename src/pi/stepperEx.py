# SPDX-FileCopyrightText: 2024 Liz Clark for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import time
import RPi.GPIO as GPIO

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

DIR_PIN = 5   # D5 = BCM 5
STEP_PIN = 6  # D6 = BCM 6

GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)

microMode = 16
steps = 200 * microMode

try:
    while True:
        GPIO.output(DIR_PIN, not GPIO.input(DIR_PIN))  # toggle direction
        for i in range(steps):
            GPIO.output(STEP_PIN, True)
            time.sleep(0.001)
            GPIO.output(STEP_PIN, False)
            time.sleep(0.001)
        print("rotated! now reverse")
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()