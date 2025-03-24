from tkinter import *
from tkinter.ttk import *
from time import strftime
from myOTP import TOTPT
from base64 import b32decode

root = Tk()
root.title('Sample TOTP Generator')

k = b32decode('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA') # base32 encoded shared secret
 
def display():
    try:
        totp, ss = TOTPT(k)
    except:
        root.destroy()
    lbl.config(text=f'{totp}:{ss:02d}') # display current TOTP and seconds before it expires
    lbl.after(1000, display)

def on_click(e):
    lbl.clipboard_clear()
    lbl.clipboard_append(TOTPT(k)[0])
 
lbl = Label(root, font=('calibri', 40, 'bold'), background='purple', foreground='white')
lbl.bind("<Button-1>", on_click) # click label to copy TOTP to clipboard
lbl.pack(anchor='center')
display()
 
mainloop()
