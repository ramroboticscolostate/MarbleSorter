from motor import MotorController
from drive import Drive

motor = MotorController()
drive = Drive(motor)

commands = {
    "w": drive.forward,
    "s": drive.backward,
    "a": drive.left,
    "d": drive.right,
    " ": drive.stop,  # space
    "q": drive.stop
}

print("Robot ready")
print("Commands: w s a d (space stop) q quit")

while True:

    cmd = input("> ").strip().lower()

    if cmd in commands:
        commands[cmd]()

        if cmd == "q":
            break

    else:
        print("Unknown command")