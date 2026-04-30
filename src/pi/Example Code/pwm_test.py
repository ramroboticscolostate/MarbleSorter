from machine import Pin, PWM
import time

# Create a PWM object on pin 4
pwm = PWM(Pin(4))

# Set frequency to 1000 Hz
pwm.freq(1000)

# Test: gradually increase and decrease brightness
while True:
    # Fade in
    for duty in range(0, 65536, 1000):
        pwm.duty_u16(duty)
        time.sleep(0.01)
    
    # Fade out
    for duty in range(65536, 0, -1000):
        pwm.duty_u16(duty)
        time.sleep(0.01)
