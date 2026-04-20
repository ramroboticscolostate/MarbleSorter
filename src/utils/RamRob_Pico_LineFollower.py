from machine import Pin, PWM
import time
from ssd1327 import WS_OLED_128X128
from machine import I2C

#Setup I2C Communication - Only needed for OLED visualization
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=int(40E5))
oled = WS_OLED_128X128(i2c, addr=0x3D)
oled.fill(0)

#OLED Monitor - only needed for OLED visualization
class OLEDMonitor:
    
    def __init__(self, oled):
        self.oled = oled
        
    def update(self, L, R, error, correction):
        self.oled.fill(0)
        self.oled.text("LINE FOLLOW DEBUG",5,5,15)
        self.oled.text("Left: {}".format(L),5,30,12)
        self.oled.text("Right: {}".format(R),5,45,12)
        self.oled.text("Error: {:.2f}".format(error),5,65,10)
        
        self.oled.text("Corr: {:.2f}".format(correction),5,80,10)
        
        self.oled.show()

#Setup LineSensor object
class LineSensor:
        #sets up structure for pin inputs
        def __init__(self, left_pin, right_pin):
            self.left = Pin(left_pin, Pin.IN)
            self.right = Pin(right_pin, Pin.IN)
        #sets up structure for reading values from pins and storing 
        def read(self):
            L = self.left.value()
            R = self.right.value()
            return L, R
        #sets up error
        #this compares the left and right values of the linesensor so robot
            #knows if it needs to turn R or L to center itself on the line
        def error(self):
            L, R = self.read()
            return R - L

#Setup controller object
class PDController:
    #sets up variables that will be inputted and tuned later
    def __init__(self, kp, kd):
        self.kp = kp
        self.kd = kd
        self.last_error = 0
        
    #sets up computation for controller function
    def compute(self, error):
        derivative = error - self.last_error
        correction = self.kp*error + self.kd*derivative
        self.last_error = error
        return correction

#Setup driver object
class MotorDriver:
    def __init__(self):
        # TODO: Initialize PWM pins for motor controller and remove pass
        pass
    
    #setup speeds and factor in correction
    def drive(self, correction):
        left_speed = 0.5 - correction
        right_speed = 0.5 + correction
        
        # Clamp speeds to [0.0, 1.0] 
        left_speed = max(0.0, min(1.0, left_speed))
        right_speed = max(0.0, min(1.0, right_speed))

        # TODO: Write speeds to motor controller output

        print("L:", left_speed, "R:", right_speed) #just visualization
    
#setup full robot object ("blueprint")
class Robot:
    
    #will be used to tell object where to find all of the components (pins)
    def __init__(self, sensor, controller, motors):
        
        self.sensor = sensor
        self.controller = controller
        self.motors = motors
        
    #robot update function - this is how the robot will continuously control itself
    def update(self):
        
        L,R = self.sensor.read()
        
        error = R - L
        
        correction = self.controller.compute(error)
        
        self.motors.drive(correction)
        
        return L,R,error,correction
    
# - - - Initialization - - - #

sensor = LineSensor(14,15)
controller = PDController(0.6,0.3)
motors = MotorDriver()
robot = Robot(sensor,controller,motors)
monitor = OLEDMonitor(oled)

# - - - Main Loop - - - #

while True:
    
    L,R,error,correction = robot.update()
    
    monitor.update(L,R,error,correction)
    
    time.sleep(0.05)

