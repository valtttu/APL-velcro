import camera
import time
import matplotlib.pyplot as plt

cam = camera.Camera()

cam.open()

fig = plt.figure(1)

cam.start_live_view(fig)

cam.start_recording('./', 'test')

time.sleep(10)

t_start = time.time()
cam.end_recording()

print(f'Wrote all frames in {time.time() -  t_start:.2f} seconds')

cam.close()