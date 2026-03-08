


// Declare the pins
const byte en_pin = D0;
const byte dir_pin = D7;
const byte step_pin = D8;
const byte ms1_pin = D10;
const byte ms2_pin = D9;

const byte upper_limit_pin = D5;
const byte lower_limit_pin = D6;

const byte status_led_pin = D4;


// Declare flags
bool is_at_limit = false;
bool is_homed = false;


// Declare variables needed for operation
float speed = 10;       // mm/s
const float pitch = 2;  // mm/rev
float current_position; // mm
unsigned long step_count = 0;



void setup() {

    // Set the pin modes
    pinMode(en_pin, OUTPUT);
    pinMode(dir_pin, OUTPUT);
    pinMode(step_pin, OUTPUT);
    pinMode(ms1_pin, OUTPUT);
    pinMode(ms2_pin, OUTPUT);

    pinMode(upper_limit_pin, INPUT_PULLUP);
    pinMode(lower_limit_pin, INPUT_PULLUP);

    pinMode(status_led_pin, OUTPUT);

    // Initialize pin values
    digitalWrite(en_pin, HIGH);
    digitalWrite(ms1_pin, LOW);
    digitalWrite(ms2_pin, LOW);
    digitalWrite(en_pin, HIGH);


    // Open the serial communication to the laptop
    Serial.begin(115200);
    while(!Serial);

    




}


void loop() {


}