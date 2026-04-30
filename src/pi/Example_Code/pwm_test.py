from gpiozero import PWMLED
from signal import pause
import time

# Create a PWM LED on GPIO pin 4
led = PWMLED(4)

# Test: gradually increase and decrease brightness
try:
    while True:
        # Fade in
        for brightness in range(0, 101):
            led.value = brightness / 100
            time.sleep(0.01)
        
        # Fade out
        for brightness in range(100, -1, -1):
            led.value = brightness / 100
            time.sleep(0.01)
except KeyboardInterrupt:
    led.off()
    print("LED test stopped")
