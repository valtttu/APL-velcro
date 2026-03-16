
from probe import Probe
from camera import Camera
from stage import Stage, MAX_SPEED, Z_MAX
import numpy as np
import utils
import logging
import time
import threading

MEASUREMENT_STOP_NOISE_THRESHOLD = 10  # Limit for force reading standard deviation in [um]. Recording stops only after the noise is smaller than this
MEASUREMENT_STOP_TIMEOUT = 30   # The timeout for waiting for the standard deviation to come down in [s]

class Measurement:

    def __init__(self, probe: Probe, camera: Camera, stage: Stage):
        
        # Object handles for the hardware
        self.probe = probe
        self.camera = camera
        self.stage = stage

        # Parameters dict
        self._params = {'spring constant': {'value': 400, 'type': 'float', 'range': (0, 50000), 'unit': 'N/m'},
                        'z-velocity meas.': {'value': 0.5, 'type': 'float', 'range': (0.01, MAX_SPEED), 'unit': 'mm/s'},
                        'z-velocity default': {'value': 2, 'type': 'float', 'range': (0.1, MAX_SPEED), 'unit': 'mm/s'},
                        'pushing force': {'value': 1, 'type': 'float', 'range': (0.1, 50), 'unit': 'N'},
                        'z start meas.': {'value': 35, 'type': 'float', 'range': (0, Z_MAX), 'unit': 'mm'},
                        'scan length': {'value': 10, 'type': 'float', 'range': (0.5, 50), 'unit': 'mm'},
                        'repeats': {'value': 1, 'type': 'int', 'range': (1, 10), 'unit': ''},
                        'save path': {'value': utils.construct_default_path(), 'type': 'path', 'range': None, 'unit': ''},
                        'sample ID': {'value': 'Hook', 'type': 'string', 'range': None, 'unit': ''}}
        
        self._num_params = len(list(self._params.keys()))
        self._keys = list(self._params.keys())
        

        # Filename templates
        self._force_file_temp = self._params['sample ID']['value'] + '_force_N_'
        self._video_file_temp = self._params['sample ID']['value'] + '_video_N_'
        self._measurement_no = 1

        # Measuring thread
        self._meas_thread = threading.Thread()

        # State flags
        self._is_measuring = False
        self._is_recording = False
        self._finished = False
        self._state_str = ''


    def get_parameters(self):
        '''
            Get the current parameter names and values as two lists    
        '''

        return (self._keys, list(self._params.values()))


    def get_parameter(self, key: str):
        '''
            Get value of given parameter 
        '''
        if(key in self._keys):
            return self._params[key]['value']
        else:
            return None



    def edit_parameter(self, name: str, value_str: str):
        '''
            Edit the parameter at given index
        '''

        # Check index validity
        if(name not in self._keys):
            logging.error(f'Invalid name "{name}" for param list')
            return (False, 'Invalid name error')

        
        # Check the value validity
        res = False
        if(self._params[name]['type'] == 'float'):
            try:
                value = float(value_str)
                res = value >= self._params[name]['range'][0] and value <= self._params[name]['range'][1] 
            except ValueError:
                res = False
        if(self._params[name]['type'] == 'int'):
            try:
                value = int(value_str)
                res = value >= self._params[name]['range'][0] and value <= self._params[name]['range'][1]
            except ValueError:
                res = False
        elif(self._params[name]['type'] == 'path'):
            res = isinstance(value_str, str)
            res = utils.check_path_exists(value_str) and utils.check_path_writeable(value_str)
            value = value_str
        elif(self._params[name]['type'] == 'string'):
            res = isinstance(value_str, str)
            value = value_str

        if(res):
            self._params[name]['value'] = value
            self._sync_parameters()
            return (True, f'Successfully updated "{name}"')
        else:
            return (False, f'Invalid value "{value_str}" for parameter "{name}"')


    def start_recording(self):
        '''
            Start manual recording
        '''
        res = [False, False]
        t_now = time.time()
        res[0] = self.camera.start_recording(self._params['save path']['value'], f"{self._params['sample ID']['value']}_video_{t_now:.0f}")
        res[1] = self.probe.start_recording(self._params['save path']['value'], f"{self._params['sample ID']['value']}_force_{t_now:.0f}.csv")
        
        if(not (res[0] and res[1])):
            logging.error('Could not start recording, aborting the measurement')
            self.camera.end_recording()
            self.probe.stop_recording()
        else:
            self._is_recording = True


    def stop_recording(self):
        '''
            Stop manual recording
        '''
        if(self._is_recording):
            self.camera.end_recording()
            self.probe.stop_recording()
            self._is_recording = False


    def start_measurement(self):
        '''
            Start a single measurement
        '''

        self._is_measuring = True
        self._finished = False
        self._meas_thread = threading.Thread(target =  self._measure_single)
        self._meas_thread.start()


    def stop_measurement(self):
        '''
            Stops a single measurement
        '''

        self._is_measuring = False
        self.stage.stop()
        if(self._meas_thread.is_alive()):
            self._meas_thread.join()
            logging.info('Measurement stopped')
        if(self._is_recording):
            self.probe.stop_recording()
            self.camera.end_recording()
        


    def is_measuring_automatic(self):
        '''
            Return true if automatic measurement is active
        '''

        return self._is_measuring


    def is_recording(self):
        '''
            Return true if any recording is on
        '''

        return self._is_recording


    def get_state(self):
        '''
            Return description of the automatic measurement status
        '''
        if(self._is_measuring):
            return self._state_str
        else:
            return 'Idle'
        


    def has_finished(self):
        '''
            Return the `self._finished` flag and set it to `False` when accessed for the 1st time
        '''

        if(self._finished):
            self._finished = False
            return True
        else:
            return True
        


    def _sync_parameters(self):
        '''
            Synchronize changes in parameter list to the hardware
        '''

        self._force_file_temp = self._params['sample ID']['value'] + '_force_N_'
        self._video_file_temp = self._params['sample ID']['value'] + '_video_N_'
        self.stage.set_velocity(self._params['z-velocity default']['value'])


    def _measure_single(self):
        '''
            Perform a single measurement: Uses the params saved in `self._params` and saves data with the current measurement number 
        '''

        # Increment measurement no. and print logging info
        self._measurement_no += 1
        logging.info(f"Starting measurement {self._measurement_no} for sample ID {self._params['sample ID']['value']}")
        self._state_str = f'Meas. no. {self._measurement_no}: Starting'

        # Move to starting location
        self.stage.move_to_pos(self._params['z start meas.']['value'], wait=True)
        

        # Start recording and the approach
        if(not self._is_measuring):
            return
        else:
            self.stage.set_velocity(self._params['z-velocity meas.']['value'])
            res = [False, False]
            res[0] = self.camera.start_recording(self._params['save path']['value'], f'{self._video_file_temp}{self._measurement_no:02d}')
            res[1] = self.probe.start_recording(self._params['save path']['value'], f'{self._force_file_temp}{self._measurement_no:02d}.csv')
        
        if(res[0] and res[1]):
            self.stage.drive_stage(True)
            self._is_recording = True
            self._state_str = f'Meas. no. {self._measurement_no}: Approaching'
            logging.info('\t\tStarting approach')
        else:
            logging.error('Could not start recording, aborting the measurement')
            self.stage.stop()
            self.camera.end_recording()
            self.probe.stop_recording()
            self._is_measuring = False
            return


        # Move upwards until pushing force limit or maximum z-position is reached
        starting_force = self.probe.get_latest_mean()/1e6*self._params['spring constant']['value']
        current_force = self.probe.get_latest()/1e6*self._params['spring constant']['value']
        while(self._is_measuring and self.stage.can_move() and np.abs(starting_force - current_force) < self._params['pushing force']['value']):
            time.sleep(0.05)
            current_force = self.probe.get_latest()/1e6*self._params['spring constant']['value']
            
        # Log the approach stop reason
        if(not self._is_measuring):
            logging.info('\t\tApproach was stopped: Reason user input')
        elif(not self.stage.can_move()):
            logging.info('\t\tApproach was stopped: Stage upper limit reached')
        elif(np.abs(starting_force - current_force) >= self._params['pushing force']['value']):
            logging.info('\t\tApproach was stopped: Pushing force limit reached')
        else:
            logging.error('\t\tApproach was stopped: Reason unknown')



        # Reverse the direction and retract
        if(not self._is_measuring):
            return
        else:
            self._state_str = f'Meas. no. {self._measurement_no}: Retracting'
            logging.info('\t\tStarting retracting')
            self.stage.move_to_pos(self._params['z start meas.']['value'] - self._params['scan length']['value'], wait=True)
            self.stage.set_velocity(self._params['z-velocity default']['value'])
            
        

        # Wait for the std deviation to come down
        t_start = time.time()
        logging.debug('\t\tCurrent probe std. dev. is ' + str(self.probe.get_latest_std()) + ' um')
        while(self.probe.get_latest_std()  > MEASUREMENT_STOP_NOISE_THRESHOLD and (time.time() - t_start) < MEASUREMENT_STOP_TIMEOUT):
            time.sleep(2)
            if(not self._is_measuring):
                break
        logging.debug('\t\tCurrent probe std. dev. is ' + str(self.probe.get_latest_std()) + ' um')


        # Finish the measurement
        self.camera.end_recording()
        self.probe.stop_recording()
        self._is_recording = False
        logging.info('\t\tDone!')
        self._state_str = f'Meas. no. {self._measurement_no}: Finished'
        self._is_measuring = False
        self._finished = True
        
        return

            


