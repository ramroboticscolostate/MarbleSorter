import board # type: ignore
import busio  # type: ignore
import adafruit_apds9960.apds9960 # type: ignore
import pwmio # type: ignore
import time

i2c = busio.I2C(scl=board.GP5, sda=board.GP4)
sensor = adafruit_apds9960.apds9960.APDS9960(i2c)
sensor.enable_color = True
sensor.enable_proximity = True

def rgb_to_hue(r, g, b):
    """Convert RGB (0-255) to hue (0-360 degrees)"""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    diff = max_c - min_c

    sat = 0 if max_c == 0 else diff / max_c *100
    val = max_c * 100
    
    if diff == 0:
        return 0
    
    if max_c == r:
        hue = 60 * (((g - b) / diff) % 6)
    elif max_c == g:
        hue = 60 * (((b - r) / diff) + 2)
    else:
        hue = 60 * (((r - g) / diff) + 4)
    

    print('HSV: ({:.2f}, {:.2f}%, {:.2f}%)'.format(hue, sat, val))
    return abs(hue) , abs(sat), abs(val)

def get_color_name(r, g, b):
    """Get color name from RGB using HSL hue"""
    hue, sat, val = rgb_to_hue(r, g, b) # type: ignore
    
    # Define color ranges based on hue
    if hue < 50 or hue >= 345:
        return "Red"
    elif 50 <= hue < 175:
        return "Green"
    elif 175 <= hue < 270:
        return "Blue"
    elif 270 <= hue < 345:
        return "Pink"
    return "Unknown"

print("Ready - hold a marble in front of the sensor")


# Set up PWM on 3 pins
r_PIN = pwmio.PWMOut(board.GP9, frequency=1000)
g_PIN = pwmio.PWMOut(board.GP11, frequency=1000)
b_PIN = pwmio.PWMOut(board.GP14, frequency=1000)

# Set PWM frequency
# for led in (r_PIN, g_PIN, b_PIN):
#     led.freq(1000)

# Function to set color (0–65535)
def set_color(r, g, b):
    r_PIN.duty_cycle = r
    g_PIN.duty_cycle = g
    b_PIN.duty_cycle = b

count = 10
while True:
    while sensor.proximity > 50:
        time.sleep(0.3)
        
        # Take average of 10 readings
        r_total, g_total, b_total = 0, 0, 0
        for i in range(count+4):
            r, g, b, c = sensor.color_data
            
            if i >= 4:  # Skip first 4 readings
                print('R:{:.2f} G:{:.2f} B:{:.2f} C:{:.2f}'.format(r, g, b, c))
                r_total += r
                g_total += g
                b_total += b
            else:
                print('skipped -- R:{:.2f} G:{:.2f} B:{:.2f} C:{:.2f}'.format(r, g, b, c))
            time.sleep(0.3)
        
        r = r_total / count
        g = g_total / count
        b = b_total / count

        print('avg - R:{:.2f} G:{:.2f} B:{:.2f} C:{:.2f}'.format(r, g, b, c))
        
        rgb_max = max(r, g, b)

        rn = int(r / rgb_max * 255)
        gn = int(g / rgb_max * 255)
        bn = int(b / rgb_max * 255)

        color = get_color_name(rn, gn, bn)
            
        print('Color: {} | RGB:({:d}, {:d}, {:d})'.format(color, rn, gn, bn))

        set_color(rn * 257, gn * 257, bn * 257)  # Scale 0-255 to 0-65535

        while sensor.proximity > 50:
            time.sleep(0.1)
        print("NEXT:")