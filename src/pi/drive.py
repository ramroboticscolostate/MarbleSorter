class Drive:

    def __init__(self, motor):

        self.motor = motor
        self.speed = 30 # may need to adjust this based on the actual robot and motor capabilities

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