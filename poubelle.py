from flask import Flask, render_template, flash,redirect,request,g
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
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
DIA1 = 0.3
DIA2 = 0.3
GAIN1 = 0
GAIN2 = 0
pi = scipy.constants.pi


class SingleTable(Table):
    model = Col('Model')
    capa = Col('Total Capacity (Mbps)')
    ava = Col('Availability')
class DualTable(Table):
    model = Col('E-band Model')
    model2 = Col('MW Model')
    capa1= Col('E-band Capacity (Mbps)')
    capa2= Col('MW Capacity (Mbps)')
    t_capa = Col('Total Capacity (Mbps)')
    ava = Col('Availability (%)')

class SingleItem(object):
    def __init__(self, model,capa,ava ):
        self.model = str(model)
        self.capa = str(capa)
        self.ava = str(ava)

class DualItem(object):
    def __init__(self, model,model2,capa1,capa2, t_capa, ava):
        self.model = str(model)
        self.model2 = str(model2)
        self.capa1 = str(capa1)
        self.capa2 = str(capa2)
        self.t_capa = str(t_capa)
        self.ava = str(ava)



def getAntGain(freq):
    diameters = [0.3,0.6,0.9,1.2,1.8,2.4]
    gainList = dict()
    for val in diameters :
        gainList[val] = np.round(10*np.log10(0.5*((np.pi*val*freq)*np.power(10,9)/scipy.constants.speed_of_light)**2),1)
    return gainList

def getAntGain(dia,freq):
    return np.round(10*np.log10(0.5*((np.pi*dia*freq)*np.power(10,9)/scipy.constants.speed_of_light)**2),1)

def getProfilperCapa(capa=0,xpic=False,eband=False,multiB=False):
    profils = list()
    user = tinydb.Query()
    if multiB:
        if xpic: db = tinydb.TinyDB('db_huawei_XPIC.json')
        else : db = tinydb.TinyDB('db_huawei.json')
        if eband: tab_str = 'RTN380AX'
        else: tab_str = 'RTN900'
        for row in db.table(tab_str):
            offset = row['ACM_DROP_OFFSET']
            if offset == '' : offset =0.0
            profils.append([row['MODEL'], row['BAND_DESIGNATOR'], row['MAX_TX_POWER'], row['CAPACITY'],
                                    row['TYP_RX_THRESHOLD3'] + offset])
    else:
        db = tinydb.TinyDB('db_huawei.json')
        for tab in db.tables():
            table = db.table(str(tab))
            for row in table:
                offset = row['ACM_DROP_OFFSET']
                if offset == '': offset = 0.0
                if(np.isclose(row['CAPACITY'],float(capa),atol=MARG)):
                    profils.append([row['MODEL'],row['BAND_DESIGNATOR'],row['MAX_TX_POWER'],row['CAPACITY'],row['TYP_RX_THRESHOLD3']+ offset])

                    #profils.append()
    return profils


def getProb(profs,d,p,rr,xpic=False):
    good_pro = list()
    for prof in profs:
        GAIN1 = getAntGain(DIA1,prof[1])
        GAIN2 = getAntGain(DIA2,prof[1])
        wl = float(scipy.constants.speed_of_light / (prof[1] * (10 ** 9)))
        att= prof[2] + GAIN1 + GAIN2 - float(prof[-1]) - 20 * np.log10((4 * pi * d * 1000) / wl)
        if xpic:
            proba = 100 - itur.models.itu530.inverse_rain_attenuation(GEOLOCATE[0], GEOLOCATE[1], d, prof[1],ELEVATION, att, 0, rr).value
        else:
            proba = 100 - itur.models.itu530.inverse_rain_attenuation(GEOLOCATE[0],GEOLOCATE[1],d,prof[1],ELEVATION,att,POLAR,rr).value
        if proba > p:
            prof.append(proba)
            good_pro.append(prof)
    return good_pro

def getScenarii():
    rr = RR
    outstr = ''
    e_band_sitems = list()
    e_xpic_items = list()
    e_mw_ditems = list()
    mw_sitems = list()
    mw_items = list()
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
    for prof in good_pro:
        if prof[1]==80.0:
            e_band_sitems.append(SingleItem(prof[0],prof[-3],prof[-1]))
            outstr=outstr+str(prof[0])+' -- '+str(prof[-3])+' Mbps -- '+str(prof[-1])+'%\n'
    outstr=outstr+'---- eBand (XPIC 2+0) ----\n'
    db = tinydb.TinyDB('db_huawei_XPIC.json')
    table = getProfilperCapa(0,True,True,True)
    e_bands = list()
    e_bands = getProb(table, DISTANCE, AVAILABILITY,rr,True)
    for pro in e_bands:
        if np.isclose(float(pro[-3])*2,CIR,atol=MARG):
            e_xpic_items.append(SingleItem(pro[0],pro[-3]*2,pro[-1]))
            outstr=outstr+str(pro[0])+' -- '+str(pro[-3]*2)+' Mbps -- '+str(pro[-1])+'%\n'
    table = getProfilperCapa(0,False,True,True)
    e_bands = getProb(table, DISTANCE, AVAILABILITY,rr,False)
    table = getProfilperCapa(0,False,False,True)
    legacy = getProb(table, DISTANCE, AVAILABILITY,rr,False)
    outstr=outstr+'---- eBand + MW ----\n'
    for pro in e_bands:
        for leg in legacy:
            if leg[1] == 18.0 or leg[1] == 23:
                if np.isclose(float(pro[-3]+leg[-3]),CIR,atol=MARG) and not np.isclose(float(pro[-3]),CIR,atol=MARG) and not np.isclose(float(leg[-3]),CIR,atol=MARG):
                    e_mw_ditems.append(DualItem(pro[0],leg[0],pro[-3],leg[-3],pro[-3]+leg[-3],pro[-1]))
                    outstr=outstr+str(pro[0])+' + '+str(leg[0])+' -- '+str(pro[-3]+leg[-3])+' Mbps -- '+str(pro[-1])+'%\n'

    outstr=outstr+'---- MW (1+0) ----\n'
    for prof in good_pro:
        if prof[1]!=80.0:
            mw_sitems.append(SingleItem(prof[0], prof[-3], prof[-1]))
            outstr=outstr+str(prof[0])+' -- '+str(prof[-3])+' Mbps -- '+str(prof[-1])+'%\n'

    table = getProfilperCapa(0,True,False,True)
    legacy = getProb(table, DISTANCE, AVAILABILITY,rr,True)
    outstr=outstr+'---- MW (XPIC 2+0) ----\n'
    for pro in legacy:
        if np.isclose(float(pro[-3])*2, CIR, atol=MARG):
            mw_items.append(SingleItem(pro[0], pro[-3] * 2, pro[-1]))
            outstr = outstr + str(pro[0]) + ' -- ' + str(pro[-3]*2) + ' Mbps -- ' + str(
                pro[-1]) + '%\n'
    eb_stab = SingleTable(e_band_sitems,classes=['table table-striped'])
    ex_tab = SingleTable(e_xpic_items,classes=['table table-striped'])
    e_mw_tab = DualTable(e_mw_ditems,classes=['table table-striped'])
    mw_stab = SingleTable(mw_sitems,classes=['table table-striped'])
    mw_xtab= SingleTable(mw_items,classes=['table table-striped'])
    return ([eb_stab.__html__(),ex_tab.__html__(),e_mw_tab.__html__(),mw_stab.__html__(),mw_xtab.__html__()])#+outstr