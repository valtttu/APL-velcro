

file_in = './HAM.log'
file_out = './HAM_cleared.log'

fout = open(file_out, 'a+')

print(f'Starting looping file "{file_in}" ...')
removed_lines = 0
n_lines = 0
print_gap = 1000
with open(file_in, 'r+') as file:
    for line in file.readlines():
        if('ERR_NO_SENSORDATA_AVAILABLE' not in line):
            fout.write(line)
        else:
            removed_lines += 1

        n_lines += 1

        if(n_lines % print_gap == 0):
            print(f'\tCurrently at line {n_lines:d}')


fout.close()

print(f'Done! (removed {removed_lines:d} lines)')