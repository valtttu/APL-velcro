# This file contains probe class implementation:
# Probe takes care of reading data from the laser distance sensor
# The class uses Micro_epsilon's MEDAQLib

from MEDAQLib import MEDAQLib, ME_SENSOR, ERR_CODE
import time
import threading
import numpy as np
from termcolor import colored
import logging
import os
import sys
from utils import check_path_exists, check_path_writeable
import logging

os.system('color')

# Expected TransferData block size
EXPECTED_BLOCK_SIZE = 1

# Averaging array length
n_mean = 5

class Probe:

    ###########################################################
    # Initialize the probe class
    ###########################################################
    def __init__(self, port: str):

        # Choose the correct controller instance
        self._sensor = MEDAQLib.CreateSensorInstance(ME_SENSOR.SENSOR_ILD1220)
        self._range = 1e4

        self._sensor.SetParameterString("IP_Interface", "RS232")
        self._sensor.SetParameterString("IP_Port", port)

        # Flags
        self._is_open = False
        self._is_recording = False

        # The acquisition thread
        self._aq_thread = threading.Thread()

        # Latest distance and distance mean
        self._d_latest = 0
        self._d_mean = np.zeros((n_mean,1))

        # Other needed variables
        self._save_fid = None


    ###########################################################
    # Open the connection to ConfocalDT and start the acquisition thread
    ###########################################################
    def open(self):
        print('Probe: Opening USB connection to OptoILD ', end='')
        sys.stdout.flush()

        # Try to open communication to sensor via interface specified
        self._sensor.OpenSensor()

        # Check for errors
        if(self._sensor.GetLastError() == ERR_CODE.ERR_NOERROR):

            # Get some info for printing
            self._sensor.ExecSCmd("Get_Info")
            serialNumber = self._sensor.GetParameterString("SA_SerialNumber", 1000)
            Sensor = self._sensor.GetParameterString("SA_Sensor", 1000)
            print('with serial number: ' + str(serialNumber) + ', sensor: ' + str(Sensor) + '... ', end='')
            sys.stdout.flush()

            if(self._sensor.GetLastError() == ERR_CODE.ERR_NOERROR):
                print(colored('Done!', 'green'))
                self._is_open = True

                self._aq_thread = threading.Thread(target=self._get_single)
                self._aq_thread.start()

                return True
            else:
                print('... ' + colored('Error: ' + self._sensor.GetError(1024).split('.')[0], 'red'))
                return False
        else:
            print('... ' + colored('Error: ' + self._sensor.GetError(1024).split('.')[0], 'red'))
            return False


    ###########################################################
    # Get the open state of the probe
    ###########################################################
    def get_open(self):
        return self._is_open
  

    ###########################################################
    # Reset the probe parameters
    ###########################################################
    def reset(self):
        self._sensor.ExecSCmd("Reset_Boot")
        self._sensor.ClearAllParameters()
        print(self._sensor.GetParameters(1024))


    ###########################################################
    # Stop the data acquisition and close the serial connection
    ###########################################################
    def close(self):

        self.stop_recording()
        self._is_open = False

        self._aq_thread.join()
        while self._aq_thread.is_alive():
            time.sleep(0.01)

        # Closing down by closing interface and releasing sensor instance
        self._sensor.CloseSensor()
        self._sensor.ReleaseSensorInstance()
    

    ###########################################################
    # Start recording data in a csv file
    ###########################################################
    def start_recording(self, path, filename) -> bool:

        # Check the recording path and filename
        if not check_path_writeable(path):
            logging.error('Cannot write to the given path!')
            return False
        
        if not check_path_exists(path):
            logging.error('Given path does not exist!')
            return False

        if check_path_exists(path + '/' + filename):
            logging.error('Given file already exists!')
            return False
        
        self._save_fid = open(path + '/' + filename, 'w')
        self._is_recording = True
        return True



    ###########################################################
    # Stop recording data
    ###########################################################
    def stop_recording(self) -> bool:
        if(self._is_recording):
            self._is_recording = False
            self._save_fid.close()

    

    ###########################################################
    # Get the latest distance and force readout
    ###########################################################
    def get_latest(self):
        self._d_mean[0:-1] = self._d_mean[1:]
        self._d_mean[-1] = self._d_latest
        return self._d_latest
  

    ###########################################################
    # Get the latest mean distance and force
    ###########################################################
    def get_latest_mean(self):
        self.get_latest()
        m = np.mean(self._d_mean)
        return m
  

    ###########################################################
    # Get the latest mean distance and force
    ###########################################################
    def get_latest_std(self):
        self.get_latest()
        s = np.std(self._d_mean)
        return s
    

    ###########################################################
    # Private function that avails one measurement
    ###########################################################
    def _get_single(self):

        while self._is_open:
            # Check whether there's enough data to read in
            if(self._sensor.DataAvail() >= EXPECTED_BLOCK_SIZE):

                # Fetch data from MEDAQLib's internal buffer
                polled_data = self._sensor.Poll(1)

                # Check if TransferData causes an error
                if(self._sensor.GetLastError() == ERR_CODE.ERR_NOERROR):
                    # Convert to distance in um
                    raw_value = polled_data[0]
                    raw_data=sum(raw_value)
                    d_value = (raw_data)/6.5
                    if(d_value > self._range):
                        self._d_latest = np.nan
                    else:
                        self._d_latest = d_value

                    if(self._is_recording):
                        save_str = f'{time.time()}, {self._d_latest} \n'
                        self._save_fid.write(save_str)
                        self._save_fid.flush()

                else:
                    # Print TransferData error
                    logging.error(self._sensor.GetError(1024).split('.')[0])
            
            else:
                time.sleep(0.0001)
