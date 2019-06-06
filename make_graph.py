from flask import Flask, render_template, flash,redirect,request,g
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
from flask_wtf import Form, RecaptchaField
from wtforms import SelectField
import flask_sijax
import re
from flask_wtf.file import FileField
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
    BooleanField, SubmitField, IntegerField, FormField, validators,StringField,DecimalField,SelectMultipleField
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
import poubelle
import requests
from geolocation.main import GoogleMaps

class MakeGraph():
    #<--- Variables --->
    el = float()
    URL = "https://nominatim.openstreetmap.org/search"
    #rr = float(rp.rre.data)
    geoloc = (float(),float())
    rr = float()
    graphs = dict()
    tau = float()
    #rr = float(rp.rre.data)
    p0 = float
    xpic = str()
    equip = str()
    freq = float()
    card = str()
    bw = float
    ref_mod = str()
    g1a=float()
    g1b=float()
    am = str()
    #<--- Constants --->
    pi = float()
    wl = float()
    rainp = bool()
    modp = bool()
    availp=bool()
    modulation_level = dict()
    html = ''
    d = np.arange(0.01, 20, 0.01)
    def __init__(self,d1a,d1b,el,geoloc,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,rainp,modp,availp):
        self.g1a = d1a
        self.g1b = d1b
        self.el = el
        self.geoloc = geoloc
        self.rr = rr
        self.tau = tau
        self.p0 = p0
        self.xpic = xpic
        self.equip = equip
        self.freq = freq
        self.card=card
        self.bw = bw
        self.ref_mod = ref_mod
        self.rainp=rainp
        self.modp = modp
        self.availp=availp

    def getTx(self,mod):
        user = tinydb.Query()
        if self.xpic == '1':
            db = tinydb.TinyDB('db_huawei_XPIC.json')
        else:
            db = tinydb.TinyDB('db_huawei.json')
        table = db.table(self.equip)
        row = table.search((user.MODEL.search('(' + self.card + ')')) & (user.BAND_DESIGNATOR == float(self.freq)) & (
                user.BANDWIDTH == float(self.bw)) & (user.MODULATION_TYPE == str(mod)))
        return row[0]['MAX_TX_POWER']

    def getCapa(self,mod):
        user = tinydb.Query()
        if self.xpic == '1':
            db = tinydb.TinyDB('db_huawei_XPIC.json')
        else:
            db = tinydb.TinyDB('db_huawei.json')
        table = db.table(self.equip)
        row = table.search((user.MODEL.search('(' + self.card + ')')) & (user.BAND_DESIGNATOR == float(self.freq)) & (
                user.BANDWIDTH == float(self.bw)) & (user.MODULATION_TYPE == str(mod)))
        return row[0]['CAPACITY']

    def getRxThr(self,mod=''):
        user = tinydb.Query()
        if self.xpic == '1':
            db = tinydb.TinyDB('db_huawei_XPIC.json')
        else:
            db = tinydb.TinyDB('db_huawei.json')
        # manu='Ericsson',boolAM,equip,fre,modem,bw,mod
        # cb1 = equip , fe = freq, carde = card_modem, cpe = bandwidth , ref_mode = modulation

        if mod == '':
            mod = self.ref_mod
        table = db.table(self.equip)
        row = table.search((user.MODEL.search('(' + self.card + ')')) & (user.BAND_DESIGNATOR == float(self.freq)) & (
                    user.BANDWIDTH == float(self.bw)) & (user.MODULATION_TYPE == str(mod)))
        if (self.am == '1'):
            return row[0]['TYP_RX_THRESHOLD3'] + row[0]['ACM_DROP_OFFSET']
        else:
            return row[0]['TYP_RX_THRESHOLD3']

    def getThrList(self):

        user = tinydb.Query()
        if self.xpic == '1':
            db = tinydb.TinyDB('db_huawei_XPIC.json')
        else:
            db = tinydb.TinyDB('db_huawei.json')

        modulations = self.bandwCh(None,self.xpic,self.equip,self.freq,self.card,self.bw)
        table = db.table(self.equip)
        for mod in modulations:
            self.modulation_level[mod] = self.getRxThr(mod)
    def mkplots(self):
        html = ''
        d = self.d
        freq = self.freq
        el = self.el
        tau = self.tau
        rr= self.rr
        g1a = self.g1a
        g1b = self.g1b
        geoloc=self.geoloc
        ref_mod=self.ref_mod
        p0 = self.p0
        graphs=dict()
        if(self.rainp):
            p = plt.figure(title='Rain-caused exceeded attenuation according to the distance',x_axis_label = 'Distance (km)',y_axis_label = 'Attenuation (dB)')
            p.line(d, itur.models.itu530.rain_attenuation(0, 0, d, freq, el, 0.01, tau, rr), line_width=2)
            p.add_tools(HoverTool())
            graphs['rain']=p
            html = html + file_html(p, CDN, "my plot")

        if(self.modp):
            p=plt.figure(title='Capacity according to the distance',x_axis_label = 'Distance (km)',y_axis_label = 'Capacity (Mbps)')
            self.getThrList()
            # print(str(pi)+' -- '+str(tx1)+' -- '+str(g1a)+' -- '+str(g1b)+' -- '+str(20*np.log10((4*pi*9.94*1000)/wl)))
            rain_att = list()
            rain_att =  (g1a + g1b - 20 * np.log10(
                (4 * self.pi * d * 1000) / self.wl) - itur.models.itu530.rain_attenuation(geoloc[0], geoloc[1], d, freq, el, p0,
                                                                                tau, rr).value)
            mod_d = list()
            levels = list(self.modulation_level.values())
            mods_lab = list(self.modulation_level.keys())
            tx_mod = dict()
            capa_mod = dict()
            for lab in mods_lab:
                tx_mod[lab]=self.getTx(lab)
                capa_mod[lab]=self.getCapa(lab)
            capaline = list()

            for val in rain_att:
                max_mod = -100
                match = False
                for lab,mod in self.modulation_level.items():
                    if val+tx_mod[lab]> mod:
                        max_mod = mod
                        capa = capa_mod[lab]
                        match=True
                capaline.append(float(capa)) if match else capaline.append(0)
            p.line(d, capaline)
            p.add_tools(HoverTool())
            html = html+file_html(p, CDN, "my plot")
            graphs['mod'] = p
            # plt.hlines(-100,0,20,label='Rx Sensitivity',linestyles='dotted',colors=cmap(random.randint(1,20)))
            # plt.plot(tx2+g2a+g2b-itur.models.itu530.rain_attenuation(geoloc[0],geoloc[1], d, f2, el, 0.01,tau,rr).value-20*np.log((4*pi*d)/wl),label=str(f2)+'GHz')
        if(self.availp):
            rx_thr = self.getRxThr(ref_mod)
            tx1 = self.getTx(ref_mod)
            res = list()
            p=plt.figure(title='Availability according to the distance',x_axis_label = 'Distance (km)',y_axis_label = 'Availability')
            for dcrt in d:
                att_max = tx1 + g1a + g1b - float(rx_thr) - 20 * np.log10((4 * self.pi * dcrt * 1000) / self.wl)
                val = float()

                val = np.nan_to_num(itur.models.itu530.inverse_rain_attenuation(geoloc[0], geoloc[1], dcrt, freq, el, att_max, tau,rr).value)
                val = 100 - round(val, 5)
                res.append(val)
            # z = np.polyfit(d,res,10)
            # f = np.poly1d(z)
            # print(f(d))
            p.line(d, res)
            graphs['avail']=p
            html = html + file_html(p, CDN, "my plot")
        graphs['html']=html


