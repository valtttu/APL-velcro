import tkinter as tk
import time
from datetime import datetime
import sys

root = tk.Tk()

def onPress():
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\tGot a click')

def upKey(event):
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\tUp pressed')

def downKey(event):
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\tDown pressed')

btn = tk.Button(root, text="Test", 
                            command= onPress,
                            activebackground="green", 
                            activeforeground="white",
                            anchor="center",
                            bd=3,
                            bg="lightgray",
                            cursor="hand2",
                            disabledforeground="gray",
                            fg="black",
                            highlightbackground="black",
                            highlightcolor="green",
                            highlightthickness=2,
                            justify="center",
                            overrelief="raised",
                            padx=10,
                            pady=10)

btn.pack()

root.bind('<Up>', upKey)
root.bind('<Down>', downKey)

tk.mainloop()