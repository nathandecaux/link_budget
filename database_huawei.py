import tinydb
import xlrd
import re
from tkinter import filedialog
import os

db = tinydb.TinyDB('db_huawei_XPIC.json')
path = filedialog.askopenfilename(initialdir='/Users/Travail/Desktop/Docs/Link_Budget/Huawei',title='Select File',filetypes = (("Link Configuration files","*.*"),("all files","*.*")))
#path = '/Users/Travail/Desktop/Docs/Link_Budget/Huawei/RTN300/'
#
# files = []
# r=root, d=directories, f = files
# for r, d, f in os.walk(path):
#      for file in f:
#          print(f)
#          if '.xls' in file:
#              files.append(os.path.join(r, file))
#

def add(path):
    f = xlrd.open_workbook(path,on_demand = True)
    ws = f.sheet_by_index(0)
    i=1
    j=1
    user = tinydb.Query()
    name = "RTN380AX"
    table = db.table(name)
    equipment = list()
    spec = dict()

    while i < ws.nrows:
        while j < ws.ncols:
            spec[ws.cell_value(rowx=0, colx=j)]=ws.cell_value(i,j)
            j=j+1
        equipment.append(spec.copy())
        i = i + 1
        spec.clear()
        j = 0

    for equip in equipment:
        table.insert(equip)


add(path)
# for f in files:
#     if(f.split('_')[-2]=='AdMod'):
#         print("Bonjour")
#         i = i + 1
#     #add(f)


