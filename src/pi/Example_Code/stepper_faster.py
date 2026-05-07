import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

DIR_PIN = 5
STEP_PIN = 6

GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)

# motor settings
microsteps = 1          # try 1 first for max torque
steps_per_rev = 200 * microsteps

# speed control (tweak these)
min_delay = 0.0005      # fastest speed (high RPM)
max_delay = 0.003       # slow start (high torque)

def step_motor(step_count, direction):
    GPIO.output(DIR_PIN, direction)

    # acceleration up
    for i in range(step_count):
        # exponential-ish ramp down delay
        progress = i / step_count
        delay = max_delay - (max_delay - min_delay) * progress

        GPIO.output(STEP_PIN, True)
        time.sleep(delay)
        GPIO.output(STEP_PIN, False)
        time.sleep(delay)

try:
    while True:
        print("forward")
        step_motor(steps_per_rev, True)

        time.sleep(0.5)

        print("reverse")
        step_motor(steps_per_rev, False)

        time.sleep(0.5)

except KeyboardInterrupt:
    GPIO.cleanup()