import argparse
from motor import MotorController, find_sabertooth_port
from drive import Drive


def main():

    parser = argparse.ArgumentParser(description="Robot keyboard controller")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode (no hardware)")
    parser.add_argument("--speed", type=int, default=30, help="Drive speed 1-63 (default: 30)")
    parser.add_argument("--port", type=str, default=None, help="Serial port (e.g. /dev/ttyUSB0, COM3)")
    parser.add_argument("--list-ports", action="store_true", help="List available serial ports and exit")
    args = parser.parse_args()

    if args.list_ports:
        try:
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            if ports:
                print("Available serial ports:")
                for p in ports:
                    print(f"  {p.device}: {p.description}")
                detected = find_sabertooth_port()
                if detected:
                    print(f"\nAuto-detect would pick: {detected}")
            else:
                print("No serial ports found")
        except ImportError:
            print("pyserial not installed // pip install pyserial")
        return

    with MotorController(mock=args.mock, port=args.port) as motor:
        drive = Drive(motor, speed=args.speed)

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
