import argparse
import sys
from motor import MotorController
from drive import Drive

# # NOTE
#     #linux/mac 
#         tty, terminos
#     FOR WINDOWS CHECK (I use windows to debug so we can remove all os checks for win32 once base working on the pi)
#         msvcrt.getwch()

if sys.platform == "win32":
    import msvcrt
    def getKey():
        key = msvcrt.getwch()
        #win arrow keys = 2 bytes
        if key in ("\x00", "\xe0"):
            msvcrt.getwch() #eat 2nd byte ignored
            return ""
        return key
else:
    import tty, termios
    def getKey():
        # read inputs as raw keypress ie hold w keep forward let go = stop
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)

        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

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
            "x": drive.spinRight,
            "z": drive.spinLeft,
            " ": drive.stop,  # space
        }

        print("Robot ready")
        print("Movement: w = forward <> s = backward <> a = arc left <> d = arc right ~")
        print("Spin: z = leftSpin [&] x = rightSpin")
        print(f"Speed: {drive.speed} | Use '+' or '-' to adjust speed")
        print("Quit: q | Esc or Ctrl+c")
    
        try:   
            while True:

                cmd = getKey()

                #quit handles [\x03 = ctl+c], [\1xb = esc]
                if cmd in ("q", "\x03", "\x1b"):
                    print("\nQuitting...")
                    drive.stop()
                    print("Done!")
                    break

                elif cmd == "+":
                    drive.setSpeed(min(Drive.MAX_SPEED, drive.speed + 5))
            
                elif cmd == "-":
                    drive.setSpeed(max(1, drive.speed - 5))
            
                elif cmd in commands:
                    commands[cmd]()
            
                else:
                    #silent ignore raw unknown inp
                    pass
        except KeyboardInterrupt:
            print("\nInterrupted")
            drive.stop()

if __name__ == "__main__":
    main()