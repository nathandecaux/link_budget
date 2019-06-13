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
from geolocation.main import GoogleMaps


print('connard'+str(itur.models.itu530.XPD_outage_precipitation(47,2,23,2,28.67,18)))