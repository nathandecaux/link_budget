import socket

from flask import Flask, render_template, flash,redirect,request,g
from flask_bootstrap import Bootstrap
from bokeh.server.server import Server,BaseServer
from tornado.ioloop import IOLoop
import bokeh.palettes as bkolor
import itertools
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
from bokeh.models import Plot,Tool,HoverTool,Slider,WidgetBox,Button,Select,TextInput,Spinner,Legend,LegendItem,Div,Markup
from bokeh.resources import CDN
from bokeh.embed import file_html,components,server_document
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
from bokeh.client import pull_session
from bokeh.embed import server_session
from jinja2 import Environment,Template
from threading import Thread
import poubelle_2
import poubelle
from make_graph import MakeGraph
from make_graph_eric import MakeGraphE
import requests

from flask_table import Table, Col

global BKTHREAD
BKTHREAD = Thread()
BKTHREAD.start()
app = Flask(__name__, static_url_path='/static')


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

# with open('graph_tmp', 'rb') as graph_tmp:
#     # Step 3
#     graphs = pickle.load(graph_tmp)

STATICFILES_DIRS = (
    os.path.join(os.path.dirname(__file__),'static'),
)

choices_po = dict()

class SelectFieldNoValidation(SelectField):
    def pre_validate(self, form):
        pass

class LinkForm(Form):
    gae = SelectField('Antenna Diameter A (m)',choices =[('0.3','0.3'),('0.6','0.6'),('0.9','0.9'),('1.2','1.2'),('1.8','1.8'),('2.4','2.4')])
    gbe = SelectField('Antenna Diameter B (m)',choices =[('0.3','0.3'),('0.6','0.6'),('0.9','0.9'),('1.2','1.2'),('1.8','1.8'),('2.4','2.4')])
    ele = DecimalField('Rx Antenna Elevation (degrees)')
    polar = SelectField('Polar',choices=[('0', 'Horizontal'), ('90', 'Vertical')])
    p_entry = DecimalField('Availability ( %/year )')
    xe = StringField('Site Location (Address)')
    rre = DecimalField('Rainrate (mm/h)')


class EquipFormEric(Form):
    cb0 = SelectField('Adaptative Modulation', choices=[('3','----'),('1', 'Yes'), ('0', 'No')],)
    cb1 = SelectField('Equipment',choices=[('0', '----')])#[('0', '----')],validators=())
    fe = SelectField('Frequency (GHz)',choices=[('0', '----')])
    carde = SelectField('Modem Card',choices=[('0', '----')])
    cpe = SelectField('Bandwidth (MHz)',choices=[('0', '----')])
    ref_mod = SelectField('Reference Modulation (Only for "Availability / Distance" graph)', choices=[('0', '----')])
    def validate(self):
        return True

class EquipForm(Form):
    cb0 = SelectField('XPIC', choices=[('3','----'),('1', 'Yes'), ('0', 'No')],)
    cb1 = SelectField('Equipment',choices=[('0', '----')])#[('0', '----')],validators=())
    fe = SelectField('Frequency (GHz)',choices=[('0', '----')])
    carde = SelectField('Modem Card + ODU',choices=[('0', '----')])
    cpe = SelectField('Bandwidth (MHz)',choices=[('0', '----')])
    ref_mod = SelectField('Reference Modulation (Only for "Availability / Distance" graph)', choices=[('0', '----')])
    am = SelectField('Adaptative Modulation', choices=[('3','----'),('1', 'Yes'), ('0', 'No')])
    def validate(self):
        return True

class ScenarioForm(Form):
    capa = DecimalField('Capacity (Mbps)')
    margin = DecimalField('Margin (Mbps)')
    peak = DecimalField('PIR (Mbps)')
    avaiPIR = DecimalField('Availability PIR ( %/year )')
    dist = DecimalField('Distance (km)')

class GlobalScenarioForm(Form):
    lp = FormField(LinkForm,label="Link Profil")
    sp = FormField(ScenarioForm,label="Scenario Profil")
    submit_button = SubmitField('Submit Form')

class MetricForm(Form):
    modp = BooleanField('Capacity / Distance')
    availp = BooleanField('Availability / Distance')
    rainp = BooleanField('Capacity / Availability')
    dist = DecimalField('Distance (km)')
    def validate(self):
        return True
class GlobalForm(Form):
    lp = FormField(LinkForm,label="Link Profil")
    ep = FormField(EquipForm, label="Equipment Profil")
    mf = FormField(MetricForm, label="Graphs")
    submit_button = SubmitField('Submit Form')

class GlobalFormEric(Form):
    lp = FormField(LinkForm,label="Link Profil")
    ep = FormField(EquipFormEric, label="Equipment Profil")
    mf = FormField(MetricForm, label="Graphs")
    submit_button = SubmitField('Submit Form')

if __name__ == '__main__':
    path = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')
    app.config['SIJAX_STATIC_PATH'] = path
    app.config['SIJAX_JSON_URI'] = '/static/js/sijax/json2.js'
    flask_sijax.Sijax(app)
    Bootstrap(app)

    app.config['SECRET_KEY'] = 'devkey'


    @flask_sijax.route(app, '/')
    def home():
        return render_template('home.html',title="Home")

    @flask_sijax.route(app,'/ericsson')
    def ericsson():
        mods_list = list()
        form = GlobalFormEric()
        def cb0Ch(obj_response,xpic):
            if obj_response!=None:
                obj_response.html('#ep-cb1','')
                obj_response.html_append('#ep-cb1', '<option>----</option>')
            if xpic == '1':
                db = tinydb.TinyDB('db_ericsson_AM.json')

            elif xpic == '0':
                db = tinydb.TinyDB('db_ericsson.json')
            i=0
            choix = list()
            for val in db.tables():
                if val != '_default':
                    if obj_response != None:
                        obj_response.html_append('#ep-cb1', '<option id='+str(i)+' value='+str(val)+' >'+val+'</option>')
                    choix.append((str(val)))
                    i=i+1
            form.ep.cb1.choices = choix
            choices_po['cb1']=choix
            return choix



        def equiCh(obj_response,xpic,equi):
            if obj_response != None:
                obj_response.html('#ep-fe','')
                obj_response.html_append('#ep-fe', '<option>----</option>')
            if xpic == '1':
                db = tinydb.TinyDB('db_ericsson_AM.json')

            elif xpic == '0':
                db = tinydb.TinyDB('db_ericsson.json')
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
                choix.append(str(val))

            def sortFreq(freq):
                return int(float(freq))
            if obj_response != None:
                choix.sort(key=sortFreq)
                for val in choix:
                    obj_response.html_append('#ep-fe', '<option id=' + str(i) + ' value=' + val + ' >' + val + '</option>')
            i = i + 1
            return choix




        def freqCh(obj_response,xpic,equi,freq):
            if obj_response != None:
                obj_response.html('#ep-carde','')
                obj_response.html_append('#ep-carde', '<option>----</option>')
            if xpic == '1':
                db = tinydb.TinyDB('db_ericsson_AM.json')

            elif xpic == '0':
                db = tinydb.TinyDB('db_ericsson.json')
            table = db.table(str(equi))
            mod_cards = list()
            i=0
            choix = list()
            for row in table:
                freq0 = row['BAND_DESIGNATOR']
                if str(row['MODEL']).split('/').__len__() > 3 and str(equi)=='MINI-LINK_6600':
                    mod_card = str(row['MODEL']).split('/')[1]
                else:
                    mod_card = str(int(float(freq))) + 'ASA'
                if str(freq0) == str(freq) and mod_card not in mod_cards:
                    mod_cards.append(mod_card)
                    if obj_response != None:
                        obj_response.html_append('#ep-carde', '<option id=' + str(i) + ' value=' + mod_card + ' >' + mod_card + '</option>')
            return mod_cards

            # for row in table:
            #     freq0 = row['BAND_DESIGNATOR']
            #     if equi == 'RTN900' and xpic == '1':
            #         mod_card = str(row['MODEL']).split('_')[-2]
            #     elif equi == 'RTN900' and xpic == '0':
            #         mod_card = str(row['MODEL']).split('_')[-1]
            #     else:
            #         mod_card = str(row['MODEL']).split('_')[0]
            #     if str(freq0) == str(freq) and mod_card not in mod_cards:
            #         i=i+1
            #         mod_card=str(mod_card)
            #         mod_cards.append(mod_card)
            #         choix.append(str(mod_card))
            #         if obj_response != None:
            #             obj_response.html_append('#ep-carde', '<option id=' + str(i) + ' value=' + mod_card + ' >' + mod_card + '</option>')
            # return mod_cards




        def cardCh(obj_response,xpic,equi,freq,carde):
            if obj_response != None:
                obj_response.html('#ep-cpe','')
                obj_response.html_append('#ep-cpe', '<option>----</option>')
            if xpic == '1':
                db = tinydb.TinyDB('db_ericsson_AM.json')

            elif xpic == '0':
                db = tinydb.TinyDB('db_ericsson.json')
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
                    choix.append(str(bandwidth))
                    if obj_response != None:
                        obj_response.html_append('#ep-cpe', '<option id=' + str(i) + ' value=' + bandwidth + ' >' + bandwidth + '</option>')
            choix = sorted(choix,key=float)
            return choix

        def sortMod(mod):
            if (re.match('BPSK', str(mod))):
                mod = '2QAM'
            return int(str(mod).split('QAM')[0])

        def bandwCh(obj_response,xpic,equi,freq,carde,bandw):

            if str(obj_response) != 'None':
                obj_response.html('#ep-ref_mod','')
                obj_response.html_append('#ep-ref_mod', '<option>----</option>')
            if xpic == '1':
                db = tinydb.TinyDB('db_ericsson_AM.json')

            elif xpic == '0':
                db = tinydb.TinyDB('db_ericsson.json')
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
            modulations.sort(reverse=True)
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



        def bkapp2(doc):
            link = form.lp
            ep = form.ep
            # <--- Variables --->
            d1a = float(link.gae.data)
            d1b = float(link.gbe.data)
            el = float(link.ele.data)
            URL = "https://nominatim.openstreetmap.org/search"
            geoloc = (0, 0)

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
                geoloc = (latitude, longitude)
                itur.models.itu837.change_version(6)
                rr = itur.models.itu837.rainfall_rate(latitude, longitude, 0.01).value
            else:
                rr = float(link.rre.data)
            tau = float(link.polar.data) # float(form.polar.data)
            # rr = float(rp.rre.data)
            p0 = 100 - float(link.p_entry.data)
            xpic = ep.cb0.data
            equip = ep.cb1.data
            freq = float(ep.fe.data)
            card = ep.carde.data
            bw = ep.cpe.data
            ref_mod = ep.ref_mod.data
            g1a = poubelle.getAntGain(d1a, freq)
            g1b = poubelle.getAntGain(d1b, freq)
            if form.mf.dist.data != None:
                dist = float(form.mf.dist.data)
            # items = SingleItem(d1a, d1b, el, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod)
            # table = SingleTable([items], classes=['table table-striped'])
            checks = [form.mf.rainp.data, form.mf.modp.data, form.mf.availp.data]
            graph = MakeGraphE(g1a, g1b, el, geoloc, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod, checks[0],
                              checks[1], checks[2])
            if(checks[0]):
                widgets = list()
                widgets2 = list()
                buttons = list()
                g1aS = Select(title="Antenna Diameter A (m)", value=str(d1a), options=link.gae.choices)
                g1bS = Select(title="Antenna Diameter B (m)", value=str(d1b), options=link.gae.choices)
                polarS = Select(title="Polarization", value=str(link.polar.data), options=link.polar.choices)
                # elS2 = Slider(title="Elevation (degrees)", value=float(el), start=0, end=45, step=10)
                rrS= Slider(title="Rainrate (mm/h)", value=float(rr), start=0, end=110, step=1)
                dS = Slider(title="Distance km", value=float(dist), start=0, end=25, step=0.5)

                add_button2 = Button(label='Add Line')
                refresh_button2 = Button(label='Refresh')
                widgets.append(g1aS)
                widgets.append(g1bS)
                widgets.append(polarS)
                widgets.append(rrS)
                widgets.append(dS)
                buttons.append(refresh_button2)
                xpicS = Select(title="Adaptative Modulation", value=str(xpic), options=ep.cb0.choices)
                equipS = Select(title="Equipment", value=str(equip), options=cb0Ch(None, xpic))
                freqS = Select(title="Frequency (GHz)", value=str(freq), options=equiCh(None, xpic, equip))
                cardS = Select(title="Modem + ODU", value=str(card), options=freqCh(None, xpic, equip, freq))
                bwS = Select(title="Bandwidth (MHz)", value=str(bw), options=cardCh(None, xpic, equip, freq, card))

                widgets2.append(xpicS)
                widgets2.append(equipS)
                widgets2.append(freqS)
                widgets2.append(cardS)
                widgets2.append(bwS)
                buttons.append(add_button2)

                colors = itertools.cycle(bkolor.Category10_10)
                source2 = plt.ColumnDataSource(
                    data=graph.plotRain(g1a, g1b, el, geoloc, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod,dist))

                graph1 = plt.figure(title='Capacity according to the availability',
                                    x_axis_label='Availability (%)', y_axis_label='Capacity (Mbps)')
                graph1.line('x', 'y', source=source2, color=next(colors), line_width=2)

                def update_data(event):
                    g1a = float(poubelle.getAntGain(float(g1aS.value.__str__()), freq))
                    g1b = float(poubelle.getAntGain(float(g1bS.value.__str__()), freq))

                    source2.data = plt.ColumnDataSource(
                        data=graph.plotRain(g1a, g1b, el, geoloc,
                                           rrS.value, float(polarS.value), p0, xpicS.value, equipS.value,
                                           float(freqS.value), cardS.value, float(bwS.value), ref_mod,dS.value)).data

                def add_data(event):
                    g1a = float(poubelle.getAntGain(float(g1aS.value.__str__()), freq))
                    g1b = float(poubelle.getAntGain(float(g1bS.value.__str__()), freq))
                    curr_dat = graph.plotRain(g1a, g1b, el, geoloc,
                                             rrS.value, float(polarS.value), p0, xpicS.value, equipS.value,
                                             float(freqS.value), cardS.value, float(bwS.value), ref_mod,dS.value)
                    graph1.line(curr_dat['x'], curr_dat['y'], color=next(colors), line_width=2)
                    graph1.add_tools(HoverTool())

                def xpicUp(attr, old, new):
                    equipS.options = list(cb0Ch(None, xpicS.value))

                def equipUp(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        equipS.value = new
                        freqS.options = list(equiCh(None, xpicS.value, new))

                def freqUp(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        freqS.value = new
                        cardS.options = list(freqCh(None, xpicS.value, equipS.value, new))
                        # bwS.options= list(cardCh(None,xpicS.value,equipS.value,freqS.value,cardS.value))

                def cardUp(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        cardS.value = new
                        bwS.options = list(cardCh(None, xpicS.value, equipS.value, freqS.value, new))

                def bwUp(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        bwS.value = new

                # graph2.add_tools(HoverTool())
                graph1.css_classes = ["container"]
                refresh_button2.on_click(handler=update_data)
                add_button2.on_click(handler=add_data)
                xpicS.on_change('value', xpicUp)
                equipS.on_change('value', equipUp)
                equipS.on_change('options', equipUp)
                freqS.on_change('value', freqUp)
                freqS.on_change('options', freqUp)
                cardS.on_change('value', cardUp)
                cardS.on_change('options', cardUp)
                bwS.on_change('options', bwUp)
                bwS.on_change('value', bwUp)

                doc.add_root(row(graph1, column(row(column(widgets), column(widgets2)), row(buttons))))
            if(checks[1]):
                widgets = list()
                widgets2 = list()
                buttons = list()
                g1as2 = Select(title="Antenna Diameter A (m)",value=str(d1a),options=link.gae.choices)
                g1bS2 = Select(title="Antenna Diameter B (m)",value=str(d1b),options=link.gae.choices)
                polarS2 = Select(title="Polarization",value=str(link.polar.data),options=link.polar.choices)
                #elS2 = Slider(title="Elevation (degrees)", value=float(el), start=0, end=45, step=10)
                rrS2 = Slider(title="Rainrate (mm/h)", value=float(rr), start=0, end=110, step=1)
                pS2 = TextInput(title="Availability",value=str(link.p_entry.data))#Spinner(title="Availability", value=float(link.p_entry.data), low=99, high=100,step=0.001)
                add_button2 = Button(label='Add Line')
                refresh_button2 = Button(label='Refresh')
                widgets.append(g1as2)
                widgets.append(g1bS2)
                widgets.append(polarS2)
                widgets.append(rrS2)
                widgets.append(pS2)
                buttons.append(refresh_button2)
                xpicS2 = Select(title="Adaptative Modulation",value=str(xpic),options=ep.cb0.choices)
                equipS2 = Select(title="Equipment",value=str(equip),options=cb0Ch(None,xpic))
                freqS2 = Select(title="Frequency (GHz)",value=str(freq),options=equiCh(None,xpic,equip))
                cardS2 = Select(title="Modem + ODU",value=str(card),options=freqCh(None,xpic,equip,freq))
                bwS2 = Select(title="Bandwidth (MHz)", value=str(bw), options=cardCh(None,xpic,equip,freq,card))

                widgets2.append(xpicS2)
                widgets2.append(equipS2)
                widgets2.append(freqS2)
                widgets2.append(cardS2)
                widgets2.append(bwS2)
                buttons.append(add_button2)

                colors = itertools.cycle(bkolor.Category10_10)
                source2 = plt.ColumnDataSource(
                    data=graph.plotMod(g1a, g1b, el, geoloc, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod))
                #source2.data['freq']=np.full(1999,freq)
                TOOLTIPS = [
                    ("Capacity", "@y"),
                    ("Distance", "@x"),
                    ("Link", "@infl"),
                    ("Equip","@infe")
                ]
                graph2 = plt.figure(title='Capacity according to the distance',
                                    x_axis_label='Distance (km)', y_axis_label='Capacity (Mbps)',tooltips=TOOLTIPS,sizing_mode='scale_both')
                graph2.line('x', 'y', source=source2,color=next(colors),line_width=2)
                def update_data2(event):

                    p0 = np.round(100.0 - float(pS2.value),5)
                    g1a = float(poubelle.getAntGain(float(g1as2.value.__str__()), freq))
                    g1b = float(poubelle.getAntGain(float(g1bS2.value.__str__()), freq))
            
                    source2.data = plt.ColumnDataSource(
                        data=graph.plotMod(g1a,g1b, el, geoloc,
                                  rrS2.value,float(polarS2.value), p0,xpicS2.value, equipS2.value, float(freqS2.value), cardS2.value, float(bwS2.value), ref_mod)).data


                def add_data2(event):
                    p0 = 100.0 - float(pS2.value)
                    g1a = float(poubelle.getAntGain(float(g1as2.value.__str__()), freq))
                    g1b =float(poubelle.getAntGain(float(g1bS2.value.__str__()), freq))
                    curr_dat = graph.plotMod(g1a,g1b, el, geoloc,
                                  rrS2.value,float(polarS2.value), p0, xpicS2.value, equipS2.value, float(freqS2.value), cardS2.value, float(bwS2.value), ref_mod)
                    graph2.line(curr_dat['x'],curr_dat['y'], color = next(colors),line_width=2)
                    graph2.add_tools(HoverTool())

                def xpicUp2(attr,old,new):
                    equipS2.options = list(cb0Ch(None,xpicS2.value))

                def equipUp2(attr,old,new):
                    if new != []:
                        if isinstance(new,list):
                            new = new[0]
                        equipS2.value = new
                        freqS2.options= list(equiCh(None,xpicS2.value,new))

                def freqUp2(attr,old,new):
                    if new != []:
                        if isinstance(new,list):
                            new=new[0]
                        freqS2.value = new
                        cardS2.options= list(freqCh(None,xpicS2.value,equipS2.value,new))
                        # bwS2.options= list(cardCh(None,xpicS.value,equipS2.value,freqS2.value,cardS2.value))

                def cardUp2(attr,old,new):
                    if new != []:
                        if isinstance(new,list):
                            new=new[0]
                        cardS2.value = new
                        bwS2.options= list(cardCh(None,xpicS2.value,equipS2.value,freqS2.value,new))
                def bwUp2(attr,old,new):
                    if new != []:
                        if isinstance(new,list):
                            new=new[0]
                        bwS2.value = new



                #graph2.add_tools(HoverTool())
                graph2.css_classes = ["container"]
                refresh_button2.on_click(handler=update_data2)
                add_button2.on_click(handler=add_data2)
                xpicS2.on_change('value',xpicUp2)
                equipS2.on_change('value',equipUp2)
                equipS2.on_change('options', equipUp2)
                freqS2.on_change('value',freqUp2)
                freqS2.on_change('options',freqUp2)
                cardS2.on_change('value',cardUp2)
                cardS2.on_change('options', cardUp2)
                bwS2.on_change('options',bwUp2)
                bwS2.on_change('value',bwUp2)

                bkrainp=row(graph2, column(row(column(widgets),column(widgets2)),row(buttons)))
                bkrainp.sizing_mode='scale_both'
                bkrainp.css_classes=["truc"]
                bkrainp.name = "encule"
                doc.add_root(bkrainp)
            if (checks[2]):
                widgets = list()
                widgets2 = list()
                buttons = list()
                lines = list()
                g1aS3 = Select(title="Antenna Diameter A (m)", value=str(d1a), options=link.gae.choices)
                g1bS23 = Select(title="Antenna Diameter B (m)", value=str(d1b), options=link.gae.choices)
                polarS3 = Select(title="Polarization", value=str(link.polar.data), options=link.polar.choices)
                # elS2 = Slider(title="Elevation (degrees)", value=float(el), start=0, end=45, step=10)
                rrS3 = Slider(title="Rainrate (mm/h)", value=float(rr), start=0, end=110, step=1)

                add_button3 = Button(label='Add Line')
                refresh_button3 = Button(label='Refresh')
                widgets.append(g1aS3)
                widgets.append(g1bS23)
                widgets.append(polarS3)
                widgets.append(rrS3)
                buttons.append(refresh_button3)
                xpicS3 = Select(title="Adaptative Modulation", value=str(xpic), options=ep.cb0.choices)
                equipS3 = Select(title="Equipment", value=str(equip), options=cb0Ch(None, xpic))
                freqS3 = Select(title="Frequency (GHz)", value=str(freq), options=equiCh(None, xpic, equip))
                cardS3 = Select(title="Modem + ODU", value=str(card), options=freqCh(None, xpic, equip, freq))
                bwS3 = Select(title="Bandwidth (MHz)", value=str(bw), options=cardCh(None, xpic, equip, freq, card))
                refS3 = Select(title="Reference Modulation", value=str(ref_mod), options=bandwCh(None, xpic, equip, freq, card,bw))

                widgets2.append(xpicS3)
                widgets2.append(equipS3)
                widgets2.append(freqS3)
                widgets2.append(cardS3)
                widgets2.append(bwS3)
                widgets2.append(refS3)
                buttons.append(add_button3)

                colors3 = itertools.cycle(bkolor.Category10_10)
                source3 = plt.ColumnDataSource(
                    data=graph.plotAvail(g1a, g1b, el, geoloc, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod))
                graph3 = plt.figure(title='Availability according to the distance',
                                    x_axis_label='Distance (km)', y_axis_label='Availability (%)',)
                l = graph3.line('x', 'y', source=source3, color=next(colors3),line_width=2)
                lines.append((str(rr),[l]))
                # graph3.plot_width = 1000
                # graph3.plot_height = 800
                def update_data3(event):
                    g1a = float(poubelle.getAntGain(float(g1aS3.value.__str__()), freq))
                    g1b = float(poubelle.getAntGain(float(g1bS23.value.__str__()), freq))
                    # truc = [g1a,g1b,p0,rrS2.value,float(polarS.value),xpicS.value, equipS.value, float(freqS.value), cardS.value, float(bwS.value), ref_mod, amS.value]
                    # print(truc)
                    # plotAvail(self,g1a,g1b,el,geoloc,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,am)

                    source3.data = plt.ColumnDataSource(
                        data=graph.plotAvail(g1a, g1b, el, geoloc,
                                           rrS3.value, float(polarS3.value), p0, xpicS3.value, equipS3.value,
                                           float(freqS3.value), cardS3.value, float(bwS3.value), refS3.value)).data

                def add_data3(event):
                    g1a = float(poubelle.getAntGain(float(g1aS3.value.__str__()), freq))
                    g1b = float(poubelle.getAntGain(float(g1bS23.value.__str__()), freq))
                    curr_dat = graph.plotAvail(g1a, g1b, el, geoloc,
                                             rrS3.value, float(polarS3.value), p0, xpicS3.value, equipS3.value,
                                             float(freqS3.value), cardS3.value, float(bwS3.value), refS3.value)
                    l = graph3.line(curr_dat['x'], curr_dat['y'], color=next(colors3),line_width=2)
                    graph3.add_tools(HoverTool())
                    lines.append((str(rrS3.value), [l]))
                    legend.items = lines

                def xpicUp3(attr, old, new):
                    equipS3.options = list(cb0Ch(None, xpicS3.value))

                def equipUp3(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        equipS3.value = new
                        freqS3.options = list(equiCh(None, xpicS3.value, new))

                def freqUp3(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        freqS3.value = new
                        cardS3.options = list(freqCh(None, xpicS3.value, equipS3.value, new))
                        # bwS.options= list(cardCh(None,xpicS.value,equipS.value,freqS.value,cardS.value))

                def cardUp3(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        cardS3.value = new
                        bwS3.options = list(cardCh(None, xpicS3.value, equipS3.value, freqS3.value, new))

                def bwUp3(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        bwS3.value = new
                        refS3.options = list(bandwCh(None, xpicS3.value, equipS3.value, freqS3.value,cardS3.value,new))

                def refUp3(attr,old,new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        refS3.value = new

                legend = Legend(items=lines)
                graph3.add_tools(HoverTool())
                graph3.css_classes = ["container"]
                refresh_button3.on_click(handler=update_data3)
                add_button3.on_click(handler=add_data3)
                xpicS3.on_change('value', xpicUp3)
                equipS3.on_change('value', equipUp3)
                equipS3.on_change('options', equipUp3)
                freqS3.on_change('value', freqUp3)
                freqS3.on_change('options', freqUp3)
                cardS3.on_change('value', cardUp3)
                cardS3.on_change('options', cardUp3)
                bwS3.on_change('options', bwUp3)
                bwS3.on_change('value', bwUp3)
                refS3.on_change('options', refUp3)
                refS3.on_change('value', refUp3)
                doc.add_root(row(graph3, column(row(column(widgets),column(widgets2)),row(buttons))))
                #doc.add_root(bk.layouts.grid(children=[[graph3,[[widgets,widgets2],[buttons]]]]))

        def get_free_tcp_port():
            tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp.bind(('', 0))
            addr, port = tcp.getsockname()
            tcp.close()
            return port

        session_port = get_free_tcp_port()
        addr = 'localhost'
        if len(sys.argv) >1 : addr = sys.argv[1]

        def bk_worker():
            # Can't pass num_procs > 1 in this configuration. If you need to run multiple
            # processes, see e.g. flask_gunicorn_embed.py
            
            server = Server({'/bkapp2': bkapp2},port=session_port,io_loop=IOLoop(), allow_websocket_origin=[addr])
            server.start()
            server.io_loop.start()

        if form.is_submitted():
            Thread(target=bk_worker).start()
            script = server_document('http://'+addr+':'+str(session_port)+'/bkapp2')
            return render_template('graphs.html',graph1=script,title='Graphs viewer')#,rrS=script,graph1=div,graph2=file_html(graph1,CDN,'plot1'),graph3=file_html(graph1,CDN,'plot1'),js_resources=js_resources,css_resources=css_resources)
            # return render_template('graphs.html', graph=html)

        return render_template('index.html', form=form,title='Ericsson profil')

    @flask_sijax.route(app,'/huawei')
    def huawei():
        mods_list = list()
        form = GlobalForm()
        def cb0Ch(obj_response,xpic):
            db = tinydb.TinyDB('db_huawei.json')
            if obj_response!=None:
                obj_response.html('#ep-cb1','')
                obj_response.html_append('#ep-cb1', '<option>----</option>')
            if xpic == '1':
                db = tinydb.TinyDB('db_huawei_XPIC.json')

            elif xpic == '0':
                db = tinydb.TinyDB('db_huawei.json')
            i=0
            choix = list()
            for val in db.tables():
                if val != '_default':
                    if obj_response != None:
                        obj_response.html_append('#ep-cb1', '<option id='+str(i)+' value='+str(val)+' >'+val+'</option>')
                    choix.append((str(val)))
                    i=i+1
            form.ep.cb1.choices = choix
            choices_po['cb1']=choix
            return choix



        def equiCh(obj_response,xpic,equi):
            db = tinydb.TinyDB('db_huawei.json')
            if obj_response != None:
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
                choix.append(str(val))
                if obj_response != None:
                    obj_response.html_append('#ep-fe', '<option id='+str(i)+' value='+val+' >'+val+'</option>')
                i=i+1
            return choix




        def freqCh(obj_response,xpic,equi,freq):
            db = tinydb.TinyDB('db_huawei.json')
            if obj_response != None:
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
                    choix.append(str(mod_card))
                    if obj_response != None:
                        obj_response.html_append('#ep-carde', '<option id=' + str(i) + ' value=' + mod_card + ' >' + mod_card + '</option>')
            return mod_cards




        def cardCh(obj_response,xpic,equi,freq,carde):
            db = tinydb.TinyDB('db_huawei.json')
            if obj_response != None:
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
                    choix.append(str(bandwidth))
                    if obj_response != None:
                        obj_response.html_append('#ep-cpe', '<option id=' + str(i) + ' value=' + bandwidth + ' >' + bandwidth + '</option>')
            form.ep.cpe.choices = choix
            return choix

        def sortMod(mod):
            if (re.match('BPSK', str(mod))):
                mod = '2QAM'
            if (re.match('QPSK', str(mod))):
                mod = '4QAM'
            if (re.match('8PSK', str(mod))):
                mod = '8QAM'
            return int(str(mod).split('QAM')[0])

        def bandwCh(obj_response,xpic,equi,freq,carde,bandw):
            db = tinydb.TinyDB('db_huawei.json')
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



        def bkapp(doc):
            link = form.lp
            ep = form.ep
            # <--- Variables --->
            d1a = float(link.gae.data)
            d1b = float(link.gbe.data)
            el = float(link.ele.data)
            URL = "https://nominatim.openstreetmap.org/search"
            geoloc = (0, 0)
            if form.mf.dist.data != None:
                dist = float(form.mf.dist.data)
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
                geoloc = (latitude, longitude)
                itur.models.itu837.change_version(6)
                rr = itur.models.itu837.rainfall_rate(latitude, longitude, 0.01).value
            else:
                rr = float(link.rre.data)
            tau = float(link.polar.data) # float(form.polar.data)
            # rr = float(rp.rre.data)
            p0 = 100 - float(link.p_entry.data)
            xpic = ep.cb0.data
            equip = ep.cb1.data
            freq = float(ep.fe.data)
            card = ep.carde.data
            bw = ep.cpe.data
            ref_mod = ep.ref_mod.data
            g1a = poubelle.getAntGain(d1a, freq)
            g1b = poubelle.getAntGain(d1b, freq)
            am = ep.am.data
            # items = SingleItem(d1a, d1b, el, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod, am)
            # table = SingleTable([items], classes=['table table-striped'])
            checks = [form.mf.rainp.data, form.mf.modp.data, form.mf.availp.data]
            graph = MakeGraph(g1a, g1b, el, geoloc, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod,am,checks[0],
                              checks[1], checks[2])
            if(checks[0]):
                widgets = list()
                widgets2 = list()
                buttons = list()
                g1aS = Select(title="Antenna Diameter A (m)", value=str(d1a), options=link.gae.choices)
                g1bS = Select(title="Antenna Diameter B (m)", value=str(d1b), options=link.gae.choices)
                polarS = Select(title="Polarization", value=str(link.polar.data), options=link.polar.choices)
                # elS2 = Slider(title="Elevation (degrees)", value=float(el), start=0, end=45, step=10)
                rrS= Slider(title="Rainrate (mm/h)", value=float(rr), start=0, end=110, step=1)
                dS = Slider(title="Distance km", value=float(dist), start=0, end=25, step=0.5)

                add_button2 = Button(label='Add Line')
                refresh_button2 = Button(label='Refresh')
                widgets.append(g1aS)
                widgets.append(g1bS)
                widgets.append(polarS)
                widgets.append(rrS)
                widgets.append(dS)
                buttons.append(refresh_button2)
                xpicS = Select(title="Adaptative Modulation", value=str(xpic), options=ep.cb0.choices)
                equipS = Select(title="Equipment", value=str(equip), options=cb0Ch(None, xpic))
                freqS = Select(title="Frequency (GHz)", value=str(freq), options=equiCh(None, xpic, equip))
                cardS = Select(title="Modem + ODU", value=str(card), options=freqCh(None, xpic, equip, freq))
                bwS = Select(title="Bandwidth (MHz)", value=str(bw), options=cardCh(None, xpic, equip, freq, card))

                widgets2.append(xpicS)
                widgets2.append(equipS)
                widgets2.append(freqS)
                widgets2.append(cardS)
                widgets2.append(bwS)
                buttons.append(add_button2)

                colors = itertools.cycle(bkolor.Category10_10)
                source2 = plt.ColumnDataSource(
                    data=graph.plotRain(g1a, g1b, el, geoloc, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod,am,dist))

                graph1 = plt.figure(title='Capacity according to the availability',
                                    x_axis_label='Availability (%)', y_axis_label='Capacity (Mbps)')
                graph1.line('x', 'y', source=source2, color=next(colors), line_width=2)

                def update_data(event):
                    g1a = float(poubelle.getAntGain(float(g1aS.value.__str__()), freq))
                    g1b = float(poubelle.getAntGain(float(g1bS.value.__str__()), freq))

                    source2.data = plt.ColumnDataSource(
                        data=graph.plotRain(g1a, g1b, el, geoloc,
                                           rrS.value, float(polarS.value), p0, xpicS.value, equipS.value,
                                           float(freqS.value), cardS.value, float(bwS.value), ref_mod,am,dS.value)).data

                def add_data(event):
                    g1a = float(poubelle.getAntGain(float(g1aS.value.__str__()), freq))
                    g1b = float(poubelle.getAntGain(float(g1bS.value.__str__()), freq))
                    curr_dat = graph.plotRain(g1a, g1b, el, geoloc,
                                             rrS.value, float(polarS.value), p0, xpicS.value, equipS.value,
                                             float(freqS.value), cardS.value, float(bwS.value), ref_mod,am,dS.value)
                    graph1.line(curr_dat['x'], curr_dat['y'], color=next(colors), line_width=2)
                    graph1.add_tools(HoverTool())

                def xpicUp(attr, old, new):
                    equipS.options = list(cb0Ch(None, xpicS.value))

                def equipUp(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        equipS.value = new
                        freqS.options = list(equiCh(None, xpicS.value, new))

                def freqUp(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        freqS.value = new
                        cardS.options = list(freqCh(None, xpicS.value, equipS.value, new))
                        # bwS.options= list(cardCh(None,xpicS.value,equipS.value,freqS.value,cardS.value))

                def cardUp(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        cardS.value = new
                        bwS.options = list(cardCh(None, xpicS.value, equipS.value, freqS.value, new))

                def bwUp(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        bwS.value = new

                # graph2.add_tools(HoverTool())
                graph1.css_classes = ["container"]
                refresh_button2.on_click(handler=update_data)
                add_button2.on_click(handler=add_data)
                xpicS.on_change('value', xpicUp)
                equipS.on_change('value', equipUp)
                equipS.on_change('options', equipUp)
                freqS.on_change('value', freqUp)
                freqS.on_change('options', freqUp)
                cardS.on_change('value', cardUp)
                cardS.on_change('options', cardUp)
                bwS.on_change('options', bwUp)
                bwS.on_change('value', bwUp)

                doc.add_root(row(graph1, column(row(column(widgets), column(widgets2)), row(buttons))))

            if(checks[1]):
                widgets = list()
                widgets2 = list()
                buttons = list()
                g1as2 = Select(title="Antenna Diameter A (m)",value=str(d1a),options=link.gae.choices)
                g1bS2 = Select(title="Antenna Diameter B (m)",value=str(d1b),options=link.gae.choices)
                polarS2 = Select(title="Polarization",value=str(link.polar.data),options=link.polar.choices)
                #elS2 = Slider(title="Elevation (degrees)", value=float(el), start=0, end=45, step=10)
                rrS2 = Slider(title="Rainrate (mm/h)", value=float(rr), start=0, end=110, step=1)
                pS = TextInput(title="Availability",value=str(link.p_entry.data))#Spinner(title="Availability", value=float(link.p_entry.data), low=99, high=100,step=0.001)
                add_button2 = Button(label='Add Line')
                refresh_button2 = Button(label='Refresh')

                widgets.append(g1as2)
                widgets.append(g1bS2)
                widgets.append(polarS2)
                widgets.append(rrS2)
                widgets.append(pS)

                buttons.append(refresh_button2)
                xpicS2 = Select(title="XPIC",value=str(xpic),options=ep.cb0.choices)
                equipS2 = Select(title="Equipment",value=str(equip),options=cb0Ch(None,xpic))
                freqS2 = Select(title="Frequency (GHz)",value=str(freq),options=equiCh(None,xpic,equip))
                cardS2 = Select(title="Modem + ODU",value=str(card),options=freqCh(None,xpic,equip,freq))
                bwS2 = Select(title="Bandwidth (MHz)", value=str(bw), options=cardCh(None,xpic,equip,freq,card))
                amS2 = Select(title="Adaptative Modulation", value=str(am), options=ep.am.choices)

                widgets2.append(xpicS2)
                widgets2.append(equipS2)
                widgets2.append(freqS2)
                widgets2.append(cardS2)
                widgets2.append(bwS2)
                widgets2.append(amS2)
                buttons.append(add_button2)

                colors = itertools.cycle(bkolor.Category10_10)
                source2 = plt.ColumnDataSource(
                    data=graph.plotMod(g1a, g1b, el, geoloc, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod, am))
                #source2.data['freq']=np.full(1999,freq)
                TOOLTIPS = [
                    ("Capacity", "@y"),
                    ("Distance", "@x"),
                    ("Link", "@infl"),
                    ("Equip","@infe")
                ]
                graph2 = plt.figure(title='Capacity according to the distance',
                                    x_axis_label='Distance (km)', y_axis_label='Capacity (Mbps)',tooltips=TOOLTIPS,sizing_mode='scale_both')
                graph2.line('x', 'y', source=source2,color=next(colors),line_width=2)
                def update_data2(event):

                    p0 = np.round(100.0 - float(pS.value),5)
                    g1a = float(poubelle.getAntGain(float(g1as2.value.__str__()), freq))
                    g1b = float(poubelle.getAntGain(float(g1bS2.value.__str__()), freq))
                    # truc = [g1a,g1b,p0,rrS2.value,float(polarS2.value),xpicS2.value, equipS2.value, float(freqS2.value), cardS2.value, float(bwS2.value), ref_mod, amS2.value]
                    # print(truc)
                    #plotMod(self,g1a,g1b,el,geoloc,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,am)
                    source2.data = plt.ColumnDataSource(
                        data=graph.plotMod(g1a,g1b, el, geoloc,
                                  rrS2.value,float(polarS2.value), p0,xpicS2.value, equipS2.value, float(freqS2.value), cardS2.value, float(bwS2.value), ref_mod, amS2.value)).data


                def add_data2(event):
                    p0 = 100.0 - float(pS.value)
                    g1a = float(poubelle.getAntGain(float(g1as2.value.__str__()), freq))
                    g1b =float(poubelle.getAntGain(float(g1bS2.value.__str__()), freq))
                    curr_dat = graph.plotMod(g1a,g1b, el, geoloc,
                                  rrS2.value,float(polarS2.value), p0, xpicS2.value, equipS2.value, float(freqS2.value), cardS2.value, float(bwS2.value), ref_mod, amS2.value)
                    graph2.line(curr_dat['x'],curr_dat['y'], color = next(colors),line_width=2)
                    #graph2.add_tools(HoverTool())

                def xpicUp2(attr,old,new):
                    equipS2.options = list(cb0Ch(None,xpicS2.value))

                def equipUp2(attr,old,new):
                    if new != []:
                        if isinstance(new,list):
                            new = new[0]
                        equipS2.value = new
                        freqS2.options= list(equiCh(None,xpicS2.value,new))

                def freqUp2(attr,old,new):
                    if new != []:
                        if isinstance(new,list):
                            new=new[0]
                        freqS2.value = new
                        cardS2.options= list(freqCh(None,xpicS2.value,equipS2.value,new))
                        # bwS2.options= list(cardCh(None,xpicS.value,equipS2.value,freqS2.value,cardS2.value))

                def cardUp2(attr,old,new):
                    if new != []:
                        if isinstance(new,list):
                            new=new[0]
                        cardS2.value = new
                        bwS2.options= list(cardCh(None,xpicS2.value,equipS2.value,freqS2.value,new))
                def bwUp2(attr,old,new):
                    if new != []:
                        if isinstance(new,list):
                            new=new[0]
                        bwS2.value = new



                #graph2.add_tools(HoverTool())
                graph2.css_classes = ["container"]
                refresh_button2.on_click(handler=update_data2)
                add_button2.on_click(handler=add_data2)
                xpicS2.on_change('value',xpicUp2)
                equipS2.on_change('value',equipUp2)
                equipS2.on_change('options', equipUp2)
                freqS2.on_change('value',freqUp2)
                freqS2.on_change('options',freqUp2)
                cardS2.on_change('value',cardUp2)
                cardS2.on_change('options', cardUp2)
                bwS2.on_change('options',bwUp2)
                bwS2.on_change('value',bwUp2)

                bkrainp=row(graph2, column(row(column(widgets),column(widgets2)),row(buttons)))
                bkrainp.sizing_mode='scale_both'
                bkrainp.css_classes=["truc"]
                bkrainp.name = "encule"
                doc.add_root(bkrainp)
            if (checks[2]):
                widgets = list()
                widgets2 = list()
                buttons = list()
                lines = list()
                g1aS3 = Select(title="Antenna Diameter A (m)", value=str(d1a), options=link.gae.choices)
                g1bS3 = Select(title="Antenna Diameter B (m)", value=str(d1b), options=link.gae.choices)
                polarS3 = Select(title="Polarization", value=str(link.polar.data), options=link.polar.choices)
                # elS2 = Slider(title="Elevation (degrees)", value=float(el), start=0, end=45, step=10)
                rrS3 = Slider(title="Rainrate (mm/h)", value=float(rr), start=0, end=110, step=1)
                pS3 = TextInput(title="Availability", value=str(
                    link.p_entry.data))  # Spinner(title="Availability", value=float(link.p_entry.data), low=99, high=100,step=0.001)
                add_button3 = Button(label='Add Line')
                refresh_button3 = Button(label='Refresh')
                widgets.append(g1aS3)
                widgets.append(g1bS3)
                widgets.append(polarS3)
                widgets.append(rrS3)
                widgets.append(pS3)
                buttons.append(refresh_button3)
                xpicS3 = Select(title="XPIC", value=str(xpic), options=ep.cb0.choices)
                equipS3 = Select(title="Equipment", value=str(equip), options=cb0Ch(None, xpic))
                freqS3 = Select(title="Frequency (GHz)", value=str(freq), options=equiCh(None, xpic, equip))
                cardS3 = Select(title="Modem + ODU", value=str(card), options=freqCh(None, xpic, equip, freq))
                bwS3 = Select(title="Bandwidth (MHz)", value=str(bw), options=cardCh(None, xpic, equip, freq, card))
                refS3 = Select(title="Reference Modulation", value=str(ref_mod), options=bandwCh(None, xpic, equip, freq, card,bw))
                amS3 = Select(title="Adaptative Modulation", value=str(am), options=ep.am.choices)

                widgets2.append(xpicS3)
                widgets2.append(equipS3)
                widgets2.append(freqS3)
                widgets2.append(cardS3)
                widgets2.append(bwS3)
                widgets.append(amS3)
                widgets2.append(refS3)
                buttons.append(add_button3)

                colors3 = itertools.cycle(bkolor.Category10_10)
                source3 = plt.ColumnDataSource(
                    data=graph.plotAvail(g1a, g1b, el, geoloc, rr, tau, p0, xpic, equip, freq, card, bw, ref_mod, am))
                graph3 = plt.figure(title='Capacity according to the distance',
                                    x_axis_label='Distance (km)', y_axis_label='Capacity (Mbps)',sizing_mode='scale_both')
                l = graph3.line('x', 'y', source=source3, color=next(colors3),line_width=2)
                lines.append((str(rr),[l]))
                # graph3.plot_width = 1000
                # graph3.plot_height = 800
                def update_data3(event):

                    p0 = np.round(100.0 - float(pS3.value), 5)
                    g1a = float(poubelle.getAntGain(float(g1aS3.value.__str__()), freq))
                    g1b = float(poubelle.getAntGain(float(g1bS3.value.__str__()), freq))
                    # truc = [g1a,g1b,p0,rrS2.value,float(polarS.value),xpicS.value, equipS.value, float(freqS.value), cardS.value, float(bwS.value), ref_mod, amS.value]
                    # print(truc)
                    # plotAvail(self,g1a,g1b,el,geoloc,rr,tau,p0,xpic,equip,freq,card,bw,ref_mod,am)

                    source3.data = plt.ColumnDataSource(
                        data=graph.plotAvail(g1a, g1b, el, geoloc,
                                           rrS3.value, float(polarS3.value), p0, xpicS3.value, equipS3.value,
                                           float(freqS3.value), cardS3.value, float(bwS3.value), refS3.value, amS3.value)).data

                def add_data3(event):
                    p0 = 100.0 - float(pS3.value)
                    g1a = float(poubelle.getAntGain(float(g1aS3.value.__str__()), freq))
                    g1b = float(poubelle.getAntGain(float(g1bS3.value.__str__()), freq))
                    curr_dat = graph.plotAvail(g1a, g1b, el, geoloc,
                                             rrS3.value, float(polarS3.value), p0, xpicS3.value, equipS3.value,
                                             float(freqS3.value), cardS3.value, float(bwS3.value), refS3.value, amS3.value)
                    l = graph3.line(curr_dat['x'], curr_dat['y'], color=next(colors3),line_width=2)
                    graph3.add_tools(HoverTool())
                    lines.append((str(rrS3.value), [l]))
                    legend.items = lines

                def xpicUp3(attr, old, new):
                    equipS3.options = list(cb0Ch(None, xpicS3.value))

                def equipUp3(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        equipS3.value = new
                        freqS3.options = list(equiCh(None, xpicS3.value, new))

                def freqUp3(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        freqS3.value = new
                        cardS3.options = list(freqCh(None, xpicS3.value, equipS3.value, new))
                        # bwS.options= list(cardCh(None,xpicS.value,equipS.value,freqS.value,cardS.value))

                def cardUp3(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        cardS3.value = new
                        bwS3.options = list(cardCh(None, xpicS3.value, equipS3.value, freqS3.value, new))

                def bwUp3(attr, old, new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        bwS3.value = new
                        refS3.options = list(bandwCh(None, xpicS3.value, equipS3.value, freqS3.value,cardS3.value,new))

                def refUp3(attr,old,new):
                    if new != []:
                        if isinstance(new, list):
                            new = new[0]
                        refS3.value = new

                legend = Legend(items=lines)
                graph3.add_tools(HoverTool())
                graph3.css_classes = ["container"]
                refresh_button3.on_click(handler=update_data3)
                add_button3.on_click(handler=add_data3)
                xpicS3.on_change('value', xpicUp3)
                equipS3.on_change('value', equipUp3)
                equipS3.on_change('options', equipUp3)
                freqS3.on_change('value', freqUp3)
                freqS3.on_change('options', freqUp3)
                cardS3.on_change('value', cardUp3)
                cardS3.on_change('options', cardUp3)
                bwS3.on_change('options', bwUp3)
                bwS3.on_change('value', bwUp3)
                refS3.on_change('options', refUp3)
                refS3.on_change('value', refUp3)
                doc.add_root(row(graph3, column(row(column(widgets),column(widgets2)),row(buttons))))
                #doc.add_root(bk.layouts.grid(children=[[graph3,[[widgets,widgets2],[buttons]]]]))

        def get_free_tcp_port():
            tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp.bind(('', 0))
            addr, port = tcp.getsockname()
            tcp.close()
            return port

        session_port = get_free_tcp_port()
        addr = 'localhost'
        if len(sys.argv) >1: addr = sys.argv[1]

        def bk_worker():
            # Can't pass num_procs > 1 in this configuration. If you need to run multiple
            # processes, see e.g. flask_gunicorn_embed.py

            server = Server({'/bkapp': bkapp},port=session_port,io_loop=IOLoop(), allow_websocket_origin=[addr])
            server.start()
            server.io_loop.start()
            print('pouet'+str(server.port))
            server.run_until_shutdown()

        if form.is_submitted():
            from threading import Thread
            Thread(target=bk_worker).start()
            script = server_document('http://'+addr+':'+str(session_port)+'/bkapp')
            return render_template('graphs.html',graph1=script,title='Graphs viewer')#,rrS=script,graph1=div,graph2=file_html(graph1,CDN,'plot1'),graph3=file_html(graph1,CDN,'plot1'),js_resources=js_resources,css_resources=css_resources)
            # return render_template('graphs.html', graph=html)

        return render_template('index.html', form=form,title='Huawei profil')

    @flask_sijax.route(app,'/scenario')
    def coucou():
        form = GlobalScenarioForm()
        if form.is_submitted():
            link = form.lp
            URL = "https://nominatim.openstreetmap.org/search"
            location = str(link.xe.data)
            #key = 'AIzaSyA3nLe6yUCTTMB82u1LTuWoyGJGvr8gBZg'
            location_detail = {'q': location,'format':'json'}
            if location != '':
                r = requests.get(url=URL, params=location_detail)
                data = r.json()
                latitude = float(data[0]['lat'])
                longitude = float(data[0]['lon'])
                poubelle.GEOLOCATE = (latitude, longitude)
            poubelle.DIA1 = float(link.gae.data)
            poubelle.DIA2 = float(link.gbe.data)
            poubelle.ELEVATION = float(link.ele.data)
            if form.sp.peak.data != None and form.sp.avaiPIR.data:
                poubelle.PIR = float(form.sp.peak.data)
                poubelle.AVAI_PIR = float(form.sp.avaiPIR.data)


            poubelle.MARG = float(form.sp.margin.data)
            poubelle.POLAR = 0 if link.polar.data=='h' else 90 # float(form.polar.data)
            if link.rre.data != None:
                poubelle.RR = float(link.rre.data)
            poubelle.AVAILABILITY  = float(link.p_entry.data)
            poubelle.CIR = float(form.sp.capa.data)
            [eb_stab,ex_tab,e_mw_tab,mw_stab,mw_xtab] = poubelle.getScenarii(0,float(form.sp.capa.data),float(link.p_entry.data))
            return render_template('tables.html',table=eb_stab,ex_tab=ex_tab,e_mw_tab=e_mw_tab,mw_stab=mw_stab,mw_xtab=mw_xtab,title='Huawei scenario')

        return render_template('index.html',form=form,title='Huawei scenario')

    @flask_sijax.route(app,'/scenarioe')
    def scenarEric():
        form = GlobalScenarioForm()
        if form.is_submitted():
            link = form.lp
            URL = "https://nominatim.openstreetmap.org/search"
            location = str(link.xe.data)
            #key = 'AIzaSyA3nLe6yUCTTMB82u1LTuWoyGJGvr8gBZg'
            location_detail = {'q': location,'format':'json'}
            if location != '':
                r = requests.get(url=URL, params=location_detail)
                data = r.json()
                latitude = float(data[0]['lat'])
                longitude = float(data[0]['lon'])
                poubelle_2.GEOLOCATE = (latitude, longitude)
            poubelle_2.DIA1 = float(link.gae.data)
            poubelle_2.DIA2 = float(link.gbe.data)
            poubelle_2.ELEVATION = float(link.ele.data)

            if form.sp.peak.data != None and form.sp.avaiPIR.data!=None:
                poubelle_2.PIR = float(form.sp.peak.data)
                poubelle_2.AVAI_PIR = float(form.sp.avaiPIR.data)

            poubelle_2.MARG = float(form.sp.margin.data)
            poubelle_2.POLAR = 0 if link.polar.data=='h' else 90 # float(form.polar.data)
            if link.rre.data != None:
                poubelle_2.RR = float(link.rre.data)
            poubelle_2.AVAILABILITY  = float(link.p_entry.data)
            poubelle_2.CIR = float(form.sp.capa.data)
            [eb_stab,ex_tab,e_mw_tab,mw_stab,mw_xtab] = poubelle_2.getScenarii(0,float(form.sp.capa.data),float(link.p_entry.data))
            return render_template('tables.html',table=eb_stab,ex_tab=ex_tab,e_mw_tab=e_mw_tab,mw_stab=mw_stab,mw_xtab=mw_xtab,title='Ericsson scenario')

        return render_template('index.html',form=form,title='Ericsson scenario')



    app.run(host='0.0.0.0',port=80,debug=True)