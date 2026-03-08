import probe
import camera
import stage
import utils
import measurement

import cv2

WINDOW_NAME = 'Live view'

# Open hardware connections
laser_probe = probe.Probe()
side_camera = camera.Camera()
z_stage = stage.Stage(port = 'COM3')

measurer = measurement.Measurement(laser_probe, side_camera, z_stage)

# Start the hardware
laser_probe.open()
side_camera.open()
z_stage.open()

# Start live view and the menu loop
cv2.namedWindow(WINDOW_NAME)
side_camera.start_live_view(WINDOW_NAME)

is_running = True
while is_running:

    key = cv2.waitKey()
    # Listen for user actions
    if(measurer.is_measuring_automatic()):

        if(key == chr('c')):
            measurer.stop_measurement()

    else:
        if(key == chr('e')):
            measurer.edit_parameter(1, 1)


    # Print menu view
