from flask import Flask, render_template, flash,redirect,request,g
from flask_bootstrap import Bootstrap
from flask_wtf import Form, RecaptchaField
from wtforms import SelectField
import flask_sijax
import re
from flask_wtf.file import FileField
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
    BooleanField, SubmitField, IntegerField, FormField, validators,StringField,DecimalField,SelectMultipleField
from wtforms.validators import Required
import bokeh.plotting as plt
from bokeh.models import Plot,Tool,HoverTool,Select,TextInput,Button,Slider
from bokeh.resources import CDN
from bokeh.embed import file_html
import scipy.constants
import itur
import numpy as np
from flask_table import Table, Col

import tinydb
import os,sys
import webbrowser
import pickle
import poubelle
import requests




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
    truc = Slider()
    graphs = dict()
    table = str()
    db = ''
    def __init__(self,d1a,d1b,el,geoloc,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,am,rainp,modp,availp):
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
        self.am = am
        self.rainp=rainp
        self.modp = modp
        self.availp=availp
        self.pi = scipy.constants.pi
        self.wl = float(scipy.constants.speed_of_light / (freq * (10 ** 9)))
        self.graphs['rain'] = None
        self.graphs['mod'] = None
        self.graphs['avail'] = None
        self.db = tinydb.TinyDB('db_huawei_XPIC.json') if xpic == '1' else tinydb.TinyDB('db_huawei.json')



    def update(self,d1a,d1b,el,geoloc,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,am):
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
        self.card = card
        self.bw = bw
        self.ref_mod = ref_mod
        self.am = am
        self.modulation_level.clear()
        self.db = tinydb.TinyDB('db_huawei_XPIC.json') if xpic == '1' else tinydb.TinyDB('db_huawei.json')


    def getTx(self,mod):
        user = tinydb.Query()
        table = self.db.table(self.equip)
        row = table.search((user.MODEL.search('(' + self.card + ')')) & (user.BAND_DESIGNATOR == float(self.freq)) & (
                user.BANDWIDTH == float(self.bw)) & (user.MODULATION_TYPE == str(mod)))
        return row[0]['MAX_TX_POWER']

    def getCapa(self,mod):
        user = tinydb.Query()
        table = self.db.table(self.equip)
        row = table.search((user.MODEL.search('(' + self.card + ')')) & (user.BAND_DESIGNATOR == float(self.freq)) & (
                user.BANDWIDTH == float(self.bw)) & (user.MODULATION_TYPE == str(mod)))
        return row[0]['CAPACITY']

    def getRxThr(self,mod=''):
        user = tinydb.Query()
        # manu='Ericsson',boolAM,equip,fre,modem,bw,mod
        # cb1 = equip , fe = freq, carde = card_modem, cpe = bandwidth , ref_mode = modulation

        if mod == '':
            mod = self.ref_mod
        table = self.db.table(self.equip)
        row = table.search((user.MODEL.search('(' + self.card + ')')) & (user.BAND_DESIGNATOR == float(self.freq)) & (
                    user.BANDWIDTH == float(self.bw)) & (user.MODULATION_TYPE == str(mod)))
        if (self.am == '1'):
            return row[0]['TYP_RX_THRESHOLD3'] + row[0]['ACM_DROP_OFFSET']
        else:
            return row[0]['TYP_RX_THRESHOLD3']



    def bandwCh(self,xpic, equi, freq, carde, bandw):
        table = self.db.table(str(equi))
        modulations = list()
        match_str = str(carde)
        i = 0
        choix = list()

        def sortMod(mod):
            if (re.match('BPSK', str(mod))):
                mod = '2QAM'
            if (re.match('QPSK', str(mod))):
                mod = '4QAM'
            if (re.match('8PSK', str(mod))):
                mod = '8QAM'
            return int(str(mod).split('QAM')[0])

        for row in table:
            modulation = row['MODULATION_TYPE']
            freq0 = str(row['BAND_DESIGNATOR'])
            bandwidth = str(row['BANDWIDTH'])
            if (re.search('(' + match_str + ')', str(row['MODEL'])) != None) and str(freq0) == str(freq) and str(
                    bandwidth) == str(bandw) and modulation not in modulations:
                modulations.append(modulation)
        modulations.sort(key=sortMod)
        return modulations

    def getThrList(self):
        modulations = self.bandwCh(self.xpic,self.equip,self.freq,self.card,self.bw)
        table = self.db.table(self.equip)
        for mod in modulations:
            self.modulation_level[mod] = self.getRxThr(mod)
    def plotRain(self,g1a,g1b,el,geoloc,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,am,d):
        p1 = np.arange(0.001,1,0.001)
        self.update(g1a,g1b,el,geoloc,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,am)
        self.getThrList()

        rx = (g1a + g1b - 20 * np.log10(
            (4 * self.pi * d * 1000) / self.wl) - itur.models.itu530.rain_attenuation(0, 0, d, freq, el, p1, tau, rr).value)

        mod_d = list()
        levels = list(self.modulation_level.values())
        mods_lab = list(self.modulation_level.keys())
        tx_mod = dict()
        capa_mod = dict()
        for lab in mods_lab:
            tx_mod[lab] = self.getTx(lab)
            capa_mod[lab] = self.getCapa(lab)
        capaline = list()

        for val in rx:
            max_mod = -100
            match = False
            capa = None
            for lab, mod in self.modulation_level.items():
                if val + tx_mod[lab] > mod:
                    max_mod = mod
                    capa = capa_mod[lab]
                    match = True
            capaline.append(float(capa)) if match else capaline.append(0)

        source1 =  dict(x=100-p1,y=capaline)
        return source1
    def plotMod(self,g1a,g1b,el,geoloc,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,am):
        d = np.arange(0.01, 20, 0.01)
        self.update(g1a, g1b, el, geoloc, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod, am)
        #infosl = dict(gainA=np.full(1999,g1a),gainB=np.full(1999,g1b),rain=np.full(1999,np.round(rr,1)),polar=np.full(1999,tau),avail=np.full(1999,np.round(100-p0,5)))
        #infose = {'xpic':np.full(1999,xpic),'equip':np.full(1999,equip),'freq':np.full(1999,freq),'card':np.full(1999,card),'bw':np.full(1999,bw),'ref_mod':np.full(1999,ref_mod),'am':np.full(1999,am)}

        p=plt.figure(title='Capacity according to the distance',x_axis_label = 'Distance (km)',y_axis_label = 'Capacity (Mbps)')

        self.getThrList()

        # print(str(pi)+' -- '+str(tx1)+' -- '+str(g1a)+' -- '+str(g1b)+' -- '+str(20*np.log10((4*pi*9.94*1000)/wl)))
        rain_att = list()
        rain_att =(g1a + g1b - 20 * np.log10(
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
            capa = None
            for lab,mod in self.modulation_level.items():
                if val+tx_mod[lab]> mod:
                    max_mod = mod
                    capa = capa_mod[lab]
                    match=True
            capaline.append(float(capa)) if match else capaline.append(0)
        dico = dict(x=d,y=capaline)
       # dico = dict(list(dico.items()) + list(infosl.items()) + list(infose.items()))
        return dico #infl=np.full(1999,infosl.__str__()),infe=np.full(1999,infose.__str__()))

    def plotAvail(self,g1a,g1b,el,geoloc,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,am):
        d = np.arange(0.01, 20, 0.01)
        self.update(g1a, g1b, el, geoloc, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod, am)
        rx_thr = self.getRxThr(ref_mod)
        tx1 = self.getTx(ref_mod)
        res = list()
        p=plt.figure(title='Availability according to the distance',x_axis_label = 'Distance (km)',y_axis_label = 'Availability')
        for dcrt in d:

            #d_t = itur.models.itu530.inverse_rain_attenuation(geoloc[0], geoloc[1], str(dcrt)+'_test', freq, el, 0, tau,rr).value
            #print('d = '+str(dcrt)+'; d_t = '+str(d_t))
            att_max = tx1 + g1a + g1b - float(rx_thr) - 20 * np.log10((4 * self.pi * dcrt * 1000) / self.wl)
            val = float()
            val = itur.models.itu530.inverse_rain_attenuation(geoloc[0], geoloc[1], dcrt, freq, el, att_max, tau,rr).value
            val = 100 - round(val, 9)
            res.append(val)
        return dict(x=d,y=res,freq=np.full(1999,freq))







    # def addline(self,d1a,d1b,el,geoloc,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,rainp,modp,availp):
    #     d = self.d
    #     self.update(d1a, d1b, el, geoloc, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod)
    #     html = ''
    #     if (rainp):
    #         p = self.graphs['rain']
    #         p.line(d, itur.models.itu530.rain_attenuation(0, 0, d, freq, el, 0.01, tau, rr), line_width=2)
    #         p.add_tools(HoverTool())
    #         self.graphs['rain'] = p
    #         html = html + file_html(p, CDN, "my plot")
    #
    #     if (self.modp):
    #         p = self.graphs['mod']
    #         self.getThrList()
    #         # print(str(pi)+' -- '+str(tx1)+' -- '+str(g1a)+' -- '+str(g1b)+' -- '+str(20*np.log10((4*pi*9.94*1000)/wl)))
    #         rain_att = list()
    #         rain_att = (d1a + d1b - 20 * np.log10(
    #             (4 * self.pi * d * 1000) / self.wl) - itur.models.itu530.rain_attenuation(geoloc[0], geoloc[1], d, freq,
    #                                                                                       el, p0,
    #                                                                                       tau, rr).value)
    #         mod_d = list()
    #         levels = list(self.modulation_level.values())
    #         mods_lab = list(self.modulation_level.keys())
    #         tx_mod = dict()
    #         capa_mod = dict()
    #         for lab in mods_lab:
    #             tx_mod[lab] = self.getTx(lab)
    #             capa_mod[lab] = self.getCapa(lab)
    #         capaline = list()
    #
    #         for val in rain_att:
    #             max_mod = -100
    #             match = False
    #             for lab, mod in self.modulation_level.items():
    #                 capa = None
    #                 if val + tx_mod[lab] > mod:
    #                     max_mod = mod
    #                     capa = capa_mod[lab]
    #                     match = True
    #             capaline.append(float(capa)) if match else capaline.append(0)
    #         p.line(d, capaline)
    #         p.add_tools(HoverTool())
    #         html = html + file_html(p, CDN, "my plot")
    #         self.graphs['mod'] = p
    #         # plt.hlines(-100,0,20,label='Rx Sensitivity',linestyles='dotted',colors=cmap(random.randint(1,20)))
    #         # plt.plot(tx2+g2a+g2b-itur.models.itu530.rain_attenuation(geoloc[0],geoloc[1], d, f2, el, 0.01,tau,rr).value-20*np.log((4*pi*d)/wl),label=str(f2)+'GHz')
    #     if (self.availp):
    #         rx_thr = self.getRxThr(ref_mod)
    #         tx1 = self.getTx(ref_mod)
    #         res = list()
    #         p = self.graphs['avail']
    #         for dcrt in d:
    #             att_max = tx1 + d1a + d1b - float(rx_thr) - 20 * np.log10((4 * self.pi * dcrt * 1000) / self.wl)
    #             val = float()
    #
    #             val = np.nan_to_num(
    #                 itur.models.itu530.inverse_rain_attenuation(geoloc[0], geoloc[1], dcrt, freq, el, att_max, tau,
    #                                                             rr).value)
    #             val = 100 - round(val, 5)
    #             res.append(val)
    #         # z = np.polyfit(d,res,10)
    #         # f = np.poly1d(z)
    #         # print(f(d))
    #         p.line(d, res)
    #         self.graphs['avail'] = p
    #         html = html + file_html(p, CDN, "my plot")
    #     self.graphs['html'] = html
    #     return self.graphs

    def getGraphs(self):
        return self.graphs

