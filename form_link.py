from flask import Flask, render_template, flash,redirect,request,g
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
from flask_wtf import Form, RecaptchaField
from wtforms import SelectField
import flask_sijax

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
    cb0 = SelectField('XPIC', choices=[('1', 'Yes'), ('0', 'No')])
    cb1 = SelectField('Equipment',choices=[('pouet', 'Yes')])
    submit_button = SubmitField('Submit Form')
class GlobalForm(Form):
    link = FormField(LinkForm)
    equip = FormField(EquipForm)
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
        #form = GlobalForm()
        form = EquipForm()
        def cb0Ch(obj_response,xpic):
            obj_response.alert("coucou")
            # print("coucou")
            # if xpic == 1:
            #     db = tinydb.TinyDB('db_huawei_XPIC.json')
            #
            # else:
            #     db = tinydb.TinyDB('db_huawei.json')
            # i=0
            # choix = list()
            # for val in db.tables():
            #     choix.append((str(i),str(val)))
            #     i=i+1
            # form.cb1.choices = choix

        if g.sijax.is_sijax_request:
            g.sijax.register_callback('coucou',cb0Ch)
            print('hello')
            return g.sijax.process_request()

        #     tx1=float(form.txee.data)
        #     g1a = float(form.gae.data)
        #     g1b = float(form.gbe.data)
        #     d = np.arange(0.001, 20, 0.001)
        #     f = float(form.fe.data)
        #     el = float(form.ele.data)
        #     tau = 45#float(form.polar.data)
        #     rr= float(form.rre.data)
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

    app.run(host='0.0.0.0',debug=True)