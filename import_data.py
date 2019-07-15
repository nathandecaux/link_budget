import tinydb
import xlrd
import re
import os,sys


#Database File
#db = tinydb.TinyDB(str(sys.argv[1]))

#Excel Source file
#path = str(sys.argv[2])

def check(path,db):
    if db=="" : return False,False
    db_code = {'db_huawei.json': 0, 'db_ericsson.json': 1, 'db_ericsson_AM.json': 2}
    #Opening excel file (first tab)
    f = xlrd.open_workbook(path,on_demand = True)
    ws = f.sheet_by_index(0)
    i=1
    j=1
    user = tinydb.Query()
    #Specifying Equipment Name
    name = 'truc' #str(sys.argv[3])
    #Select or create table according to the name
    #table = db.table(name)
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
        flag = True
        if db_code[db]==0 :
            if not (equip['MODEL'].split('_').__len__()==4 and equip['ACM_DROP_OFFSET'] != None): flag = False

        elif db_code[db]== 1 :
            if not equip['MODEL'].split('/').__len__() > 2 and equip['MODEL'].split('/B').__len__()==1 : flag = False

        elif db_code[db]== 2:
            if not equip['MODEL'].split('/').__len__()>2 and equip['MOD_DOWNSHIFT_OFFSET'] != None and equip['MODEL'].split('/B').__len__()==2:
                flag = False
        else: flag = False
    return [flag,equipment]

def add(file,dico,name):
    db = tinydb.TinyDB(file)
    tab = db.table(name)
    for equip in dico:
        tab.insert(equip)



#Calling add() function
#add(path)

# For ericsson :
#
# MODEL column should be like this : <CARD>/<Bandwidth value>/<SUBCARD> (the subcard value is not important)
#
# For Huawei : (ONLY USE db_huawei.json)
#
# If the equipment is RTN900 : The syntax is <FREQUENCY>G<BANDWIDTH>M<MODULATION>QAM_<CARD> =>  Example : 13G7M32QAM_ISM6XMC5D
#
# Else, the syntax is : <CARD>_<FREQUENCY>G_<BANDWIDTH>M_<MODULATION>QAM => Example : RTN380AX_80G_62.5M_128QAM




