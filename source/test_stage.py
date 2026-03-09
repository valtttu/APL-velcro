import stage
import time
import sys


stg = stage.Stage('COM6')

res = stg.open()

if(not res):
    sys.exit()

print(stg.get_state())

print(stg.home())

print(stg.get_state())

stg.set_velocity(2)

print(stg.get_state())

print('Staring moving up...')
t_start = time.time()
stg.move_to_pos(24)

while(stg.get_state()[2]):
    time.sleep(0.5)
    print(stg.get_state())

print(f'Finished move in {time.time() -  t_start:.2f} seconds')

stg.close()

