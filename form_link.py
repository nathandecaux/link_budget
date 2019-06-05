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


graphs = list()
graphs = [None,None,None]
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
    dist = DecimalField('Distance (km)')

class GlobalScenarioForm(Form):
    lp = FormField(LinkForm,label="Link Profil")
    sp = FormField(ScenarioForm,label="Scenario Profil")
    submit_button = SubmitField('Submit Form')

class MetricForm(Form):
    rainp = BooleanField('Rain attenuation')
    modp = BooleanField('Modulation / Distance')
    availp = BooleanField('Availability / Distance')
    def validate(self):
        return True
class GlobalForm(Form):
    lp = FormField(LinkForm,label="Link Profil")
    ep = FormField(EquipForm, label="Equipment Profil")
    mf = FormField(MetricForm, label="Graphs")
    submit_button = SubmitField('Submit Form')

if __name__ == '__main__':
    app = Flask(__name__)


    path = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')
    app.config['SIJAX_STATIC_PATH'] = path
    app.config['SIJAX_JSON_URI'] = '/static/js/sijax/json2.js'
    flask_sijax.Sijax(app)
    Bootstrap(app)
    GoogleMaps(app)

    app.config['SECRET_KEY'] = 'devkey'


    @flask_sijax.route(app,'/')
    def index():
        mods_list = list()
        #form = GlobalForm()
        form = GlobalForm()
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
            global graphs
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
                rr = itur.models.itu837.rainfall_rate(latitude,longitude,0.01)
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
            html = ''

            #<--- Constants --->
            pi = float(scipy.constants.pi)
            wl = float(scipy.constants.speed_of_light / (freq * (10 ** 9)))

            def getTx(mod):
                user = tinydb.Query()
                if xpic == '1':
                    db = tinydb.TinyDB('db_huawei_XPIC.json')
                else:
                    db = tinydb.TinyDB('db_huawei.json')
                table = db.table(equip)
                row = table.search((user.MODEL.search('(' + card + ')')) & (user.BAND_DESIGNATOR == float(freq)) & (
                        user.BANDWIDTH == float(bw)) & (user.MODULATION_TYPE == str(mod)))
                return row[0]['MAX_TX_POWER']

            def getCapa(mod):
                user = tinydb.Query()
                if xpic == '1':
                    db = tinydb.TinyDB('db_huawei_XPIC.json')
                else:
                    db = tinydb.TinyDB('db_huawei.json')
                table = db.table(equip)
                row = table.search((user.MODEL.search('(' + card + ')')) & (user.BAND_DESIGNATOR == float(freq)) & (
                        user.BANDWIDTH == float(bw)) & (user.MODULATION_TYPE == str(mod)))
                return row[0]['CAPACITY']

            def getRxThr(mod=''):
                user = tinydb.Query()
                if xpic == '1':
                    db = tinydb.TinyDB('db_huawei_XPIC.json')
                else:
                    db = tinydb.TinyDB('db_huawei.json')
                # manu='Ericsson',boolAM,equip,fre,modem,bw,mod
                # cb1 = equip , fe = freq, carde = card_modem, cpe = bandwidth , ref_mode = modulation

                if mod == '':
                    mod = ref_mod
                table = db.table(equip)
                row = table.search((user.MODEL.search('(' + card + ')')) & (user.BAND_DESIGNATOR == float(freq)) & (
                            user.BANDWIDTH == float(bw)) & (user.MODULATION_TYPE == str(mod)))
                if (am == '1'):
                    return row[0]['TYP_RX_THRESHOLD3'] + row[0]['ACM_DROP_OFFSET']
                else:
                    return row[0]['TYP_RX_THRESHOLD3']
            modulation_level = dict()
            def getThrList():

                user = tinydb.Query()
                if xpic == '1':
                    db = tinydb.TinyDB('db_huawei_XPIC.json')
                else:
                    db = tinydb.TinyDB('db_huawei.json')

                modulations = bandwCh(None,xpic,equip,freq,card,bw)
                table = db.table(equip)
                for mod in modulations:
                    modulation_level[mod] = getRxThr(mod)
            html = ''
            d = np.arange(0.01, 20, 0.01)
            if(form.mf.rainp.data):

                graphs[0] = plt.figure(title='Rain-caused exceeded attenuation according to the distance',x_axis_label = 'Distance (km)',y_axis_label = 'Attenuation (dB)')
                graphs[0].line(d, itur.models.itu530.rain_attenuation(0, 0, d, freq, el, 0.01, tau, rr), line_width=2)
                graphs[0].add_tools(HoverTool())
                html = html + file_html(graphs[0], CDN, "my plot")

            if(form.mf.modp.data):
                p=plt.figure(title='Capacity according to the distance',x_axis_label = 'Distance (km)',y_axis_label = 'Capacity (Mbps)')
                getThrList()
                # print(str(pi)+' -- '+str(tx1)+' -- '+str(g1a)+' -- '+str(g1b)+' -- '+str(20*np.log10((4*pi*9.94*1000)/wl)))
                rain_att = list()
                rain_att =  (g1a + g1b - 20 * np.log10(
                    (4 * pi * d * 1000) / wl) - itur.models.itu530.rain_attenuation(geoloc[0], geoloc[1], d, freq, el, p0,
                                                                                    tau, rr).value)
                mod_d = list()
                levels = list(modulation_level.values())
                mods_lab = list(modulation_level.keys())
                tx_mod = dict()
                capa_mod = dict()
                for lab in mods_lab:
                    tx_mod[lab]=getTx(lab)
                    capa_mod[lab]=getCapa(lab)
                capaline = list()

                for val in rain_att:
                    max_mod = -100
                    match = False
                    for lab,mod in modulation_level.items():
                        if val+tx_mod[lab]> mod:
                            max_mod = mod
                            capa = capa_mod[lab]
                            match=True
                    capaline.append(float(capa)) if match else capaline.append(0)
                p.line(d, capaline)
                p.add_tools(HoverTool())
                html = html+file_html(p, CDN, "my plot")
                # plt.hlines(-100,0,20,label='Rx Sensitivity',linestyles='dotted',colors=cmap(random.randint(1,20)))
                # plt.plot(tx2+g2a+g2b-itur.models.itu530.rain_attenuation(geoloc[0],geoloc[1], d, f2, el, 0.01,tau,rr).value-20*np.log((4*pi*d)/wl),label=str(f2)+'GHz')
            if(form.mf.availp.data):
                rx_thr = getRxThr(ref_mod)
                tx1 = getTx(ref_mod)
                res = list()
                p=plt.figure(title='Availability according to the distance',x_axis_label = 'Distance (km)',y_axis_label = 'Availability')
                for dcrt in d:
                    att_max = tx1 + g1a + g1b - float(rx_thr) - 20 * np.log10((4 * pi * dcrt * 1000) / wl)
                    val = float()

                    val = np.nan_to_num(itur.models.itu530.inverse_rain_attenuation(geoloc[0], geoloc[1], dcrt, freq, el, att_max, tau,rr).value)
                    val = 100 - round(val, 5)
                    res.append(val)
                # z = np.polyfit(d,res,10)
                # f = np.poly1d(z)
                # print(f(d))
                p.line(d, res)
                html = html + file_html(p, CDN, "my plot")
            f= open("templates/graphs.html","w")
            f.write(html)
            return render_template('graphs.html', graph=html)

        return render_template('index.html', form=form)



    @flask_sijax.route(app,'/scenario')
    def coucou():
        form = GlobalScenarioForm()
        if form.is_submitted():
            link = form.lp
            URL = "https://nominatim.openstreetmap.org/search"
            location = str(link.xe.data)
            #key = 'AIzaSyA3nLe6yUCTTMB82u1LTuWoyGJGvr8gBZg'
            location_detail = {'q': location,'format':'json'}
            r = requests.get(url=URL, params=location_detail)
            data = r.json()
            latitude = float(data[0]['lat'])
            longitude = float(data[0]['lon'])
            poubelle.DIA1 = float(link.gae.data)
            poubelle.DIA2 = float(link.gbe.data)
            poubelle.ELEVATION = float(link.ele.data)

            poubelle.GEOLOCATE = (latitude,longitude)

            poubelle.MARG = float(form.sp.margin.data)
            poubelle.POLAR = 0 if link.polar.data=='h' else 90 # float(form.polar.data)
            if link.rre.data != None:
                poubelle.RR = float(link.rre.data)
            poubelle.AVAILABILITY  = float(link.p_entry.data)
            poubelle.CIR = float(form.sp.capa.data)
            [eb_stab,ex_tab,e_mw_tab,mw_stab,mw_xtab] = poubelle.getScenarii()
            return render_template('tables.html',table=eb_stab,ex_tab=ex_tab,e_mw_tab=e_mw_tab,mw_stab=mw_stab,mw_xtab=mw_xtab)

        return render_template('index.html',form=form)

    app.run(host='0.0.0.0',port=80,debug=True)