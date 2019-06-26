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
PIR = 0
AVAI_PIR = 99.0
GAIN1 = 0
GAIN2 = 0
pi = scipy.constants.pi
test=0

class SingleTable(Table):
    ref = Col('Metric',th_html_attrs={'style':"display:none;"},td_html_attrs={'style':"display:none;"})
    model = Col('Model',th_html_attrs={'data-sortable':"true"})
    capa = Col('Total Capacity (Mbps)',th_html_attrs={'data-sortable':"true"})
    ava = Col('Availability',th_html_attrs={'data-sortable':"true"})

    def get_tr_attrs(self, item):
        if re.match('.*p',item.ref):
            return {'id': item.ref,'style':"display:none;",'class':'odd'}
        else:
            return {'id': item.ref,'class':'even'}


class DualTable(Table):
    ref = Col('Metric',th_html_attrs={'style':"display:none;"},td_html_attrs={'style':"display:none;"})
    model = Col('E-band Model')
    model2 = Col('MW Model')
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
    def __init__(self,ref, model,capa,ava ):
        # a = '<div class="card"><div class="card-header" id="heading1"><h5 class="mb-0"><button class="btn btn-link" type="button" data-toggle="collapse" data-target="#collapseA" aria-expanded="true" aria-controls="collapseA">'
        # b = '</h5></div><div id="collapseA" class="collapse show" aria-labelledby="headingA" data-parent="#accordionExample"><div class="card-body"><div class="bootstrap-table">'
        # c = '</div></div></div></div>'

        self.ref= str(ref)
        self.model = str(model)
        self.capa = str(capa)
        self.ava = str(ava)
        self.id= str(ref)
class DualItem(object):
    def __init__(self,ref, model,model2,capa1,capa2, t_capa, ava):
        self.ref = str(ref)
        self.model = str(model)
        self.model2 = str(model2)
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
    return np.round(10*np.log10(0.5*((np.pi*dia*freq)*np.power(10,9)/scipy.constants.speed_of_light)**2),1)

def getProfilperCapa(capa=0,xpic=False,eband=False,multiB=False):
    profils = list()
    user = tinydb.Query()
    db = ''
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
        if prof[1]==80.0:
            i = i+1
            met = str(i)

            goodCIR['eband'].append(prof)
            e_band_sitems.append(SingleItem(met,prof[0],prof[-3],prof[-1]))
            outstr=outstr+str(prof[0])+' -- '+str(prof[-3])+' Mbps -- '+str(prof[-1])+'%\n'
    outstr=outstr+'---- eBand (XPIC 2+0) ----\n'
    i=0

    db = tinydb.TinyDB('db_huawei_XPIC.json')
    table = getProfilperCapa(0,True,True,True)
    e_bands = list()
    e_bands = getProb(table, DISTANCE, AVAILABILITY,rr,True)
    for pro in e_bands:
        if np.isclose(float(pro[-3])*2,CIR,atol=MARG):
            i = i+1
            met = str(i)
            goodCIR['ebandx'].append(pro)
            e_xpic_items.append(SingleItem(met,pro[0],pro[-3]*2,pro[-1]))
            outstr=outstr+str(pro[0])+' -- '+str(pro[-3]*2)+' Mbps -- '+str(pro[-1])+'%\n'
    table = getProfilperCapa(0,False,True,True)
    e_bands = getProb(table, DISTANCE, AVAILABILITY,rr,False)
    table = getProfilperCapa(0,False,False,True)
    legacy = getProb(table, DISTANCE, AVAILABILITY,rr,False)
    outstr=outstr+'---- eBand + MW ----\n'
    i=0

    for pro in e_bands:
        for leg in legacy:
            if leg[1] == 18.0 or leg[1] == 23:
                if np.isclose(float(pro[-3]+leg[-3]),CIR,atol=MARG) and not np.isclose(float(pro[-3]),CIR,atol=MARG) and not np.isclose(float(leg[-3]),CIR,atol=MARG):
                    i = i + 1
                    met = str(i)

                    goodCIR['multi'].append((pro,leg))
                    e_mw_ditems.append(DualItem(met,pro[0],leg[0],pro[-3],leg[-3],pro[-3]+leg[-3],np.minimum(pro[-1],leg[-1])))
                    outstr=outstr+str(pro[0])+' + '+str(leg[0])+' -- '+str(pro[-3]+leg[-3])+' Mbps -- '+str(pro[-1])+'%\n'

    outstr=outstr+'---- MW (1+0) ----\n'
    i=0
    for prof in good_pro:
        if prof[1]!=80.0:
            i = i+1
            met = str(i)

            goodCIR['mw'].append((prof))
            mw_sitems.append(SingleItem(met,prof[0], prof[-3], prof[-1]))
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
            mw_items.append(SingleItem(met,pro[0], pro[-3] * 2, pro[-1]))
            outstr = outstr + str(pro[0]) + ' -- ' + str(pro[-3]*2) + ' Mbps -- ' + str(
                pro[-1]) + '%\n'
    eb_stab = SingleTable(e_band_sitems, classes=['table table-striped table-bordered'],
                          html_attrs={'data-sortable': "true"})
    eb_stab.table_id = "pouet"
    ex_tab = SingleTable(e_xpic_items, classes=['table table-striped table-bordered'])
    ex_tab.table_id = "pouet2"
    e_mw_tab = DualTable(e_mw_ditems, classes=['table table-striped table-bordered'])
    e_mw_tab.table_id = "pouet3"
    mw_stab = SingleTable(mw_sitems, classes=['table table-striped table-bordered'])
    mw_stab.table_id = "pouet4"
    mw_xtab = SingleTable(mw_items, classes=['table table-striped table-bordered'])
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
    goodPIR = getScenarii(2,PIR,AVAI_PIR)
    final = dict()
    cur= []
    cur.append('pouet')
    for key in goodPIR.keys():
        cur = []
        for valP in goodPIR[str(key)]:
            for valC in goodCIR[str(key)]:
                    if key == 'multi':
                        if getModelMulti(valC[0],valC[1],valP[0],valP[1]) and (valC,valP) not in cur : cur.append((valC,valP))
                    else:
                        if getModel(str(valC[0]),str(valP[0])):
                            cur.append((valC,valP))
            final[str(key)]=cur
    e_band_sitems = list()
    e_xpic_items = list()
    e_mw_ditems = list()
    mw_sitems = list()
    mw_items = list()
    i=0
    if final.__contains__('eband'):
        for prof in final['eband']:
            i=i+1
            e_band_sitems.append(SingleItem(str(i)+'a',prof[0][0], prof[0][-3], prof[0][-1]))
            e_band_sitems.append(SingleItem(str(i)+'ap',prof[1][0], prof[1][-3], prof[1][-1]))
    i=0
    if final.__contains__('ebandx'):
        for pro in final['ebandx']:
            i=i+1
            e_xpic_items.append(SingleItem(str(i)+'b',pro[0][0], pro[0][-3] * 2, pro[0][-1]))
            e_xpic_items.append(SingleItem(str(i)+'bp',pro[1][0], pro[1][-3] * 2, pro[1][-1]))
    i=0
    if final.__contains__('mw'):
        for prof in final['mw']:
            i=i+1
            mw_sitems.append(SingleItem(str(i)+'c',prof[0][0], prof[0][-3], prof[0][-1]))
            mw_sitems.append(SingleItem(str(i)+'cp',prof[1][0], prof[1][-3], prof[1][-1]))
    i=0
    if final.__contains__('mwx'):
        for pro in final['mwx']:
            i=i+1
            mw_items.append(SingleItem(str(i)+'d',pro[0][0], pro[0][-3] * 2, pro[0][-1]))
            mw_items.append(SingleItem(str(i)+'dp',pro[1][0], pro[1][-3] * 2, pro[1][-1]))

    if final.__contains__('multi'):
        for (a,b) in final['multi']:
            i=i+1
            (pro,leg) = a
            prout = DualItem(str(i)+'e', pro[0], leg[0], pro[-3], leg[-3], pro[-3] + leg[-3], np.minimum(pro[-1],leg[-1]))
            e_mw_ditems.append(prout)
#td_html_attrs={'id':str(i)+'p','style':"display: none;"}
            (pro, leg) = b
            e_mw_ditems.append(DualItem(str(i)+'ep', pro[0], leg[0], pro[-3], leg[-3], pro[-3] + leg[-3], np.minimum(pro[-1],leg[-1])))

    eb_stab = SingleTable(e_band_sitems, classes=['table table-striped table-bordered'],html_attrs={'data-sortable':"true"})
    eb_stab.table_id="pouet"
    ex_tab = SingleTable(e_xpic_items, classes=['table table-striped table-bordered'])
    ex_tab.table_id="pouet2"
    e_mw_tab = DualTable(e_mw_ditems, classes=['table table-striped table-bordered'])
    e_mw_tab.table_id="pouet3"
    mw_stab = SingleTable(mw_sitems, classes=['table table-striped table-bordered'])
    mw_stab.table_id="pouet4"
    mw_xtab = SingleTable(mw_items, classes=['table table-striped table-bordered'])
    mw_xtab.table_id="pouet5"
    return ([eb_stab.__html__(), ex_tab.__html__(), e_mw_tab.__html__(), mw_stab.__html__(), mw_xtab.__html__()])

def getModel(row,row2):
    if row.split('_').__len__()>3:
        div = row.split('_')
        mod = div[0]
        div2= row2.split('_')
        mod2 = div2[0]
        if mod==mod2:
            if div[-1]!='X':
                if div[-1]=='BPSK':
                   bw = float(div[2].split('M')[0])
                   bw2 = float(div2[2].split('M')[0])
                   if bw < 700 and bw2/bw in [1.0,2.0,4.0]:
                        return True
                   elif (bw == 750 or bw == 1000) and bw2/bw in [1.0,2.0]:
                       return True
                   elif  (bw == 1500 or bw == 2000) and bw2==bw:
                       return True
                   else:
                       return False
                elif div[-1]!='BPSK' and div[-2]==div2[-2]:
                    return True
                else:
                    return False
            else:
               if div[-3] == div2[-3]:
                   return True
               else:
                   return False
        else:
            return False
    else:
        div = row.split('M')
        div2 = row2.split('M')
        srow = row.split('_')
        srow2 = row2.split('_')
        if srow[-1]=='X' and srow2[-1]=='X':
            if div[0]==div2[0] and srow[-2]==srow2[-2]:
                return True
            else:
                return False
        else:
            if div[0]==div2[0] and srow[-1]==srow2[-1]:
                return True
            else:
                return False

def getModelMulti(row,rowb,row2,row2b):
    div = str(row[0]).split('_')
    mod = div[0]
    div2= str(row2[0]).split('_')
    mod2 = div2[0]
    eban = False
    if mod==mod2:
        if div[-1] == 'BPSK':
            bw = float(div[2].split('M')[0])
            bw2 = float(div2[2].split('M')[0])
            if bw < 700 and bw2 / bw in [1.0, 2.0, 4.0]:
                eban= True
            elif (bw == 750 or bw == 1000) and bw2 / bw in [1.0, 2.0]:
                eban= True
            elif (bw == 1500 or bw == 2000) and bw2 == bw:
                eban= True
            else:
                eban= False
        elif div[-1] != 'BPSK' and div[-2] == div2[-2]:
            eban= True
        else:
            eban= False

        if eban:
            div = str(rowb[0]).split('M')
            div2 = str(row2b[0]).split('M')
            srow = str(rowb[0]).split('_')
            srow2 = str(row2b[0]).split('_')
            #print('div[0] : '+str(div[0])+' div3[0] : '+str(div2[0])+' srow[-1] : '+str(srow[-1])+' srow2[-1] : '+str(srow2[-1])+'\n')
            if div[0]==div2[0] and srow[-1]==srow2[-1] and row2b[3]>rowb[3]:
                return True
            else:
                return False
            
        else: return False
    else:
        return False


