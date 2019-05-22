from tkinter import *
import os

#!venv/Scripts/python.exe

window = Tk()
window.title("Link Budget Start menu")
window.geometry('200x150')


def launchHua():
    window.destroy()
    os.system(os.getcwd()+'/venv/Scripts/python.exe test_huawei.py')
def launchEri():
    window.destroy()
    os.system(os.getcwd() + '/venv/Scripts/python.exe test.py')
lbl = Label(text='Choose the manufacturer\n----')
lbl.pack()
bt1 = Button(text='Huawei',command=launchHua)
bt1.pack()
bt2 = Button(text='Ericsson',command=launchEri)
bt2.pack()
window.mainloop()