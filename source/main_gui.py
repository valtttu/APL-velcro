import probe
import camera
import stage
import utils
import os
import logging
import measurement

import tkinter as tk
from PIL import ImageTk, Image

import numpy as np

UPDATE_MS = 20


# Open hardware connections
laser_probe = probe.Probe(port = 'COM4')
side_camera = camera.Camera()
z_stage = stage.Stage(port = 'COM6')

measurer = measurement.Measurement(laser_probe, side_camera, z_stage)

utils.setup_logging('HAM.log')

# Start the hardware
res = [False]*3
res[0] = laser_probe.open()
res[1] = side_camera.open()
res[2] = z_stage.open()

if(not(res[0] and res[1] and res[2])):
    logging.error('Could not start the hardware!\nExiting...')
    laser_probe.close()
    side_camera.close()
    z_stage.close()

path = os.path.dirname(__file__)


# Define handlers for button press event etc.
def update_param(event, entries, keys):
    logging.info(f'Updating params:')
    for i in range(len(keys)):
        res = measurer.edit_parameter(keys[i], entries[i].get())
        logging.info(f'\t{res[1]}: {entries[i].get()}')


def toggle_manual_recording():
    if(bt_start_manual['activebackground'] == 'red'):
        measurer.stop_recording()
        bt_start_automatic.config(state=tk.NORMAL)
        bt_start_manual.config(text="Start manual\n recording")
        bt_start_manual.config(activebackground='green')
        for entry in entries:
            entry.config(state="normal")
    else:
        measurer.start_recording()
        bt_start_automatic.config(state=tk.DISABLED)
        bt_start_manual.config(text="Stop manual\n recording")
        bt_start_manual.config(activebackground='red')
        for entry in entries:
            entry.config(state="disabled")


def toggle_automatic_recording():
    if(bt_start_automatic['activebackground'] == 'red'):
        measurer.stop_measurement()
        bt_start_manual.config(state=tk.NORMAL)
        bt_stage_home.config(state=tk.NORMAL)
        bt_stage_down.config(state=tk.NORMAL)
        bt_stage_up.config(state=tk.NORMAL)
        bt_start_automatic.config(text="Start measurement\n sequence")
        bt_start_automatic.config(activebackground='green')
        for entry in entries:
            entry.config(state="normal")
    else:
        measurer.start_measurement()
        bt_start_manual.config(state=tk.DISABLED)
        bt_stage_home.config(state=tk.DISABLED)
        bt_stage_down.config(state=tk.DISABLED)
        bt_stage_up.config(state=tk.DISABLED)
        bt_start_automatic.config(text="Stop measurement\n sequence")
        bt_start_automatic.config(activebackground='red')
        for entry in entries:
            entry.config(state="disabled")


def driveUp(event):
    if(not measurer.is_measuring_automatic()):
        z_stage.drive_stage(True)


def driveDown(event):
    if(not measurer.is_measuring_automatic()):
        z_stage.drive_stage(False)

def stageStop(event):
    z_stage.stop()


def updateGUI():
    global img, oval
    # Update info labels
    springk = measurer.get_parameter('spring constant')
    delta = laser_probe.get_latest()
    stage_state = z_stage.get_state()
    camera_state = side_camera.get_saving_state()
    state1.set(f'Current distance: {delta/1000:.3f} µm\nCurrent force: {delta/1e6*springk:.3f} N')
    state2.set(f'Current position: {stage_state[0]} mm\nState: {measurer.get_state()}')
    if(camera_state[0]):
        state3.set(f'Camera FPS: {side_camera.get_acquired_fps():.2f} Hz\t Saving state: {camera_state[1]:.0f}')
    else:
        state3.set(f'Camera FPS: {side_camera.get_acquired_fps():.2f} Hz\t Saving state: {"Done"}')

    # Get the next camera frame and display that
    frame = side_camera.get_latest_frame()
    img = ImageTk.PhotoImage(Image.fromarray(frame, 'L').resize(canvas_size))
    canvas.itemconfig(image_container, image = img)

    if(measurer.is_recording()):
        canvas.itemconfig(oval, fill = 'red')
    else:
        canvas.itemconfig(oval, fill = '')

    # Add GUI update function
    root.after(UPDATE_MS, updateGUI)


# Create the GUI window
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
canvas = tk.Canvas(root, width = canvas_size[0], height = canvas_size[1], bg='#300924')
canvas.grid(sticky='N',column=0, columnspan=8, row=0, rowspan=8, padx=10, pady=10)

frame = side_camera.get_latest_frame()
pil_image = Image.fromarray(frame, 'L').resize(canvas_size)
img = ImageTk.PhotoImage(pil_image)
image_container = canvas.create_image(0,0, anchor='nw', image = img)
oval = canvas.create_oval(5, 5, 25, 25, fill='', outline = '')



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


bt_stage_home = tk.Button(root, text="Home\n stage", 
                            command= z_stage.home,
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


# Create state info labels
state1 = tk.StringVar()
state1.set(f'Current distance: {700} µm\nCurrent force: {0.7} N')
state1_label = tk.Label(root,textvariable=state1, font=default_font, foreground='green', bg='#300924', justify='left')

state2 = tk.StringVar()
state2.set(f'Current position: {10} mm\nState: {"Idle"}')
state2_label = tk.Label(root,textvariable=state2, font=default_font, foreground='green', bg='#300924', justify='left')

state3 = tk.StringVar()
state3.set(f'Camera FPS: {10} Hz\t Saving state: {"Done"}')
state3_label = tk.Label(root,textvariable=state3, font=default_font, foreground='green', bg='#300924', justify='left')


# Arrange everything in a grid arrangement
bt_start_automatic.grid(row=9, column=0, columnspan=3, sticky='W', padx=10)
bt_start_manual.grid(row=9, column=3, columnspan=3, sticky='W')

bt_stage_down.grid(row=9,column=7, sticky='W')
bt_stage_up.grid(row=8,column=7, sticky='W')

bt_stage_home.grid(row=13,column=7, rowspan=2, sticky='W')

state1_label.grid(row=8, column=0, columnspan=3, sticky='W', padx=10)
state2_label.grid(row=8, column=3, columnspan=3, sticky='W')

# Create the text entry fields for parameters
keys = measurer.get_parameters()[0]
default_params = measurer.get_parameters()[1]
text_vars = []
entries = []
start_row = 14
col_span = 3    
for i in range(len(keys)):
    text_vars.append(tk.StringVar())
    text_vars[i].set(f'{default_params[i]["value"]}')
    tk.Label(root, text=keys[i], foreground='white', bg='#300924', font=default_font).grid(column=0, row=start_row+i, columnspan=col_span, sticky='W', padx=10)
    entries.append(tk.Entry(root,textvariable = text_vars[i], font=default_font))
    entries[i].grid(column=col_span, row=start_row+i, columnspan=col_span-2, sticky='W')
    entries[i].bind("<Return>", lambda event: update_param(event, text_vars, keys))

state3_label.grid(row=start_row + len(keys), column=0, columnspan=6, sticky='W')


# Bind buttons for stage movement
bt_stage_up.bind('<ButtonPress-1>', lambda event: driveUp(event))
bt_stage_down.bind('<ButtonPress-1>', lambda event: driveDown(event))
bt_stage_up.bind('<ButtonRelease-1>', lambda event: stageStop(event))
bt_stage_down.bind('<ButtonRelease-1>', lambda event: stageStop(event))


# Add GUI update function
root.after(UPDATE_MS, updateGUI)


# Enter the main loop
tk.mainloop()   


# Close hardware after tk mainloop finishes
laser_probe.close()
side_camera.close()
z_stage.close()
