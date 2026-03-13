import serial
import logging
import time 


MAX_SPEED = 10      # [mm/s]
MOVE_TIMEOUT = 60   # timeout for waiting stage movement [s]
TIMEOUT = 3         # timeout for the serial communication [s]
BAUDRATE = 115200   # Baudrate for the serial communication


class Stage:
	
    def __init__(self, port = 'COM4'):
		
        self._port = port
        


        self._velocity = 0.5     # [mm/s]
        self._position = 0       # [mm]
        self._upper_limit_flag = False
        self._lower_limit_flag = False
        self._is_moving = False
        self._is_waiting = False
        self._zmax = 70         # [mm]



    def open(self):

        try:
            self._stepper = serial.Serial(port = self._port, baudrate = BAUDRATE, timeout = TIMEOUT)
            reply = self._write_command('QSTATE')
            if('ready' not in reply.lower()):
                logging.error('ERROR: Could not connect to the micro controller')
                return False
            else:
                return True
        except:
            logging.error('ERROR: Could not connect to the micro controller')
            return False



    def close(self):
        self._stepper.close()



    def set_velocity(self, value):

        if(value > 0 and value <= MAX_SPEED):
            if(value != self._velocity):
                self._velocity = value
                self._write_command(f'SVEL {value}')
        else:
            logging.error(f'Cannot set velocity to {value}! Value should be between [{[0, MAX_SPEED]}]')



    def get_state(self):
        '''
            Returns position, velocity and is_moving flag as a tuple
        '''
        if(not self._is_waiting):
            result = self._write_command('QSTATE')
            self._parse_state(result)
        return (self._position, self._velocity, self._is_moving, self._lower_limit_flag, self._upper_limit_flag)



    def move_to_pos(self, pos: float, wait = False):

        if(pos >= 0 and pos <= self._zmax):

            result = self._write_command(f'MOVE {pos}')

            if('move started' not in result.lower()):
                logging.error(f'Error in moving to pos {pos}: {result}')


            if(wait):
                t_start = time.time()
                self._is_waiting = True
                self._is_moving = True
                while(time.time() - t_start < MOVE_TIMEOUT and self._is_moving):
                    
                    result = self._write_command('QSTATE')
                    self._parse_state(result)
                    time.sleep(0.05)
                self._is_waiting = False
        else:
            logging.error(f'Invalid position value {pos} in move_to_pos! Value should be between [{[0, self._zmax]}]')



    def drive_stage(self, direction: bool):
        '''
            Drive the stage forward or backward until stop is called
        '''

        if(direction):
            self.move_to_pos(self._zmax)
        else:
            self.move_to_pos(0)



    def can_move(self):
        return (not self._lower_limit_flag) and (not self._upper_limit_flag)


    def stop(self):
        self._write_command('STOP')



    def home(self):
        self._write_command('HOME')



    def _write_command(self, command: str): 
        self._stepper.read_all() # Empty the current buffer
        self._stepper.write(bytes(command + '\n', 'utf-8'))
        time.sleep(0.05)
        data = self._stepper.readline().decode().rstrip()
        return data 
    


    def _listen_reply(self):
        data = self._stepper.readline().decode().rstrip()
        return data 



    def _parse_state(self, msg: str):
        pts = msg.split(',')

        if('busy' in pts[0].lower()):
            self._is_moving = True
        elif('ready' in pts[0].lower()):
            self._is_moving = False
        else:
            logging.error(f'Got invalid reply for "QSTATE" {msg}')
            return
        
        for i in range(1,len(pts)):
            tmp = pts[i].split('=')
            if('pos' in tmp[0].lower()):
                self._position = float(tmp[1].rstrip())
            elif('homed' in tmp[0].lower()):
                self._is_homed = bool(tmp[1].rstrip())
            elif('ll' in tmp[0].lower()):
                self._lower_limit_flag = bool(tmp[1].rstrip())
            elif('ul' in tmp[0].lower()):
                self._upper_limit_flag = bool(tmp[1].rstrip())



