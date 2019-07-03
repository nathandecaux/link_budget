from flask import Flask, render_template, flash, redirect, request, g, url_for
from flask_bootstrap import Bootstrap
from flask_table import Table, Col
from flask_wtf import Form, RecaptchaField
from wtforms import SelectField
import flask_sijax
import re
from flask_wtf.file import FileField
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
    BooleanField, SubmitField, IntegerField, FormField, validators,StringField,DecimalField
from wtforms.validators import Required
import bokeh.plotting as plt
from bokeh.models import Plot,Tool,HoverTool
from bokeh.resources import CDN
from bokeh.embed import file_html
import scipy.constants
import itur
import numpy as np
import tinydb
import os,sys
import webbrowser
import pickle


DISTANCE = 3.0
AVAILABILITY = 99.999
CIR = 10000.0
MARG = 300.0
GEOLOCATE = (0,0)
ELEVATION = 0.4
RR = 0
POLAR = 90
PIR = 0
AVAI_PIR = 99.0
DIA1 = 0.3
DIA2 = 0.3
GAIN1 = 0
GAIN2 = 0
pi = scipy.constants.pi
test=0


class SingleTable(Table):
    ref = Col('Metric',th_html_attrs={'style':"display:none;"},td_html_attrs={'style':"display:none;"})
    model = Col('Model')
    mod = Col('Modulation')
    capa = Col('Total Capacity (Mbps)')
    ava = Col('Availability')

    def get_tr_attrs(self, item):
        if re.match('.*p',item.ref):
            return {'id': item.ref,'style':"display:none;",'class':'odd'}
        else:
            return {'id': item.ref,'class':'even'}

class DualTable(Table):
    ref = Col('Metric',th_html_attrs={'style':"display:none;"},td_html_attrs={'style':"display:none;"})
    model = Col('E-band Model')
    mod = Col('E-band Modulation')
    model2 = Col('MW Model')
    mod2 = Col('MW Modulation')
    capa1= Col('E-band Capacity (Mbps)')
    capa2= Col('MW Capacity (Mbps)')
    t_capa = Col('Total Capacity (Mbps)')
    ava = Col('Availability (%)')

    def get_tr_attrs(self, item):
        if re.match('.*p',item.ref):
            return {'id': item.ref,'style':"display:none;",'class':'odd'}
        else:
            return {'id': item.ref,'class':'even'}



class SingleItem(object):
    def __init__(self,ref, model,mod,capa,ava):
        self.ref= str(ref)
        self.model = str(model)
        self.mod = str(mod)
        self.capa = str(capa)
        self.ava = str(ava)

class DualItem(object):
    def __init__(self,ref, model,mod,model2,mod2,capa1,capa2, t_capa, ava):
        self.ref= str(ref)
        self.model = str(model)
        self.mod = str(mod)
        self.model2 = str(model2)
        self.mod2 = str(mod2)
        self.capa1 = str(capa1)
        self.capa2 = str(capa2)
        self.t_capa = str(t_capa)
        self.ava = str(ava)
def update(pir,avail):
    CIR = pir

def getAntGain(freq):
    diameters = [0.3,0.6,0.9,1.2,1.8,2.4]
    gainList = dict()
    for val in diameters :
        gainList[val] = np.round(10*np.log10(0.5*((np.pi*val*freq)*np.power(10,9)/scipy.constants.speed_of_light)**2),1)
    return gainList

def getAntGain(dia,freq):
    return np.round(10*np.log10(0.6*((np.pi*dia*freq)*np.power(10,9)/scipy.constants.speed_of_light)**2),1)

def getProfilperCapa(capa=0,xpic=False,eband=False,multiB=False):
    profils = list()
    user = tinydb.Query()
    db = tinydb.TinyDB('db_ericsson_AM.json')

    for table in db.tables():
        for row in db.table(table):
            if capa>0 and np.isclose(float(row['CAPACITY']),capa,atol=MARG):
                profils.append([row['MODEL'],row['MODULATION_TYPE'], row['BAND_DESIGNATOR'], row['MAX_TX_POWER'], row['CAPACITY'],
                                            row['TYP_RX_THRESHOLD3']])


            if eband and row['BAND_DESIGNATOR']==80:
                profils.append([row['MODEL'],row['MODULATION_TYPE'],row['BAND_DESIGNATOR'], row['MAX_TX_POWER'], row['CAPACITY'],
                                row['TYP_RX_THRESHOLD3']])
            if not eband and row['BAND_DESIGNATOR']!=80 :
                profils.append([row['MODEL'],row['MODULATION_TYPE'], row['BAND_DESIGNATOR'], row['MAX_TX_POWER'], row['CAPACITY'],
                                row['TYP_RX_THRESHOLD3']])


                    #profils.append()
    return profils


def getProb(profs,d,p,rr,xpic=False):
    good_pro = list()
    for prof in profs:
        GAIN1 = getAntGain(DIA1,prof[2])
        GAIN2 = getAntGain(DIA2,prof[2])
        wl = float(scipy.constants.speed_of_light / (prof[2] * (10 ** 9)))
        att= prof[3] + GAIN1 + GAIN2 - float(prof[-1]) - 20 * np.log10((4 * pi * d * 1000) / wl)
        if xpic and prof[2]>0.0:
            proba = 100 - itur.models.itu530.inverse_rain_attenuation(GEOLOCATE[0], GEOLOCATE[1], d, prof[2],ELEVATION, att, 0, rr).value
        elif not xpic and prof[2]>0.0:
            proba = 100 - itur.models.itu530.inverse_rain_attenuation(GEOLOCATE[0],GEOLOCATE[1],d,prof[2],ELEVATION,att,POLAR,rr).value
        if proba > p:
            prof.append(proba)
            good_pro.append(prof)
    return good_pro

def getScenarii(test,CIR,AVAILABILITY):
    rr = RR
    outstr = ''
    e_band_sitems = list()
    e_xpic_items = list()
    e_mw_ditems = list()
    mw_sitems = list()
    mw_items = list()
    goodCIR = dict()
    i=0
    profils = getProfilperCapa(CIR)
    if(GEOLOCATE != (0,0) and rr == 0):
        itur.models.itu837.change_version(6)
        rr = itur.models.itu837.rainfall_rate(GEOLOCATE[0], GEOLOCATE[1], 0.01)
    outstr = '---- eBand (1+0) ----\n'
    good_pro = getProb(profils,DISTANCE,AVAILABILITY,rr)
    # while flag==0:
    #
    #     GAIN1 =GAIN1+10
    #     print(GAIN1)
    goodCIR['eband'] = list()
    goodCIR['ebandx'] = list()
    goodCIR['mw'] = list()
    goodCIR['mwx'] = list()
    goodCIR['multi'] = list()
    for prof in good_pro:
        if prof[2]==80.0:
            i = i+1
            met = str(i)
            goodCIR['eband'].append(prof)
            e_band_sitems.append(SingleItem(met,prof[0],prof[1],prof[-3],prof[-1]))
            outstr=outstr+str(prof[0])+' -- '+str(prof[-3])+' Mbps -- '+str(prof[-1])+'%\n'
    outstr=outstr+'---- eBand (XPIC 2+0) ----\n'
    i=0
    db = tinydb.TinyDB('db_ericsson_AM.json')
    table = getProfilperCapa(0,True,True,True)
    e_bands = list()
    e_bands = getProb(table, DISTANCE, AVAILABILITY,rr,True)
    for pro in e_bands:
        if np.isclose(float(pro[-3])*2,CIR,atol=MARG):
            i = i+1
            met = str(i)
            goodCIR['ebandx'].append(pro)
            e_xpic_items.append(SingleItem(met,pro[0],pro[1],str(int(pro[-3])*2),pro[-1]))
            outstr=outstr+str(pro[0])+' -- '+str(int(pro[-3])*2)+' Mbps -- '+str(pro[-1])+'%\n'
    table = getProfilperCapa(0,False,True,True)
    e_bands = getProb(table, DISTANCE, AVAILABILITY,rr,False)
    table = getProfilperCapa(0,False,False,True)
    legacy = getProb(table, DISTANCE, AVAILABILITY,rr,False)
    outstr=outstr+'---- eBand + MW ----\n'
    i=0
    for pro in e_bands:
        for leg in legacy:
            if leg[2] == 18.0 or leg[2] == 23:
                if np.isclose(float(float(pro[-3])+float(leg[-3])),CIR,atol=MARG) and not np.isclose(float(pro[-3]),CIR,atol=MARG) and not np.isclose(float(leg[-3]),CIR,atol=MARG) and float(pro[-3])>MARG and float(leg[-3])>MARG:
                    i = i + 1
                    met = str(i)
                    goodCIR['multi'].append((pro,leg))
                    e_mw_ditems.append(DualItem(met,pro[0],pro[1],leg[0],leg[1],pro[-3],leg[-3],str(int(pro[-3])+int(leg[-3])),pro[-1]))
                    outstr=outstr+str(pro[0])+' + '+str(leg[0])+' -- '+str(int(pro[-3])+int(leg[-3]))+' Mbps -- '+str(pro[-1])+'%\n'

    outstr=outstr+'---- MW (1+0) ----\n'
    i=0
    for prof in good_pro:
        if prof[2]!=80.0 and np.isclose(float(prof[-3]),CIR,atol=MARG):
            i = i+1
            met = str(i)
            goodCIR['mw'].append((prof))
            mw_sitems.append(SingleItem(met,prof[0],prof[1], prof[-3], prof[-1]))
            outstr=outstr+str(prof[0])+' -- '+str(prof[-3])+' Mbps -- '+str(prof[-1])+'%\n'

    table = getProfilperCapa(0,True,False,True)
    legacy = getProb(table, DISTANCE, AVAILABILITY,rr,True)
    outstr=outstr+'---- MW (XPIC 2+0) ----\n'
    i=0
    for pro in legacy:
        if np.isclose(float(pro[-3])*2, CIR, atol=MARG):
            i = i+1
            met = str(i)
            goodCIR['mwx'].append((pro))
            mw_items.append(SingleItem(met,pro[0],pro[1], str(int(pro[-3])*2), pro[-1]))
            outstr = outstr + str(pro[0]) + ' -- ' +str(int(pro[-3])*2) + ' Mbps -- ' + str(
                pro[-1]) + '%\n'
    eb_stab = SingleTable(e_band_sitems, classes=['table table-striped '],html_attrs={'width':"100%"})
    eb_stab.table_id = "pouet"
    ex_tab = SingleTable(e_xpic_items, classes=['table table-striped '], html_attrs={'width':"100%"})
    ex_tab.table_id = "pouet2"
    e_mw_tab = DualTable(e_mw_ditems, classes=['table table-striped '], html_attrs={'width':"100%"})
    e_mw_tab.table_id = "pouet3"
    mw_stab = SingleTable(mw_sitems, classes=['table table-striped '], html_attrs={'width':"100%"})
    mw_stab.table_id = "pouet4"
    mw_xtab = SingleTable(mw_items, classes=['table table-striped'], html_attrs={'width':"100%"})
    mw_xtab.table_id = "pouet5"
    if test==0 and PIR != 0:
        test=2
        return getScenariiPIR(goodCIR)
    elif test==2:
        return goodCIR
    elif PIR==0:
        return ([eb_stab.__html__(),ex_tab.__html__(),e_mw_tab.__html__(),mw_stab.__html__(),mw_xtab.__html__()])#+outstr


def getScenariiPIR(goodCIR):
    CIR = PIR
    AVAILABILITY = AVAI_PIR
    goodPIR = getScenarii(2, PIR, AVAI_PIR)
    final = dict()
    cur = []
    cur.append('pouet')

    for key in goodPIR.keys():
        cur = []
        for valP in goodPIR[str(key)]:
            for valC in goodCIR[str(key)]:
                if key == 'multi':
                    if getModelMulti(valC[0], valC[1], valP[0], valP[1]) and (valC, valP) not in cur: cur.append(
                        (valC, valP))
                else:
                    if getModel(str(valC[0]), str(valP[0])):
                        cur.append((valC, valP))
            final[str(key)] = cur
    e_band_sitems = list()
    e_xpic_items = list()
    e_mw_ditems = list()
    mw_sitems = list()
    mw_items = list()
    i = 0
    if final.__contains__('eband'):
        for prof in final['eband']:
            i = i + 1
            e_band_sitems.append(SingleItem(str(i) + 'a', prof[0][0],prof[0][1], prof[0][-3], prof[0][-1]))
            e_band_sitems.append(SingleItem(str(i) + 'ap', prof[1][0],prof[1][1], prof[1][-3], prof[1][-1]))
    i = 0
    if final.__contains__('ebandx'):
        for pro in final['ebandx']:
            i = i + 1
            e_xpic_items.append(SingleItem(str(i) + 'b', pro[0][0],pro[0][1], str(int(pro[0][-3]) * 2), pro[0][-1]))
            e_xpic_items.append(SingleItem(str(i) + 'bp', pro[1][0],pro[1][1], str(int(pro[1][-3]) * 2), pro[1][-1]))
    i = 0
    if final.__contains__('mw'):
        for prof in final['mw']:
            i = i + 1
            mw_sitems.append(SingleItem(str(i) + 'c', prof[0][0],prof[0][1], prof[0][-3], prof[0][-1]))
            mw_sitems.append(SingleItem(str(i) + 'cp', prof[1][0],prof[1][1], prof[1][-3], prof[1][-1]))
    i = 0
    if final.__contains__('mwx'):
        for pro in final['mwx']:
            i = i + 1
            mw_items.append(SingleItem(str(i) + 'd', pro[0][0], pro[0][1],str(int(pro[0][-3]) * 2), pro[0][-1]))
            mw_items.append(SingleItem(str(i) + 'dp', pro[1][0],pro[1][1], str(int(pro[1][-3]) * 2), pro[1][-1]))

    if final.__contains__('multi'):
        for (a, b) in final['multi']:
            i = i + 1
            (pro, leg) = a
            prout = DualItem(str(i) + 'e', pro[0],pro[1],leg[0],leg[1],pro[-3], leg[-3], str(int(pro[-3]) + int(leg[-3])),
                             np.minimum(pro[-1], leg[-1]))
            e_mw_ditems.append(prout)
            # td_html_attrs={'id':str(i)+'p','style':"display: none;"}
            (pro, leg) = b
            e_mw_ditems.append(DualItem(str(i) + 'ep',pro[0],pro[1],leg[0],leg[1],pro[-3], leg[-3], str(int(pro[-3]) + int(leg[-3])),
                                        np.minimum(pro[-1], leg[-1])))

    eb_stab = SingleTable(e_band_sitems, classes=['table table-striped table-bordered'],
                          html_attrs={'width':"100%"})
    eb_stab.table_id = "pouet"
    ex_tab = SingleTable(e_xpic_items, classes=['table table-striped table-bordered'], html_attrs={'width':"100%"})
    ex_tab.table_id = "pouet2"
    e_mw_tab = DualTable(e_mw_ditems, classes=['table table-striped table-bordered'], html_attrs={'width':"100%"})
    e_mw_tab.table_id = "pouet3"
    mw_stab = SingleTable(mw_sitems, classes=['table table-striped table-bordered'], html_attrs={'width':"100%"})
    mw_stab.table_id = "pouet4"
    mw_xtab = SingleTable(mw_items, classes=['table table-striped table-bordered'], html_attrs={'width':"100%"})
    mw_xtab.table_id = "pouet5"
    return ([eb_stab.__html__(), ex_tab.__html__(), e_mw_tab.__html__(), mw_stab.__html__(), mw_xtab.__html__()])


def getModel(row, row2):
    div = row.split('/B')
    mod = div[0]
    div2 = row2.split('/B')
    mod2 = div2[0]
    if mod == mod2:
        return True
    else:
        return False
        
  


def getModelMulti(row, rowb, row2, row2b):
    div = str(row[0]).split('/B')
    mod = div[0]
    div2 = str(row2[0]).split('/B')
    mod2 = div2[0]
    modb= str(rowb[0]).split('/B')[0]
    mod2b = str(row2b[0]).split('/B')[0]

    if mod == mod2 and modb == mod2b and row2[-3]>row[-3] and row2b[-3]>rowb[-3]:
        return True
    else:
        return False
        

