class Drive:

    MAX_SPEED = 63

    def __init__(self, motor, speed: int = 30):
        self.motor = motor
        self.speed = speed

    def set_speed(self, speed: int):
        if not 1 <= speed <= self.MAX_SPEED:
            raise ValueError(f"Speed must be between 1 and {self.MAX_SPEED}, got {speed}")
        self.speed = speed
        print(f"Speed: {self.speed}")

    def forward(self):
        self.motor.drive(self.speed, self.speed)

    def backward(self):
        self.motor.drive(-self.speed, -self.speed)

    def left(self):
        self.motor.drive(self.speed // 2, self.speed)

    def right(self):
        self.motor.drive(self.speed, self.speed // 2)

    def spinLeft(self):
        self.motor.drive(-self.speed, self.speed)

    def spinRight(self):
        self.motor.drive(self.speed, -self.speed)
        
    def stop(self):
        self.motor.stop()
