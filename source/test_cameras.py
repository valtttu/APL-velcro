import camera
import time

cam = camera.Camera()
try:
    cam.open()

    print(cam._acq_thread.is_alive())

    time.sleep(1)

    cam.start_recording('./', 'test')

    time.sleep(10)

    t_start = time.time()
    cam.end_recording()

    print(f'Wrote all frames in {time.time() -  t_start:.2f} seconds')
except Exception as e:
    print(f'Error occured: {e}')
cam.close()