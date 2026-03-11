import tkinter as tk
import time
from datetime import datetime
import sys

root = tk.Tk()

def onPress(event):
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\tGot a click')

def onRelease(event):
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\t\tReleased')

def upKey(event):
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\tUp pressed')

def downKey(event):
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\tDown pressed')

btn1 = tk.Button(root, text="Test 1", 
                            command= None,
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


btn2 = tk.Button(root, text="Test 2", 
                            command= None,
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

btn1.pack()
btn2.pack()
btn2.bind('<ButtonPress-1>', lambda event: onPress(event))
btn2.bind('<ButtonRelease-1>', lambda event: onRelease(event))

root.bind('<Up>', upKey)
root.bind('<Down>', downKey)

tk.mainloop()