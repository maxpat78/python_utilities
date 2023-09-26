from tkinter import *
from tkinter.ttk import *
from myOTP import clock

root = Tk()
root.title('NTP Offset')

def display():
    lbl.config(text='%f s'%clock.offset)

lbl = Label(root, font=('calibri', 40, 'bold'), background='purple', foreground='white')
lbl.pack(anchor='center')
display()
 
mainloop()
