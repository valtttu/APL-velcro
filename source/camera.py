import threading
import logging
import time
import PySpin
import numpy as np
import time
from utils import check_path_exists, check_path_writeable
from termcolor import colored


class Camera:

    def __init__(self):
        
        self._cam = None
        self._system = None
        self._cam_list = None
        self._acq_thread = threading.Thread()
        self._avi_recorder = None
        self._processor = None
        self._fps = 100
        self._frame_time = np.nan
        self._is_recording = False
        self._is_live = False
        self._resolution = (720, 540)

        self._image_lock = threading.RLock()
        self._latest_frame = None

        self._write_thread = threading.Thread()
        self._is_saving = False
        self._save_progress = 0



    def open(self) -> bool:

        # Retrieve singleton reference to system object
        print('Camera: Opening USB connection to the side camera... ', end='')
        self._system = PySpin.System.GetInstance()

        # Get current library version
        version = self._system.GetLibraryVersion()
        logging.info('Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))

        # Retrieve list of cameras from the system
        self._cam_list = self._system.GetCameras()

        num_cameras = self._cam_list.GetSize()

        logging.info('Number of cameras detected: %d' % num_cameras)
        print(f'found {num_cameras} camera(s) ', end='')

        # Grab the connected camera
        if(num_cameras == 1):
            self._cam = self._cam_list[0]
            
        else:
            self._cam_list.Clear()
            self._system.ReleaseInstance()
            logging.error('Did not find one camera, but found %d cameras!' % num_cameras)
            print( colored(f'Error: Found {num_cameras} instead of one', 'red'))
            return False

        # Initialize camera and the video processor
        self._cam.Init()
        self._avi_recorder = PySpin.SpinVideo()
        self._processor = PySpin.ImageProcessor()
        self._processor.SetColorProcessing(PySpin.SPINNAKER_COLOR_PROCESSING_ALGORITHM_HQ_LINEAR)
        
        
        # Get device serial number
        serial_no = ''
        if(self._cam.TLDevice.DeviceSerialNumber is not None and self._cam.TLDevice.DeviceSerialNumber.GetAccessMode() == PySpin.RO):
            serial_no = self._cam.TLDevice.DeviceSerialNumber.GetValue()

            logging.info('Opened device with serial number  %s...' % serial_no)
            print(f'with serial number: {serial_no} ... ', end='')

        # Start the image acquisition thread
        self._is_live = True
        self._acq_thread = threading.Thread(target=self._run_camera)
        self._acq_thread.start()
        print(colored('Done!', 'green'))


        return True



    def get_latest_frame(self):
        '''
            Return the latest complete frame that was acquired
        '''
        with self._image_lock:
            return np.copy(self._latest_frame)


    def get_acquired_fps(self) -> float:
        '''
            Return the actual acquisition fps
        '''
        if(self._frame_time < 1e-3):
            return np.nan
        else:
            return 1/self._frame_time


    def get_saving_state(self) -> tuple[float | bool]:
        '''
            Return the video writing status, tuple(is_saving, percentage)
        '''
        return (self._is_saving, self._save_progress)


    def get_resolution(self) -> tuple[int]:
        '''
            Return the frame resolution
        '''
        return self._resolution


    
    def start_recording(self, path: str, filename: str) -> bool:
        ''' 
            Begin saving video to given path
        '''

        # Check that previous data has already been saved
        if(self._is_saving):
            logging.info('Have not finished writing previous video yet')
            return False

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
        

        # Get acquisition frame rate
        if self._cam.AcquisitionFrameRate.GetAccessMode() == PySpin.NA:
            logging.error('Unable to access acquisition frame rate. Aborting...')
            return False

        node_acquisition_framerate = PySpin.CFloatPtr(self._cam.GetNodeMap().GetNode('AcquisitionFrameRate'))

        if not PySpin.IsReadable(node_acquisition_framerate):
            logging.error('Unable to retrieve frame rate. Aborting...')
            return False

        self._fps = node_acquisition_framerate.GetValue()


        # Initiate the video recording object
        option = PySpin.MJPGOption()
        option.frameRate = self._fps
        option.quality = 60
        option.width = self._resolution[0]
        option.height = self._resolution[1]

        self._avi_recorder.Open(path + '/' + filename, option)
        self._images = []

        # Set recoding flag to true
        self._is_recording = True
        logging.info('Started recording with FPS %.1f' % self._fps)
        return True



    def end_recording(self):
        ''' 
            Stop the video recording and save the video
        '''
        if(self._is_recording):
            self._is_recording = False

            # Start the video writing thread
            self._is_saving = True
            self._write_thread = threading.Thread(target=self._write_video)
            self._write_thread.start()


    def close(self):
        '''
            Close the camera and free the resources
        '''

        if(self._is_live):
            self._is_live = False
            self._acq_thread.join()
            while self._acq_thread.is_alive():
                time.sleep(0.1)

        # Release the camera object
        if(self._cam_list.GetSize() > 0):
            self._cam.DeInit()
        del self._cam

        # Clear camera list before releasing system
        self._cam_list.Clear()

        # Release system instance
        self._system.ReleaseInstance()



    def _write_video(self):
        '''
            Write the currently saved frames to a video
        '''
        n_tot = len(self._images)
        for i, image in enumerate(self._images):            
            self._avi_recorder.Append(image)
            self._save_progress = (i+1)/n_tot*100
        self._avi_recorder.Close()
        self._is_saving = False

    

    def _run_camera(self):
        '''
            Main loop for camera image acquisition
        '''

        # Begin acquiring images
        self._cam.BeginAcquisition()
        logging.debug('Acquiring images...')

        frame_timer = time.time()

        # Retrieve, convert, and save images
        while self._is_recording or self._is_live:

            try:
                # Retrieve next received image and ensure image completion
                image_result = self._cam.GetNextImage()

                if image_result.IsIncomplete():
                    logging.error('Image incomplete with image status %d...' % image_result.GetImageStatus())

                else:
                    # Getting the image data as a numpy array
                    image_data = image_result.GetNDArray()

                    with self._image_lock:
                        self._latest_frame = np.copy(image_data)

                    self._frame_time = time.time() - frame_timer
                    frame_timer = time.time()

                    # Record the resolution
                    self._resolution = (image_result.GetWidth(), image_result.GetHeight())

                    # Put the frame to writing queue
                    if(self._is_recording):
                        image_converted = self._processor.Convert(image_result, PySpin.PixelFormat_Mono8)
                        self._images.append(image_converted)

                    
                        

                # Release image
                image_result.Release()

            except PySpin.SpinnakerException as ex:
                logging.error('Error in camera image acquisition: %s' % ex)

        # End acquisition
        logging.debug('Finishing the image acquisition...')
        self._cam.EndAcquisition()