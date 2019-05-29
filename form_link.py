from flask import Flask, render_template, flash,redirect,request
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
from flask_wtf import Form, RecaptchaField
from wtforms import SelectField
from flask_wtf.file import FileField
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
    BooleanField, SubmitField, IntegerField, FormField, validators,StringField,DecimalField
from wtforms.validators import Required
import bokeh.plotting as plt
from bokeh.models import Plot,Tool
from bokeh.resources import CDN
from bokeh.embed import file_html
import scipy.constants
import itur
import numpy as np



class HuaForm(Form):
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
    submit_button = SubmitField('Submit Form')


if __name__ == '__main__':
    app = Flask(__name__)
    AppConfig(app, '')  # Flask-Appconfig is not necessary, but
    # highly recommend =)
    # https://github.com/mbr/flask-appconfig
    Bootstrap(app)
    app.config['SECRET_KEY'] = 'devkey'


    @app.route('/', methods=['GET', 'POST'])
    def index():
        form = HuaForm()
        if form.validate_on_submit() :

            tx1=float(form.txee.data)
            g1a = float(form.gae.data)
            g1b = float(form.gbe.data)
            d = np.arange(0.001, 20, 0.001)
            f = float(form.fe.data)
            el = float(form.ele.data)
            tau = 45#float(form.polar.data)
            rr= float(form.rre.data)
            p = plt.figure(title='Rain-caused exceeded attenuation according to the distance',x_axis_label = 'Distance (km)',y_axis_label = 'Attenuation (dB)')
            p.line(d, itur.models.itu530.rain_attenuation(0, 0, d, f, el, 0.01, tau, rr), line_width=2)
            plot = Plot()
            plot.add_tools()
            html = file_html(p, CDN, "my plot")
            # plt.plot(itur.models.itu530.rain_attenuation(geoloc[0],geoloc[1], d, f2, el, 0.01,tau,rr),label='66GHz')
            # plt.xlabel('Distance (km)')
            # plt.ylabel('Attenuation (dB)')
            # plt.legend()
            #plt.title()
            return html
        return render_template('index.html', form=form)


    @app.route('/coucou')
    def coucou():
        return 'Coucou'

    app.run(host='0.0.0.0',debug=True)