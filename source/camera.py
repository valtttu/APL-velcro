import threading
import logging
import time
import PySpin
import matplotlib.pyplot as plt
from utils import check_path_exists, check_path_writeable


class Camera:

    def __init__(self):
        
        self._cam = None
        self._system = None
        self._cam_list = None
        self._acq_thread = threading.Thread()
        self._avi_recorder = None
        self._processor = None
        self._fps = 100
        self._is_recording = False
        self._is_live = False



    def open(self) -> bool:

        # Retrieve singleton reference to system object
        self._system = PySpin.System.GetInstance()

        # Get current library version
        version = self._system.GetLibraryVersion()
        logging.info('Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))

        # Retrieve list of cameras from the system
        self._cam_list = self._system.GetCameras()

        num_cameras = self._cam_list.GetSize()

        logging.info('Number of cameras detected: %d' % num_cameras)

        # Grab the connected camera
        if num_cameras == 1:
            self._cam = self._cam_list[0]
            
        else:
            self._cam_list.Clear()
            self._system.ReleaseInstance()
            logging.error('Did not find one camera, but found %d cameras!' % num_cameras)
            return False

        self._cam.Init()
        self._avi_recorder = PySpin.SpinVideo()
        self._processor = PySpin.ImageProcessor()
        self._processor.SetColorProcessing(PySpin.SPINNAKER_COLOR_PROCESSING_ALGORITHM_HQ_LINEAR)
        
        # Get device serial number
        serial_no = ''
        if self._cam.TLDevice.DeviceSerialNumber is not None and self._cam.TLDevice.DeviceSerialNumber.GetAccessMode() == PySpin.RO:
            serial_no = self._cam.TLDevice.DeviceSerialNumber.GetValue()

            logging.info('Opened device with serial number  %s...' % serial_no)

        return True



    def start_live_view(self, fig) -> bool:
        '''
            Start camera live view with a matplotlib figure window
        '''

        # Set acquisition mode to continuous
        if self._cam.AcquisitionMode.GetAccessMode() != PySpin.RW:
            logging.error('Unable to set acquisition mode to continuous!')
            return False

        self._cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        logging.info('Acquisition mode set to continuous...')


        # Set acquisition frame rate etc...

        # Start the image acquisition thread
        self._is_live = True
        self._acq_thread = threading.Thread(target=self.run_camera, args = (fig, ))
        self._acq_thread.start()

        return True
    


    def get_latest_frame(self):
        '''
            Return the latest complete frame that was acquired
        '''

        pass


    
    def start_recording(self, path: str, filename: str) -> bool:
        ''' 
            Begin saving video to given path
        '''

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

        #self._fps = self._cam.AcquisitionFrameRate.GetValue()

        # Initiate the video recording object
        option = PySpin.MJPGOption()
        option.frameRate = self._fps
        option.quality = 60
        option.width = 2448
        option.height = 2048

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

        self._is_recording = False
        for image in self._images:
            self._avi_recorder.Append(image)
        self._avi_recorder.Close()


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
        del self._cam

        # Clear camera list before releasing system
        self._cam_list.Clear()

        # Release system instance
        self._system.ReleaseInstance()



    def run_camera(self, fig):
        '''
            Main loop for camera image acquisition
        '''

        # Begin acquiring images
        self._cam.BeginAcquisition()
        logging.debug('Acquiring images...')


        # Figure(1) is default so you can omit this line. Figure(0) will create a new window every time program hits this line

        # Retrieve, convert, and save images
        while self._is_recording or self._is_live:

            try:
                # Retrieve next received image and ensure image completion
                image_result = self._cam.GetNextImage()

                if image_result.IsIncomplete():
                    logging.error('Image incomplete with image status %d...' % image_result.GetImageStatus())

                else:

                    # Record image resolution for potential use in the video reader
                    self._frame_width = image_result.GetWidth()
                    self._frame_height = image_result.GetHeight()

                    # Getting the image data as a numpy array
                    image_data = image_result.GetNDArray()

                    #plt.imshow(image_data, cmap='gray')
                    #plt.pause(0.001)
                    #plt.clf()

                    if(self._is_recording):
                        # Convert image to Mono8 and write to avi
                        #image_converted = image_data.Convert(PySpin.PixelFormat_Mono8)
                        image_converted = self._processor.Convert(image_result, PySpin.PixelFormat_Mono8)
                        #self._avi_recorder.Append(image_converted)
                        self._images.append(image_converted)
                        

                # Release image
                image_result.Release()

            except PySpin.SpinnakerException as ex:
                logging.error('Error in camera image acquisition: %s' % ex)

        # End acquisition
        #plt.close(fig)
        logging.debug('Finishing the image acquisition...')
        self._cam.EndAcquisition()