#include <Bluepad32.h>
#include <ESP32Servo.h>


// ========= Sabertooth pins =========
const int ST_leftPin  = 15;  // S1: LEFT motor
const int ST_rightPin = 14;  // S2: RIGHT motor

// ========= Ultrasonic pins =========
const int ULTRASONIC_TRIG_PIN = 4;  // TRIG
const int ULTRASONIC_ECHO_PIN = 5;  // ECHO

// ========= Indicators =========
const int BRAKE_LED_PIN = 27;       // Brake LED
const int BUZZER_PIN    = 26;       // Buzzer (honk on X)

Servo leftServo;
Servo rightServo;

ControllerPtr myControllers[BP32_MAX_GAMEPADS];

float lastDistanceCm = -1.0f;
bool obstacleAhead = false;
bool ultrasonicEnabled = true;   // toggled by A button

// ========= Helper: set both motors to STOP =========
void setMotorsNeutral() {
  // 90° => 1500 us pulse => STOP in Sabertooth RC mode
  leftServo.write(90);
  rightServo.write(90);
}

// ========= Ultrasonic distance (cm) =========
float readDistanceCm() {
  // Trigger pulse
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);

  // Echo read with timeout (25 ms -> ~4+ m)
  unsigned long duration = pulseIn(ULTRASONIC_ECHO_PIN, HIGH, 25000);

  if (duration == 0) {
    return -1.0f;  // no echo
  }

  float distanceCm = duration / 58.0f;  // HC-SR04 formula
  return distanceCm;
}

// ========= Bluepad32 callbacks =========
void onConnectedController(ControllerPtr ctl) {
  for (int i = 0; i < BP32_MAX_GAMEPADS; i++) {
    if (myControllers[i] == nullptr) {
      Serial.printf("Controller connected: index=%d\n", i);
      myControllers[i] = ctl;
      return;
    }
  }
  Serial.println("No empty controller slots available");
}

void onDisconnectedController(ControllerPtr ctl) {
  for (int i = 0; i < BP32_MAX_GAMEPADS; i++) {
    if (myControllers[i] == ctl) {
      Serial.printf("Controller disconnected: index=%d\n", i);
      myControllers[i] = nullptr;
      return;
    }
  }
}

// ========= Tank drive logic =========
void processGamepad(ControllerPtr ctl) {
  // --- A button toggles ultrasonic on/off ---
  static bool prevA = false;
  bool currA = ctl->a();

  if (currA && !prevA) {  // rising edge
    ultrasonicEnabled = !ultrasonicEnabled;
    Serial.printf("Ultrasonic %s\n", ultrasonicEnabled ? "ENABLED" : "DISABLED");
  }
  prevA = currA;

  // --- X button = honk buzzer ---
  if (ctl->x()) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }

  // Left stick vertical = forward/back
  int ly = ctl->axisY();   // ~ -512 (up) to +512 (down)
  // Right stick horizontal = turn control
  int rx = ctl->axisRX();  // ~ -512 (left) to +512 (right)

  const int deadzoneMove = 40;
  const int deadzoneTurn = 80;

  // Apply deadzone for movement
  if (abs(ly) < deadzoneMove) {
    ly = 0;
  }

  bool turningRight = (rx >  deadzoneTurn);
  bool turningLeft  = (rx < -deadzoneTurn);

  // Convert ly to -1..1, up = +1
  float fwd = -(float)ly / 512.0f;
  if (fwd >  1.0f) fwd =  1.0f;
  if (fwd < -1.0f) fwd = -1.0f;

  // ====== OBSTACLE RULE (only if ultrasonic enabled) ======
  if (ultrasonicEnabled && obstacleAhead && fwd > 0.0f) {
    // Trying to go forward into an obstacle: block forward
    fwd = 0.0f;
    digitalWrite(BRAKE_LED_PIN, HIGH);   // show "blocking" with LED
  } else {
    digitalWrite(BRAKE_LED_PIN, LOW);
  }

  auto cmdFromFwd = [](float f) -> int {
    if (f >  1.0f) f =  1.0f;
    if (f < -1.0f) f = -1.0f;
    int angle = (int)(90.0f + f * 90.0f);  // -1..1 -> 0..180 (90=stop)
    if (angle < 0)   angle = 0;
    if (angle > 180) angle = 180;
    return angle;
  };

  int leftOut  = 90;
  int rightOut = 90;

  if (ly == 0 && !turningLeft && !turningRight) {
    // Sticks centered -> full stop
    leftOut  = 90;
    rightOut = 90;
  } else if (turningRight) {
    // Turn right: stop RIGHT motor, move LEFT
    leftOut  = cmdFromFwd(fwd);
    rightOut = 90;
  } else if (turningLeft) {
    // Turn left: stop LEFT motor, move RIGHT
    leftOut  = 90;
    rightOut = cmdFromFwd(fwd);
  } else {
    // No strong turn: drive both wheels together
    leftOut  = cmdFromFwd(fwd);
    rightOut = cmdFromFwd(fwd);
  }

  leftServo.write(leftOut);
  rightServo.write(rightOut);

  Serial.printf("LY:%4d RX:%4d fwd:%.2f L:%3d R:%3d  dist:%.1f cm  obstacle:%d  ultra:%d\n",
                ly, rx, fwd, leftOut, rightOut,
                lastDistanceCm, obstacleAhead ? 1 : 0, ultrasonicEnabled ? 1 : 0);
}

// ========= Process all controllers =========
void processControllers() {
  bool anyConnected = false;

  for (auto ctl : myControllers) {
    if (ctl && ctl->isConnected()) {
      anyConnected = true;
      processGamepad(ctl);
    }
  }

  if (!anyConnected) {
    setMotorsNeutral();
    digitalWrite(BRAKE_LED_PIN, LOW);
    digitalWrite(BUZZER_PIN, LOW);
  }
}

// ========= Setup =========
void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 + Sabertooth + Ultrasonic (A toggle) + Buzzer (X)");

  // Bluepad32
  BP32.setup(&onConnectedController, &onDisconnectedController);

  // Sabertooth outputs
  leftServo.attach(ST_leftPin, 1000, 2000);
  rightServo.attach(ST_rightPin, 1000, 2000);
  setMotorsNeutral();

  // Ultrasonic pins
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);

  // Indicators
  pinMode(BRAKE_LED_PIN, OUTPUT);
  digitalWrite(BRAKE_LED_PIN, LOW);

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
}

// ========= Main loop =========
void loop() {
  BP32.update();

  // Read distance only if ultrasonic is enabled
  if (ultrasonicEnabled) {
    float d = readDistanceCm();
    lastDistanceCm = d;

    // Obstacle if valid reading and <= 60 cm (~2 ft)
    if (d > 0 && d <= 60.0f) {
      obstacleAhead = true;
    } else {
      obstacleAhead = false;
    }
  } else {
    // Ultrasonic disabled: ignore obstacle logic
    lastDistanceCm = -1.0f;
    obstacleAhead = false;
  }

  // Drive with controller
  processControllers();

  delay(20);  // ~50 Hz
}
