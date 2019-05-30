from flask import Flask, render_template, flash,redirect,request,g
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
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

STATICFILES_DIRS = (
    os.path.join(os.path.dirname(__file__),'static'),
)


class LinkForm(Form):
    txee = DecimalField('Tx Level (dBm)')
    gae = DecimalField('Antenna Gain A (dBi)')
    gbe = DecimalField('Antenna Gain B (dBi)')
    xe = DecimalField('Rx Antenna Coordinates ({x,y})')
    ye = DecimalField()
    fe = DecimalField('Frequency (GHz)')
    ele = DecimalField('Rx Antenna Elevation (degrees)')
    polar = SelectField('Polar',choices=[('h', 'Horizontal'), ('v', 'Vertical')])
    rre = DecimalField('Rainrate (mm/h)')
    p_entry = DecimalField('Antenna Gain B (dBi)')

class EquipForm(Form):
    cb0 = SelectField('XPIC', choices=[('3','----'),('1', 'Yes'), ('0', 'No')],)
    cb1 = SelectField('Equipment',choices=[('0', '----')],validators=())
    fe = SelectField('Frequency (GHz)',choices=[('0', '----')])
    carde = SelectField('Modem Card + ODU',choices=[('0', '----')])
    cpe = SelectField('Bandwidth (MHz)',choices=[('0', '----')])
    ref_mod = SelectField('Reference Modulation', choices=[('0', '----')])
    am = SelectField('Adaptative Modulation', choices=[('3','----'),('1', 'Yes'), ('0', 'No')])

class MetricForm(Form):
    rainp = BooleanField('Rain attenuation')
    modp = BooleanField('Modulation / Distance')
    availp = BooleanField('Availability / Distance')

class GlobalForm(Form):
    lp = FormField(LinkForm,label="Link Profil")
    ep = FormField(EquipForm, label="Equipment Profil")
    mf = FormField(MetricForm, label="Graphs")
    fe = SelectField('Frequency (GHz)', choices=[('0', '----')])
    submit_button = SubmitField('Submit Form')

if __name__ == '__main__':
    app = Flask(__name__)
    path = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')
    app.config['SIJAX_STATIC_PATH'] = path
    app.config['SIJAX_JSON_URI'] = '/static/js/sijax/json2.js'
    flask_sijax.Sijax(app)
    Bootstrap(app)

    app.config['SECRET_KEY'] = 'devkey'


    @flask_sijax.route(app,'/')
    def index():
        choices = dict()
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
                obj_response.html_append('#ep-cb1', '<option id='+str(i)+' value='+val+' >'+val+'</option>')
                choix.append((str(val),str(val)))
                i=i+1
            choices['cb1']=choix



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
            form.ep.fe.choices = choix




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
            form.ep.carde.choices = choix




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
                    choix.append((str(modulation), str(modulation)))
            modulations.sort(key=sortMod)

            for modulation in modulations:
                i=i+1
                obj_response.html_append('#ep-ref_mod', '<option id=' + str(
                    i) + ' value=' + modulation + ' >' + modulation + '</option>')

            form.ep.ref_mod.choices = choix

        if form.validate_on_submit():
            link = form.lp
            ep = form.lp
            tx1 = float(form.lp.txee.data)
            g1a = float(link.gae.data)
            g1b = float(link.gbe.data)
            d = np.arange(0.001, 20, 0.001)
            f = float(link.fe.data)
            el = float(link.ele.data)
            geoloc = (0, 0)
            tau = 45  # float(form.polar.data)
            rr = float(link.rre.data)
            p0 = float(link.p_entry.data)
            xpic = ep.cb0.data
            equip = ep.cb1.data
            freq = ep.fe.data
            card = ep.carde.data
            bw = ep.cpe.data
            mod = ep.ref_mode.data
            am = ep.am.data
            print(form.mf.modp.data)

        if g.sijax.is_sijax_request:
            g.sijax.register_callback('cb0',cb0Ch)
            g.sijax.register_callback('cb1',equiCh)
            g.sijax.register_callback('fe', freqCh)
            g.sijax.register_callback('carde', cardCh)
            g.sijax.register_callback('cpe', bandwCh)
            #g.sijax.register_callback('click',submitted)
            return g.sijax.process_request()



        #     p = plt.figure(title='Rain-caused exceeded attenuation according to the distance',x_axis_label = 'Distance (km)',y_axis_label = 'Attenuation (dB)')
        #     p.line(d, itur.models.itu530.rain_attenuation(0, 0, d, f, el, 0.01, tau, rr), line_width=2)
        #     p.add_tools(HoverTool())
        #     html = file_html(p, CDN, "my plot")
        #     # plt.plot(itur.models.itu530.rain_attenuation(geoloc[0],geoloc[1], d, f2, el, 0.01,tau,rr),label='66GHz')
        #     # plt.xlabel('Distance (km)')
        #     # plt.ylabel('Attenuation (dB)')
        #     # plt.legend()
        #     #plt.title()

            #return html

        return render_template('index.html', form=form)


    @app.route('/coucou')
    def coucou():
        return 'Coucou'

    app.run(host='0.0.0.0',port=80,debug=True)