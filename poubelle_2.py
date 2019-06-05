
import tinydb
import os,sys

db = tinydb.TinyDB('db_huawei.json')
print(db.tables())
for table in db.tables():
    subtab = db.table(str(table))
    if len(subtab)==0:
        db.purge(str(subtab))