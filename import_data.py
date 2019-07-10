import tinydb
import xlrd
import re
import os,sys

#Database File
print('coucou'+str(sys.argv[1]))
db = tinydb.TinyDB(str(sys.argv[1]))

#Excel Source file
path = str(sys.argv[2])

def add(path):
    #Opening excel file (first tab)
    f = xlrd.open_workbook(path,on_demand = True)
    ws = f.sheet_by_index(0)
    i=1
    j=1
    user = tinydb.Query()
    #Specifying Equipment Name
    name = str(sys.argv[3])
    #Select or create table according to the name
    table = db.table(name)
    equipment = list()
    spec = dict()

    #Scanning file
    while i < ws.nrows:
        while j < ws.ncols:
            spec[ws.cell_value(rowx=0, colx=j)]=ws.cell_value(i,j)
            j=j+1
        equipment.append(spec.copy())
        i = i + 1
        spec.clear()
        j = 0

    #Adding in the database
    for equip in equipment:
        table.insert(equip)

#Calling add() function
add(path)

# For ericsson :
#
# MODEL column should be like this : <CARD>/<Bandwidth value>/<SUBCARD> (the subcard value is not important)
#
# For Huawei : (ONLY USE db_huawei.json)
#
# If the equipment is RTN900 : The syntax is <FREQUENCY>G<BANDWIDTH>M<MODULATION>QAM_<CARD> =>  Example : 13G7M32QAM_ISM6XMC5D
#
# Else, the syntax is : <CARD>_<FREQUENCY>G_<BANDWIDTH>M_<MODULATION>QAM => Example : RTN380AX_80G_62.5M_128QAM




