import serial
import logging
import time 


MAX_SPEED = 2       # [mm/s]
TIMEOUT = 10        # timeout for the serial communication [s]
BAUDRATE = 115200   # Baudrate for the serial communication


class Stage:
	
    def __init__(self, port = 'COM4'):
		
        self._port = port
        


        self.velocity = 0.5     # [mm/s]
        self.position = 0       # [mm]
        self._upper_limit_flag = False
        self._lower_limit_flag = False


        self.zmax = 100         # [mm]


    def open(self):

        try:
            self._stepper = serial.Serial(port = self.port, baudrate = BAUDRATE, timeout = TIMEOUT)
            return True
        except:
            logging.error('ERROR: Could not connect to the micro controller')
            return False


    def set_velocity(self, value):

        if(value > 0 and value < MAX_SPEED):
            self.velocity = value
        else:
            logging.error(f'Cannot set velocity to {value}! Value should be between [{[0, MAX_SPEED]}]')


    def move_to_pos(self, pos: float, wait = False):

        if(isinstance(pos, float)):
            command_str = f'MOVE, Z={pos}, VEL={self.velocity}'

            result = self._write_command(command_str)

            if('move started' in result.lower()):
                if(wait):
                    result = self._listen_reply()
                    if('move finished' not in result):
                        logging.error(f'Error in moving to pos {pos}: {result}')

            else:
               logging.error(f'Error in moving to pos {pos}: {result}')


        else:
            logging.error(f'Invalid position value in move_to_pos')


    def can_move(self):
        return self._lower_limit_flag or self._upper_limit_flag


    def stop(self):
        result = self._write_command('STOP')
        



    def _write_command(self, command: str): 
        self._stepper.write(bytes(command, 'utf-8'))
        time.sleep(0.05)
        data = self._stepper.readline() 
        return data 
    
    def _listen_reply(self):
        data = self._stepper.readline() 
        return data 



