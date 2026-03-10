class Drive:

    MAX_SPEED = 63  #unknown exact going off other docs

    def __init__(self, motor, speed: int =30):

        self.motor = motor
        self.speed = speed # can adjust at runtime with set_speed() use and cmd input

    def setSpeed(self, speed: int):

        if not 1 <= speed <= self.MAX_SPEED:
            raise ValueError(f"Speed must be between 1 and {self.MAX_SPEED}, got{speed}")
        self.speed = speed
        print(f"Speed is set to {self.speed}")
        
    def forward(self):

        self.motor.drive(self.speed, self.speed)

    def backward(self):

        self.motor.drive(-self.speed, -self.speed)

    def left(self):

        self.motor.drive(-self.speed, self.speed)

    def right(self):

        self.motor.drive(self.speed, -self.speed)

    def stop(self):

        self.motor.stop()