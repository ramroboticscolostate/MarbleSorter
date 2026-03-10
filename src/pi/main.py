import argparse
from motor import MotorController
from drive import Drive


def main():

    parser = argparse.ArgumentParser(description="Robot keyboard controller")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode (no hardware)")
    parser.add_argument("--speed", type=int, default=30, help="Drive speed 1-63 (default: 30)")
    args = parser.parse_args()

    with MotorController(mock=args.mock) as motor:
        drive = Drive(motor, speed= args.speed)

        commands = {
        "w": drive.forward,
        "s": drive.backward,
        "a": drive.left,
        "d": drive.right,
        " ": drive.stop,  # space
        }

        print("Robot ready")
        print("Commands: w s a d (space stop) q quit")
        print(f"Speed: {drive.speed} | Use '+' or '-' to adjust speed")
    
        try:   
            while True:

                cmd = input("> ").lower()
                if cmd == "q":
                    break
                elif cmd == "+":
                    drive.setSpeed(min(Drive.MAX_SPEED, drive.speed + 5))
            
                elif cmd == "-":
                    drive.setSpeed(max(1, drive.speed - 5))
            
                elif cmd in commands:
                    commands[cmd]()
            
                else:
                    print("Unknown command")
        except KeyboardInterrupt:
            print("\nInterrupted")

if __name__ == "__main__":
    main()