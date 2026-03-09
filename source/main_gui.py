#import probe
#import camera
#import stage
import utils
import os
#import measurement

import tkinter as tk
from PIL import ImageTk, Image


# Open hardware connections
# laser_probe = probe.Probe(port = 'COM4')
# side_camera = camera.Camera()
# z_stage = stage.Stage(port = 'COM6')

#measurer = measurement.Measurement(laser_probe, side_camera, z_stage)

# Start the hardware
# res = [False]*3
# res[0] = laser_probe.open()
# res[1] = side_camera.open()
# res[2] = z_stage.open()

# if(not(res[0] and res[1] and res[2])):
#     logging.error('Couldn not start the hardware!\nExiting...')
#     laser_probe.close()
#     side_camera.close()
#     z_stage.close()

path = os.path.dirname(__file__)


params = {'spring constant': {'value': 4, 'type': 'float', 'range': (0, 50), 'unit': 'N/m'},
                        'z-velocity meas.': {'value': 0.5, 'type': 'float', 'range': (0.01, 2), 'unit': 'mm/s'},
                        'z-velocity default': {'value': 2, 'type': 'float', 'range': (0.1, 5), 'unit': 'mm/s'},
                        'pushing force': {'value': 1, 'type': 'float', 'range': (0.1, 50), 'unit': 'N'},
                        'z start meas.': {'value': 30, 'type': 'float', 'range': (0, 100), 'unit': 'mm'},
                        'scan length': {'value': 10, 'type': 'float', 'range': (0.5, 50), 'unit': 'mm'},
                        'repeats': {'value': 1, 'type': 'int', 'range': (1, 10), 'unit': ''},
                        'save path': {'value': 'utils.construct_default_path()', 'type': 'path', 'range': None, 'unit': ''},
                        'sample ID': {'value': 'Hook', 'type': 'string', 'range': None, 'unit': ''}}


def update_param(event, entries, params):
    print(f'Updating params!')
    keys = list(params.keys())
    for i in range(len(keys)):
        params[keys[i]] = entries[i].get()
        #measurer.edit_parameter(params[keys[i]], entries[i].get())
        print(f'\t{keys[i]}: {params[keys[i]]}, {type(entries[i].get())}')


def toggle_manual_recording():
    if(bt_start_manual['activebackground'] == 'red'):
        #measurer.stop_recording()
        bt_start_automatic.config(state=tk.NORMAL)
        bt_probe_offset.config(state=tk.NORMAL)
        bt_start_manual.config(text="Start manual\n recording")
        bt_start_manual.config(activebackground='green')
        for entry in entries:
            entry.config(state="normal")
    else:
        #measurer.start_recording()
        bt_start_automatic.config(state=tk.DISABLED)
        bt_probe_offset.config(state=tk.DISABLED)
        bt_start_manual.config(text="Stop manual\n recording")
        bt_start_manual.config(activebackground='red')
        for entry in entries:
            entry.config(state="disabled")


def toggle_automatic_recording():
    if(bt_start_automatic['activebackground'] == 'red'):
        #measurer.stop_measurement()
        bt_start_manual.config(state=tk.NORMAL)
        bt_probe_offset.config(state=tk.NORMAL)
        bt_stage_home.config(state=tk.NORMAL)
        bt_stage_down.config(state=tk.NORMAL)
        bt_stage_up.config(state=tk.NORMAL)
        bt_start_automatic.config(text="Start measurement\n sequence")
        bt_start_automatic.config(activebackground='green')
        for entry in entries:
            entry.config(state="normal")
    else:
        #measurer.start_measurement()
        bt_start_manual.config(state=tk.DISABLED)
        bt_probe_offset.config(state=tk.DISABLED)
        bt_stage_home.config(state=tk.DISABLED)
        bt_stage_down.config(state=tk.DISABLED)
        bt_stage_up.config(state=tk.DISABLED)
        bt_start_automatic.config(text="Stop measurement\n sequence")
        bt_start_automatic.config(activebackground='red')
        for entry in entries:
            entry.config(state="disabled")



# Create the GUI

default_font = ("Ubuntu Light", 12)

root = tk.Tk()
root.title('Hook adhesion microscope (HAM)')
root.configure(bg='#300924')

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

win_size = (int(screen_w*0.4), int(screen_h*1))

root.geometry(f'{win_size[0]}x{win_size[1]}+{screen_w-win_size[0]}+0')


# Create a canvas for the live view playback
canvas_size = (int(win_size[0]*0.9), int(win_size[1]*0.35))
canvas = tk.Canvas(root, width = canvas_size[0], height = canvas_size[1], bg="#C3E211" )
#canvas.create_line(108, 120, 320, 40, fill = 'black')
img = ImageTk.PhotoImage(Image.open(path + "/../figs/Two_hook_pull.png").resize(canvas_size))
canvas.create_image(0,0, anchor='nw', image=img)
canvas.grid(sticky='N',column=0, columnspan=8, row=0, rowspan=8, padx=10, pady=10)


# Create buttons
bt_start_automatic = tk.Button(root, text="Start measurement\n sequence", 
                            command= toggle_automatic_recording,
                            activebackground="green", 
                            activeforeground="white",
                            anchor="center",
                            bd=3,
                            bg="lightgray",
                            cursor="hand2",
                            disabledforeground="gray",
                            fg="black",
                            font=default_font,
                            highlightbackground="black",
                            highlightcolor="green",
                            highlightthickness=2,
                            justify="center",
                            overrelief="raised",
                            padx=10,
                            pady=10)


bt_start_manual = tk.Button(root, text="Start manual\n recording", 
                            command= toggle_manual_recording,
                            activebackground="green", 
                            activeforeground="white",
                            anchor="center",
                            bd=3,
                            bg="lightgray",
                            cursor="hand2",
                            disabledforeground="gray",
                            fg="black",
                            font=default_font,
                            highlightbackground="black",
                            highlightcolor="green",
                            highlightthickness=2,
                            justify="center",
                            overrelief="raised",
                            padx=10,
                            pady=10)


bt_stage_up = tk.Button(root, text="↑", 
                            command= None,
                            activebackground="green", 
                            activeforeground="white",
                            anchor="center",
                            bd=3,
                            bg="lightgray",
                            cursor="hand2",
                            disabledforeground="gray",
                            fg="black",
                            font=default_font,
                            highlightbackground="black",
                            highlightcolor="green",
                            highlightthickness=2,
                            justify="center",
                            overrelief="raised",
                            padx=10,
                            pady=10)


bt_stage_down = tk.Button(root, text="↓", 
                            command= None,
                            activebackground="green", 
                            activeforeground="white",
                            anchor="center",
                            bd=3,
                            bg="lightgray",
                            cursor="hand2",
                            disabledforeground="gray",
                            fg="black",
                            font=default_font,
                            highlightbackground="black",
                            highlightcolor="green",
                            highlightthickness=2,
                            justify="center",
                            overrelief="raised",
                            padx=10,
                            pady=10)

bt_probe_offset = tk.Button(root, text="Set\n probe\n offset", 
                            command= None,
                            activebackground="green", 
                            activeforeground="white",
                            anchor="center",
                            bd=3,
                            bg="lightgray",
                            cursor="hand2",
                            disabledforeground="gray",
                            fg="black",
                            font=default_font,
                            highlightbackground="black",
                            highlightcolor="green",
                            highlightthickness=2,
                            justify="center",
                            overrelief="raised",
                            padx=10,
                            pady=10)


bt_stage_home = tk.Button(root, text="Home\n stage", 
                            command= None,
                            activebackground="green", 
                            activeforeground="white",
                            anchor="center",
                            bd=3,
                            bg="lightgray",
                            cursor="hand2",
                            disabledforeground="gray",
                            fg="black",
                            font=default_font,
                            highlightbackground="black",
                            highlightcolor="green",
                            highlightthickness=2,
                            justify="center",
                            overrelief="raised",
                            padx=10,
                            pady=10)


state1 = tk.StringVar()
state1.set(f'Current distance: {700} µm\nCurrent force: {0.7} N')
state1_label = tk.Label(root,textvariable=state1, font=default_font, foreground='green', bg='#300924', justify='left')

state2 = tk.StringVar()
state2.set(f'Current position: {10} mm\nState: {"Idle"}')
state2_label = tk.Label(root,textvariable=state2, font=default_font, foreground='green', bg='#300924', justify='left')

#tk.Label(root, text='Z-stage', foreground='white', bg='#300924', wraplength=1, font=default_font).grid(column=6, row=8, rowspan=2, sticky='W')


bt_start_automatic.grid(row=8, column=0, columnspan=3, sticky='W', padx=10)
bt_start_manual.grid(row=8, column=3, columnspan=3, sticky='W')

bt_stage_down.grid(row=9,column=7, sticky='W')
bt_stage_up.grid(row=8,column=7, sticky='W')

bt_probe_offset.grid(row=11,column=7, rowspan=3, sticky='W')
bt_stage_home.grid(row=14,column=7, rowspan=2, sticky='W')

state1_label.grid(row=9, column=0, columnspan=3, sticky='W', padx=10)
state2_label.grid(row=9, column=3, columnspan=3, sticky='W')


keys = list(params.keys())
text_vars = []
entries = []
start_row = 10
col_span = 3    
for i in range(len(keys)):
    text_vars.append(tk.StringVar())
    text_vars[i].set(f'{params[keys[i]]["value"]}')
    tk.Label(root, text=keys[i], foreground='white', bg='#300924', font=default_font).grid(column=0, row=start_row+i, columnspan=col_span, sticky='W', padx=10)
    entries.append(tk.Entry(root,textvariable = text_vars[i], font=default_font))
    entries[i].grid(column=col_span, row=start_row+i, columnspan=col_span-2, sticky='W')
    #entries[i].bind("<Return>", lambda event: print(f'Got new param!{event}'))
    entries[i].bind("<Return>", lambda event: update_param(event, text_vars, params))

    
# Enter the main loop
tk.mainloop()   
