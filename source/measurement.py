
from probe import Probe
from camera import Camera
from stage import Stage
import numpy as np
import utils
import logging
import time
import threading
from termcolor import colored

MEASUREMENT_STOP_NOISE_THRESHOLD = 10  # Limit for force reading standard deviation in [um]. Recording stops only after the noise is smaller than this
MEASUREMENT_STOP_TIMEOUT = 30   # The timeout for waiting for the standard deviation to come down in [s]

class Measurement:

    def __init__(self, probe: Probe, camera: Camera, stage: Stage):
        
        # Object handles for the hardware
        self.probe = probe
        self.camera = camera
        self.stage = stage

        # Parameters dict
        self._params = {'spring constant': {'value': 4, 'type': 'float', 'range': (0, 50), 'unit': 'N/m'},
                        'z-velocity meas.': {'value': 0.5, 'type': 'float', 'range': (0.01, 2), 'unit': 'mm/s'},
                        'z-velocity default': {'value': 2, 'type': 'float', 'range': (0.1, 5), 'unit': 'mm/s'},
                        'pushing force': {'value': 1, 'type': 'float', 'range': (0.1, 50), 'unit': 'N'},
                        'z start meas.': {'value': 30, 'type': 'float', 'range': (0, 100), 'unit': 'mm'},
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


    def get_parameters(self):
        '''
            Get the current parameter names and values as two lists    
        '''

        return (self._keys, list(self._params.values()))



    def edit_parameter(self, index: int, value: any):
        '''
            Edit the parameter at given index
        '''

        # Check index validity
        if(index < 0 or index > self._num_params):
            logging.error(f'Invalid index "{index}" for param list, the index must be between [0, {self._num_params}]')
            return (False, 'Invalid index error')
        
        # Check the value validity
        res = False
        if(self._params[self._keys[index]]['type'] == 'float'):
            res = isinstance(value, float) and value >= self.self._params[self._keys[index]]['range'][0] and value <= self.self._params[self._keys[index]]['range'][1] 
        if(self._params[self._keys[index]]['type'] == 'int'):
            res = isinstance(value, int) and value >= self.self._params[self._keys[index]]['range'][0] and value <= self.self._params[self._keys[index]]['range'][1] 
        elif(self._params[self._keys[index]]['type'] == 'path'):
            res = isinstance(value, str)
            res = utils.check_path_exists(value) and utils.check_path_writeable(value)
        elif(self._params[self._keys[index]]['type'] == 'string'):
            res = isinstance(value, str)

        if(res):
            self._params[self._keys[index]]['value'] = value
            return (True, f'Successfully updated "{self._keys[index]}"')
        else:
            return (False, f'Invalid value "{value}" for parameter "{self._keys[index]}"')


    def start_measurement(self):
        '''
            Start a single measurement
        '''

        self._is_measuring = True
        self._meas_thread = threading.Thread(target =  self._measure_single)
        self._meas_thread.start()
        logging.info(f'Measurement sequence started for sample ID: "{self._params['sample ID']['value']}"')


    def stop_measurement(self):
        '''
            Stops a single measurement
        '''

        self._is_measuring = False
        self.stage.stop()
        self._meas_thread.join()
        self.probe.stop_recording()
        self.camera.end_recording()
        logging.info('Measurement stopped')


    def is_measuring_automatic(self):
        '''
            Return true if automatic measurement is active
        '''

        return self._is_measuring
        




    def _measure_single(self):
        '''
            Perform a single measurement: Uses the params saved in `self._params` and saves data with the current measurement number 
        '''

        # Print logging info
        logging.info(f'\tStarting measurement {self._measurement_no} for sample ID "{self._params['sample ID']['value']}"')

        # Move to starting location
        self.stage.move_to_pos(self._params['z start meas.']['value'], wait=True)
        

        # Start recording and the approach
        if(not self._is_measuring):
            return
        else:
            self.stage.set_velocity(self._params['z-velocity meas.']['value'])
            res = [False, False]
            res[0] = self.camera.start_recording(self._params['save path']['value'], f'{self._video_file_temp}{self._measurement_no:02d}.avi')
            res[1] = self.probe.start_recording(self._params['save path']['value'], f'{self._force_file_temp}{self._measurement_no:02d}.csv')
        
        if(res[0] and res[1]):
            self.stage.move_to_pos(self.stage.zmax)
        else:
            logging.error('Could not start recording, aborting the measurement')
            self.camera.end_recording()
            self.probe.stop_recording()


        # Move upwards until pushing force limit or maximum z-position is reached
        starting_force = self.probe.get_latest_mean()*self._params['spring constant']['value']
        current_force = self.probe.get_latest()*self._params['spring constant']['value']
        while(self._is_measuring and self.stage.can_move() and np. abs(starting_force - current_force) < self._params['pushing force']['value']):
            time.sleep(0.001)
            current_force = self.probe.get_latest()*self._params['spring constant']['value']


        # Reverse the direction and retract
        if(not self._is_measuring):
            return
        else:
            self.stage.move_to_pos(self._params['z-velocity meas.']['value'] - self._params['scan length']['value'], wait=True)
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
        self._measurement_no += 1
        logging.info('\t\tDone!')
        self._is_measuring = False
        
        return

            


