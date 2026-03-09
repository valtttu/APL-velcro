// Declare the hardware pins
const byte dir_pin = 7;
const byte step_pin = 8;

const byte ms1_pin = 9;
const byte ms2_pin = 10;

const byte ls1_pin = 5;
const byte ls2_pin = 6;

const byte enable = 0;

const byte led_pin = 4;


// Variables needed for driving the stepper
long target_count = 0;
long step_counter = 0;
int step_delay = 20;          // us
const float pitch = 2.0;      // mm/rev
const int steps_in_rev = 200; // steps/rev
int micro_steps = 64;          // steps/step
bool dir = true;
bool is_homed = false;
bool is_moving = false;
int homing_step_delay = 30;
bool lower_limit = false;
bool upper_limit = false;


// Variables for the control states
enum command {MOVE, STOP, SVEL, QSTATE, HOME, NONE};
command next_cmd = NONE;
float command_arg = 0;
int drive_cycle_duration = 2e5;


void setup() {
  // put your setup code here, to run once:

  pinMode(dir_pin, OUTPUT);
  pinMode(step_pin, OUTPUT);
  pinMode(enable, OUTPUT);
  pinMode(ms1_pin, OUTPUT);
  pinMode(ms2_pin, OUTPUT);

  pinMode(ls1_pin, INPUT_PULLUP);
  pinMode(ls2_pin, INPUT_PULLUP);

  digitalWrite(enable, LOW);
  digitalWrite(ms1_pin, HIGH);
  digitalWrite(ms2_pin, LOW);

  digitalWrite(dir_pin, LOW);

  Serial.begin(115200);

  while(!Serial);

  Serial.println("Successfully opened the conenction to XIOA");

}

void loop() {
  
  // Check for new commands
  if (Serial.available()) {
    next_cmd = parse_serial();
  } else {
    next_cmd = NONE;
  }

  // Perform action according to the command
  if(next_cmd == MOVE){
    Serial.println("Move started");
    is_moving = true;
    target_count = pos_to_steps(command_arg);
  } else if(next_cmd == STOP){
    Serial.println("Stopping");
    is_moving = false;
    target_count = step_counter;
  } else if(next_cmd == SVEL){
    Serial.println("Updating velocity");
    step_delay = vel_to_delay(command_arg);;
  } else if(next_cmd == QSTATE){
    send_state();
  } else if(next_cmd == HOME){
    Serial.println("Homing started");
    home_stage();
  }


  // Advance the steps or print move finished
  if(target_count != step_counter){
    int max_steps = drive_cycle_duration/step_delay;
    int diff = target_count - step_counter;
    int steps_to_go = min(max_steps, abs(diff));
    if(diff > 0)
      drive_stepper(steps_to_go, true);
    else
      drive_stepper(steps_to_go, false);
  } else if(is_moving) {
    Serial.println("Move finished");
    is_moving = false;
  }

}

//************* Function for parsing commands ***************************//
command parse_serial(){

  // Read until newline
  String input1 = Serial.readStringUntil('\n');  
  input1.toLowerCase();
  
  if(input1.indexOf("move") >= 0){
    if(input1.indexOf(" ") > 0){
      int idx = input1.indexOf(" ");
      String input2 = "";
      for(int i = idx; i < input1.length(); i++){
        input2 = input2 + input1[i];
      }
      command_arg = input2.toFloat();
      return MOVE;
    }
  } else if(input1.indexOf("stop") >= 0){
    return STOP;
  } else if(input1.indexOf("svel") >= 0){
    if(input1.indexOf(" ") > 0){
      int idx = input1.indexOf(" ");
      String input2 = "";
      for(int i = idx; i < input1.length(); i++){
        input2 = input2 + input1[i];
      }
      command_arg = input2.toFloat();
      return SVEL;
    }
  } else if(input1.indexOf("qstate") >= 0){
    return QSTATE;
  } else if(input1.indexOf("home") >= 0){
    return HOME;
  } else {
    return NONE;
  }

}

//************* Function for sending current state ***************************//
void send_state(){
  if(target_count != step_counter)
    Serial.print("BUSY, ");
  else
    Serial.print("READY, ");
  Serial.print("POS=");
  Serial.print(steps_to_pos(),3);
  Serial.print(", UL=");
  Serial.print(digitalRead(ls1_pin));
  Serial.print(", LL=");
  Serial.print(digitalRead(ls2_pin));
  Serial.print(", HOMED=");
  Serial.println(is_homed);
}

//******** Function for converting steps to mm and vice versa ****************//
int pos_to_steps(float pos_value){
  return int(pos_value/pitch*float(steps_in_rev*micro_steps));
}

int vel_to_delay(float vel_value){
  float cycles_per_second = float(vel_value/pitch)*float(steps_in_rev)*float(micro_steps)*2.0;
  return int(float(1.0e6/cycles_per_second));
}

float steps_to_pos(){
  return (float(step_counter)/(float(steps_in_rev)*float(micro_steps))*pitch);
}


//************* Function for homing the stage ***************************//
void home_stage(){

  // Drive to the lower limit 3 times and record the steps there
  long temp_steps[3] = {0,0,0};
  int two_mm_up = steps_in_rev*micro_steps;

  for(int i = 0; i < 3; i++){

    // Drive to lower limit
    digitalWrite(dir_pin, LOW);
    while(!digitalRead(ls2_pin)){
      digitalWrite(step_pin, LOW);
      delayMicroseconds(homing_step_delay);
      digitalWrite(step_pin, HIGH);
      delayMicroseconds(homing_step_delay);
      step_counter--;
    }

    // Record the "current zero"
    temp_steps[i] = step_counter;

    // Go a bit up before the next approach
    digitalWrite(dir_pin, HIGH);
    for(int j = 0; j < two_mm_up; j++){
      digitalWrite(step_pin, LOW);
      delayMicroseconds(homing_step_delay);
      digitalWrite(step_pin, HIGH);
      delayMicroseconds(homing_step_delay);
      step_counter++;
    }

  }

  // Compute the average and set that as the new zero
  long new_zero = (temp_steps[0] + temp_steps[1] + temp_steps[2])/3;
  step_counter = step_counter - new_zero;

  is_homed = true;
  target_count = step_counter;
  
}


//************* Function for advacing the stepper ***************************//
void drive_stepper(int n_steps, bool move_dir){
  
  // Drive the stepper to given direction
  digitalWrite(dir_pin, move_dir);
  for(int i = 0; i < n_steps; i++){
      if(move_dir){
        if(!digitalRead(ls1_pin)){
          digitalWrite(step_pin, LOW);
          delayMicroseconds(step_delay);
          digitalWrite(step_pin, HIGH);
          delayMicroseconds(step_delay);
        } else{
          target_count = step_counter;
        }
      }
      if(!move_dir){
        if(!digitalRead(ls2_pin)){
          digitalWrite(step_pin, LOW);
          delayMicroseconds(step_delay);
          digitalWrite(step_pin, HIGH);
          delayMicroseconds(step_delay);
        } else{
          target_count = step_counter;
        }
      }

      if(move_dir)
        step_counter++;
      else
        step_counter--;
    }
   
}