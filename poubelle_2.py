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
from bokeh.resources import INLINE
from bokeh.util.browser import view
from bokeh.models import Plot,Tool,HoverTool,Slider,WidgetBox
from bokeh.resources import CDN
from bokeh.embed import file_html,components
import scipy.constants
import itur
import numpy as np
import tinydb
import os,sys
import webbrowser
import pickle
from bokeh.io import output,curdoc
from bokeh.layouts import row, column
import bokeh as bk
import holoviews as hv
import holoviews.plotting.bokeh
from jinja2 import Environment,Template


import poubelle
from make_graph import MakeGraph
import requests
from geolocation.main import GoogleMaps
from flask_table import Table, Col

class SingleTable(Table):
    g1a = Col('Antenna Gain A (dBm')
    g1b = Col('Antenna Gain B (dBm')
    el = Col('Tilt (degrees)')
    polar = Col('Polarizaton')
    p0 = Col('Availability ( %/year )')
    rr = Col('Rainrate (mm/h)')
    xpic = Col('XPIC')
    equip = Col('Equipment')
    freq = Col('Frequency (GHz)')
    card = Col('Modem Card + ODU')
    bw =Col('Bandwidth (MHz)')
    ref_mod = Col('Reference modulation')
    am = Col('Adaptative modulation')
class SingleItem(object):
    def __init__(self,d1a,d1b,el,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,am):
        self.g1a = d1a
        self.g1b = d1b
        self.el = el
        self.rr = rr
        self.polar = tau
        self.p0 = p0
        self.xpic = xpic
        self.equip = equip
        self.freq = freq
        self.card = card
        self.bw = bw
        self.ref_mod = ref_mod
        self.am = am





mods_list = list()
#form = GlobalForm()
def cb0Ch(obj_response,xpic):
    obj_response.html('#ep-cb1','')
    obj_response.html_append('#ep-cb1', '<option>----</option>')
    if xpic == '1':
        db = tinydb.TinyDB('db_huawei_XPIC.json')

    elif xpic == '0':
        db = tinydb.TinyDB('db_huawei.json')
    i=0
    choix = list()
    for val in db.tables():
        obj_response.html_append('#ep-cb1', '<option id='+str(i)+' value='+str(val)+' >'+val+'</option>')
        choix.append((str(val),str(val)))
        i=i+1
    form.ep.cb1.choices = choix
    choices_po['cb1']=choix



def equiCh(obj_response,xpic,equi):
    obj_response.html('#ep-fe','')
    obj_response.html_append('#ep-fe', '<option>----</option>')
    if xpic == '1':
        db = tinydb.TinyDB('db_huawei_XPIC.json')

    elif xpic == '0':
        db = tinydb.TinyDB('db_huawei.json')
    i=0
    table = db.table(str(equi))
    freqs = list()
    choix = list()
    for row in table:
        freq = row['BAND_DESIGNATOR']
        if freq not in freqs:
            freqs.append(freq)
    for val in freqs:
        val = str(val)
        choix.append((str(val), str(val)))
        obj_response.html_append('#ep-fe', '<option id='+str(i)+' value='+val+' >'+val+'</option>')
        i=i+1




def freqCh(obj_response,xpic,equi,freq):
    obj_response.html('#ep-carde','')
    obj_response.html_append('#ep-carde', '<option>----</option>')
    if xpic == '1':
        db = tinydb.TinyDB('db_huawei_XPIC.json')

    elif xpic == '0':
        db = tinydb.TinyDB('db_huawei.json')
    table = db.table(str(equi))
    mod_cards = list()
    i=0
    choix = list()

    for row in table:
        freq0 = row['BAND_DESIGNATOR']
        if equi == 'RTN900' and xpic == '1':
            mod_card = str(row['MODEL']).split('_')[-2]
        elif equi == 'RTN900' and xpic == '0':
            mod_card = str(row['MODEL']).split('_')[-1]
        else:
            mod_card = str(row['MODEL']).split('_')[0]
        if str(freq0) == str(freq) and mod_card not in mod_cards:
            i=i+1
            mod_card=str(mod_card)
            mod_cards.append(mod_card)
            choix.append((str(mod_card), str(mod_card)))
            obj_response.html_append('#ep-carde', '<option id=' + str(i) + ' value=' + mod_card + ' >' + mod_card + '</option>')




def cardCh(obj_response,xpic,equi,freq,carde):
    obj_response.html('#ep-cpe','')
    obj_response.html_append('#ep-cpe', '<option>----</option>')
    if xpic == '1':
        db = tinydb.TinyDB('db_huawei_XPIC.json')

    elif xpic == '0':
        db = tinydb.TinyDB('db_huawei.json')
    table = db.table(str(equi))
    bandwidths = list()
    match_str = str(carde)
    i=0
    choix = list()
    for row in table:
        freq0 = str(row['BAND_DESIGNATOR'])
        bandwidth = str(row['BANDWIDTH'])
        if (re.search('(' + match_str + ')', str(row['MODEL'])) != None) and str(freq0) == str(
                freq) and bandwidth not in bandwidths:
            i=i+1
            bandwidths.append(bandwidth)
            choix.append((str(bandwidth), str(bandwidth)))
            obj_response.html_append('#ep-cpe', '<option id=' + str(i) + ' value=' + bandwidth + ' >' + bandwidth + '</option>')
    form.ep.cpe.choices = choix

def sortMod(mod):
    if (re.match('BPSK', str(mod))):
        mod = '2QAM'
    if (re.match('QPSK', str(mod))):
        mod = '4QAM'
    if (re.match('8PSK', str(mod))):
        mod = '8QAM'
    return int(str(mod).split('QAM')[0])

def bandwCh(obj_response,xpic,equi,freq,carde,bandw):

    if str(obj_response) != 'None':
        obj_response.html('#ep-ref_mod','')
        obj_response.html_append('#ep-ref_mod', '<option>----</option>')
    if xpic == '1':
        db = tinydb.TinyDB('db_huawei_XPIC.json')

    elif xpic == '0':
        db = tinydb.TinyDB('db_huawei.json')
    table = db.table(str(equi))
    modulations = list()
    match_str = str(carde)
    i=0
    choix = list()
    for row in table:
        modulation = row['MODULATION_TYPE']
        freq0 = str(row['BAND_DESIGNATOR'])
        bandwidth = str(row['BANDWIDTH'])
        if (re.search('(' + match_str + ')', str(row['MODEL'])) != None) and str(freq0) == str(freq) and str(
                bandwidth) == str(bandw) and modulation not in modulations:
            modulations.append(modulation)
    modulations.sort(key=sortMod)

    if str(obj_response)=='None':
        return modulations
    else:
        for modulation in modulations:
            i = i + 1
            obj_response.html_append('#ep-ref_mod', '<option id=' + str(
                i) + ' value=' + modulation + ' >' + modulation + '</option>')
# def submittion(obj_response,xpic,equi,freq,carde,bandw,mod):
#     form.ep.cb1.choices = [(equi,equi)]
#     print(form.ep.cb1.choices)

if g.sijax.is_sijax_request:
    g.sijax.register_callback('cb0', cb0Ch)
    g.sijax.register_callback('cb1', equiCh)
    g.sijax.register_callback('fe', freqCh)
    g.sijax.register_callback('carde', cardCh)
    g.sijax.register_callback('cpe', bandwCh)
    # g.sijax.register_callback('click',submittion)
    return g.sijax.process_request()

if form.is_submitted():
    hv.extension('bokeh')

    renderer = hv.renderer('bokeh')
    link = form.lp
    ep = form.ep
    # <--- Variables --->
    d1a = float(link.gae.data)
    d1b = float(link.gbe.data)
    el = float(link.ele.data)
    URL = "https://nominatim.openstreetmap.org/search"
    #rr = float(rp.rre.data)
    geoloc = (0,0)
    rr = float()
    print("XE : "+link.xe.data)
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    if link.xe.data != '':
        location = str(link.xe.data)
        # key = 'AIzaSyA3nLe6yUCTTMB82u1LTuWoyGJGvr8gBZg'
        location_detail = {'q': location, 'format': 'json'}
        r = requests.get(url=URL, params=location_detail)
        data = r.json()
        latitude = float(data[0]['lat'])
        longitude = float(data[0]['lon'])
        geoloc = (latitude,longitude)
        itur.models.itu837.change_version(6)
        rr = itur.models.itu837.rainfall_rate(latitude,longitude,0.01).value
    tau = 0 if link.polar.data=='h' else 90  # float(form.polar.data)
    #rr = float(rp.rre.data)
    p0 = 100-float(link.p_entry.data)
    xpic = ep.cb0.data
    equip = ep.cb1.data
    freq = float(ep.fe.data)
    card = ep.carde.data
    bw = ep.cpe.data
    ref_mod = ep.ref_mod.data
    g1a=poubelle.getAntGain(d1a,freq)
    g1b=poubelle.getAntGain(d1b,freq)
    am = ep.am.data
    items = SingleItem(d1a, d1b, el, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod, am)
    table = SingleTable([items], classes=['table table-striped'])
    checks = [form.mf.rainp.data,form.mf.modp.data,form.mf.availp.data]
    graph = MakeGraph(g1a,g1b,el,geoloc,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,am,checks[0],checks[1],checks[2])
    rrS = Slider(title="rain", value=float(rr), start=0, end=110, step=10)
    source1 = plt.ColumnDataSource(data = graph.plotRain(g1a,g1b,el,geoloc,rrS.value,tau,p0,xpic,equip,freq,card,bw,ref_mod,am))
    def update_data(attr,old,new):
        source1 = plt.ColumnDataSource(data = graph.plotRain(g1a,g1b,el,geoloc,rrS.value,tau,p0,xpic,equip,freq,card,bw,ref_mod,am))
    graph1 = plt.figure(title='Rain-caused exceeded attenuation according to the distance',x_axis_label = 'Distance (km)',y_axis_label = 'Attenuation (dB)')
    graph1.line('x', 'y', source=source1)
    rrS.on_change('value',update_data)
    # doc = curdoc().add_root(row(column(rrS), graph1, width=800))
    # bk.plotting.show(doc)
    graph1.add_tools(HoverTool())
    l = bk.layouts.layout([graph1],bk.layouts.Row(rrS))
    # f = open('templates/graphs.html')
    # template = Template(f.read())
    script, div = components(bk.layouts.Row(rrS))
    filename = 'widget.html'

    # html = template.render(rrS=script, graph1=div,graph2=file_html(graph1,CDN,'plot1'),graph3=file_html(graph1,CDN,'plot1'),js_resources=js_resources,css_resources=css_resources)
    #
    # with open(filename, 'w') as f:
    #     f.write(html)
    #
    # view(filename)
    return render_template('graphs.html',rrS=script, graph1=div,graph2=file_html(graph1,CDN,'plot1'),graph3=file_html(graph1,CDN,'plot1'),js_resources=js_resources,css_resources=css_resources)
    # return render_template('graphs.html', graph=html)


