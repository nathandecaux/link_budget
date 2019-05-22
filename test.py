
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import itur
import numpy as np
from tkinter import filedialog
from tkinter import *
from tkinter import ttk
import pickle
from matplotlib import pyplot as plt
from matplotlib import colors
import scipy.constants
from itur.models.itu453 import DN65
from itur.models.itu837 import rainfall_rate
import mpldatacursor
import random
import tinydb
import re
itur.models.itu837.change_version(6)

User = tinydb.Query()

window = Tk()
window.title("Link Budget Ericsson")
window.geometry()
equiFr = LabelFrame(window,text = 'Equipment Profil')
Frame(relief='flat', borderwidth=4)
modulation_level = dict()

profils = list()
activated_plots = dict()
activated_plots[1] = False
activated_plots[2] = False
activated_plots[3] = False
plots_set = list()
linkPr = LabelFrame(window,text='Link Profil')
linkPr.grid(column=1,row=0)
lbl = Label(linkPr, text="Tx Level (dBm)")
lbl.grid(column=0, row=1)
txee = Entry(linkPr)
txee.grid(column=1, row=1)
txee.config(width=10)
lbl = Label(linkPr, text="Antenna Gain A (dBi)")
lbl.grid(column=0, row=2,  )
gae = Entry(linkPr)
gae.grid(column=1, row=2)
gae.config(width=10)
lbl = Label(linkPr, text='-and-')
lbl.grid(column=3,row=2)
lbl = Label(linkPr, text="  Antenna Gain B (dBi)")
lbl.grid(column=4, row=2)
gbe = Entry(linkPr)
gbe.grid(column=5, row=2,padx=15)
gbe.config(width=10)

def coordEvent(event):
    rre.delete(0, 'end')
    rre.config(state='disabled')
    bool1 = (str(xe.get()).__len__() < 2 and str(ye.get()== ''))
    bool2 = (str(ye.get()).__len__() < 2 and str(xe.get()== ''))
    bool3 = bool1 or bool2
    if bool3 and event.keycode == 8:
        rre.config(state='normal')


lbl = Label(linkPr, text="Rx Antenna Coordinates ({x,y}) ")
lbl.grid(column=0, row=5,padx=20)
xe = Entry(linkPr)
xe.grid(column=1, row=5)
xe.config(width=10)
ye = Entry(linkPr)
ye.grid(column=2, row=5)
ye.config(width=10)
xe.bind('<Key>',coordEvent)
ye.bind('<Key>',coordEvent)


lbl = Label(linkPr, text="Rx Antenna Elevation (degrees)")
lbl.grid(column=0, row=4)
ele = Entry(linkPr)
ele.grid(column=1, row=4)
ele.config(width=10)

lbl = Label(linkPr, text="Rx Antenna Polar (degrees) ")
lbl.grid(column=0, row=6)
polar = ttk.Combobox(linkPr,values=['Horizontal','Vertical'])
polar.grid(column=1, row=6)
polar.config(width=10)

def rrEvent(event):
    xe.delete(0, 'end')
    ye.delete(0, 'end')
    xe.config(state='disabled')
    ye.config(state='disabled')
    if (str(rre.get()).__len__() < 2 and event.keycode == 8):
        xe.config(state='normal')
        ye.config(state='normal')


lbl = Label(linkPr, text='-or-')
lbl.grid(column=3,row=5)
lbl = Label(linkPr, text="Rainrate (mm/h) ")
lbl.grid(column=4, row=5)
rre = Entry(linkPr)
rre.grid(column=5, row=5)
rre.bind('<Key>',rrEvent)
rre.config(width=10)
def thrEvent(Event):
    cb0.delete(0, 'end')
    cb0.config(state='disabled')
    cb1.delete(0, 'end')
    cb1.config(state='disabled')
    cpe.delete(0, 'end')
    cpe.config(state='disabled')
    ref_mode.delete(0, 'end')
    ref_mode.config(state='disabled')
    carde.delete(0, 'end')
    carde.config(state='disabled')
    fe.delete(0, 'end')
    fe.config(values=[6,7,8,10,11,13,15,18,23,26,28,32,38,42,80])

    if (str(thr.get()).__len__() < 2 and Event.keycode == 8):
       cb0.config(state='normal')
       cb1.config(state='normal')
       cpe.config(state='normal')
       ref_mode.config(state='normal')
       carde.config(state='normal')
       fe.config(values=[''])


lbl = Label(equiFr, text='-or-')
lbl.grid(column=0,row=20)
lbl = Label(equiFr, text="Rx threshold (dBm)\n(Can't be use with Modulation / Distance graph) ")
lbl.grid(column=0, row=21)
thr = Entry(equiFr)
thr.grid(column=1, row=21)
thr.bind('<Key>',thrEvent)
thr.config(width=10)


lbl = Label(linkPr, text="Percentage of attenuation exceeding (%) ")
lbl.grid(column=0, row=9)
p_entry = Entry(linkPr)
p_entry.grid(column=1, row=9)
p_entry.config(width=10)

#Label(window,text='----------------------------------------').grid(column=1, row=10)

equiFr.grid(column=1, row=11)
def AMstate(event):
    thr.delete(0, 'end')
    cb1.delete(0,'end')
    fe.delete(0, 'end')
    carde.delete(0, 'end')
    cpe.delete(0, 'end')
    ref_mode.delete(0, 'end')
    if cb0.get()== 'Yes':
        db = tinydb.TinyDB('db_ericsson_AM.json')
    else:
        db = tinydb.TinyDB('db_ericsson.json')
    cb1.config(value = list(db.tables()))
#for tab in db.tables():
lbl = Label(equiFr, text='Adaptative Modulation')
lbl.grid(column=0, row=11)
cb0 = ttk.Combobox(equiFr,values = ['Yes','No'])
cb0.grid(column=1, row=11)
cb0.bind("<<ComboboxSelected>>",AMstate)

lbl = Label(equiFr, text="Equipment")
lbl.grid(column=0, row=12)
def equipEvent(event):
     if cb0.get() == 'Yes':
        db = tinydb.TinyDB('db_ericsson_AM.json')
     else:
        db = tinydb.TinyDB('db_ericsson.json')
     fe.delete(0, 'end')
     carde.delete(0, 'end')
     cpe.delete(0, 'end')
     ref_mode.delete(0, 'end')

     table = db.table(str(cb1.get()))
     freqs = list()
     for row in table:
        freq = row['BAND_DESIGNATOR']
        if freq not in freqs:
            freqs.append(freq)
     freqs.sort()
     fe.config(values=freqs)

cb1 = ttk.Combobox(equiFr)
cb1.grid(column=1, row=12)
cb1.bind("<<ComboboxSelected>>", equipEvent)


def freqEvent(event):
    if cb0.get() == 'Yes':
        db = tinydb.TinyDB('db_ericsson_AM.json')
    else:
        db = tinydb.TinyDB('db_ericsson.json')
    carde.delete(0, 'end')
    cpe.delete(0, 'end')
    ref_mode.delete(0, 'end')
    table = db.table(str(cb1.get()))
    mod_cards = list()
    for row in table:
        freq = row['BAND_DESIGNATOR']
        if str(row['MODEL']).split('/').__len__()>3:
            mod_card = str(row['MODEL']).split('/')[1]
        else:
            mod_card = str(int(freq))+'ASA'
        if str(freq) == str(fe.get()) and mod_card not in mod_cards:
            mod_cards.append(mod_card)
    print(mod_cards)
    carde.config(values=mod_cards)


#for tab in db.tables():
lbl = Label(equiFr, text="Tx Frequency (GHz)")
lbl.grid(column=0, row=13)
fe = ttk.Combobox(equiFr)
fe.grid(column=1, row=13,padx=20)
fe.bind("<<ComboboxSelected>>", freqEvent)

def cardEvent(event):
    if cb0.get() == 'Yes':
        db = tinydb.TinyDB('db_ericsson_AM.json')
    else:
        db = tinydb.TinyDB('db_ericsson.json')
    cpe.delete(0, 'end')
    ref_mode.delete(0, 'end')
    table = db.table(str(cb1.get()))
    bandwidths = list()
    match_str = str(carde.get())
    for row in table:
        freq = str(row['BAND_DESIGNATOR'])
        bandwidth = str(row['BANDWIDTH'])
        if (re.search('.('+match_str+'/).',str(row['MODEL']))!= None) and str(freq) == str(fe.get()) and bandwidth not in bandwidths:
            bandwidths.append(bandwidth)
    cpe.config(value =bandwidths)


lbl = Label(equiFr, text="Modem Card")
lbl.grid(column=0, row=14)
carde = ttk.Combobox(equiFr)
carde.grid(column=1, row=14)
carde.bind("<<ComboboxSelected>>",cardEvent)

def bwEvent(event):
    if cb0.get() == 'Yes':
        db = tinydb.TinyDB('db_ericsson_AM.json')
    else:
        db = tinydb.TinyDB('db_ericsson.json')
    ref_mode.delete(0, 'end')
    table = db.table(str(cb1.get()))
    modulations = list()
    match_str = str(carde.get())
    for row in table:
        modulation = row['MODULATION_TYPE']
        freq = str(row['BAND_DESIGNATOR'])
        bandwidth = str(row['BANDWIDTH'])
        if (re.search('.('+match_str+'/).',str(row['MODEL']))!= None) and str(freq) == str(fe.get()) and str(bandwidth) == str(cpe.get()) and modulation not in modulations:
            modulations.append(modulation)
    def sortMod(mod):
        if(re.match('BPSK',str(mod))):
            mod='2QAM'
        return int(str(mod).split('QAM')[0])
    modulations.sort(key=sortMod)
    ref_mode.config(value =modulations)
    return modulations

lbl = Label(equiFr, text="Bandwidth (MHz)")
lbl.grid(column=0, row=15)
cpe = ttk.Combobox(equiFr)
cpe.grid(column=1, row=15)
cpe.bind("<<ComboboxSelected>>",bwEvent)

lbl = Label(equiFr, text="Reference Modulation")
lbl.grid(column=0, row=16)
ref_mode = ttk.Combobox(equiFr)
ref_mode.grid(column=1, row=16)

fr_plots = LabelFrame(window,text='Graphics')
fr_plots.grid(column=1, row=18)
var1 = IntVar()

c = Checkbutton(fr_plots, text="Rain-caused attenuation / Distance", variable=var1, justify='center')
c.grid(column=1, row=18)
var2 = IntVar()

c = Checkbutton(fr_plots, text="Modulation / Distance", variable=var2, justify='center')
c.grid(column=1, row=19)


var3 = IntVar()

c = Checkbutton(fr_plots, text="Availability / Distance", variable=var3, justify='center')
c.grid(column=1, row=20)




def getRxThr(mod = ''):
    user = tinydb.Query()
    if cb0.get() == 'Yes':
        db = tinydb.TinyDB('db_ericsson_AM.json')
    else:
        db = tinydb.TinyDB('db_ericsson.json')
    #manu='Ericsson',boolAM,equip,fre,modem,bw,mod
    #cb1 = equip , fe = freq, carde = card_modem, cpe = bandwidth , ref_mode = modulation
    equip = str(cb1.get())
    freq = fe.get()
    card = str(carde.get())
    bw = cpe.get()
    if mod == '':
        mod = ref_mode.get()
    table = db.table(equip)
    row = table.search((user.MODEL.search('.('+card+'/).')) & (user.BAND_DESIGNATOR == float(freq))&(user.BANDWIDTH == float(bw))&(user.MODULATION_TYPE == str(mod)))
    return row[0]['TYP_RX_THRESHOLD3']

def getThrList():
    user = tinydb.Query()
    if cb0.get() == 'Yes':
        db = tinydb.TinyDB('db_ericsson_AM.json')
    else:
        db = tinydb.TinyDB('db_ericsson.json')

    equip = str(cb1.get())
    freq = fe.get()
    card = str(carde.get())
    bw = cpe.get()
    modulations = bwEvent(Event)
    table = db.table(equip)
    for mod in modulations:
        modulation_level[mod] = getRxThr(mod)

def save():
    conf = list()
    conf.append((txee.get()))
    conf.append((gae.get()))
    conf.append((gbe.get()))
    conf.append((fe.get()))
    conf.append((xe.get()))
    conf.append((ye.get()))
    conf.append((ele.get()))
    conf.append((polar.get()))
    conf.append((rre.get()))
    conf.append(thr.get())
    conf.append(p_entry.get())
    conf.append(cb0.get())
    conf.append(cb1.get())
    conf.append(carde.get())
    conf.append(cpe.get())
    conf.append(ref_mode.get())
    f=filedialog.asksaveasfilename(initialdir='/Users/Travail/Desktop/Docs/Link_Budget',title='Select File',filetypes = (("Link Configuration files","*.*"),("all files","*.*")))
    with open(f, 'wb') as fp:
        pickle.dump(conf, fp)

def load():
    f = filedialog.askopenfilename(initialdir='/Users/Travail/Desktop/Docs/Link_Budget',title='Select File',filetypes = (("Link Configuration files","*.*"),("all files","*.*")))
    with open(f, 'rb') as fp:
        itemlist = pickle.load(fp)
    txee.delete(0, 'end')
    txee.insert(0,itemlist[0])
    gae.delete(0, 'end')
    gae.insert(0,itemlist[1])
    gbe.delete(0, 'end')
    gbe.insert(0,itemlist[2])
    fe.delete(0, 'end')
    fe.insert(0,itemlist[3])
    xe.delete(0, 'end')
    xe.insert(0,itemlist[4])
    ye.delete(0, 'end')
    ye.insert(0,itemlist[5])
    ele.delete(0, 'end')
    ele.insert(0,itemlist[6])
    polar.delete(0, 'end')
    polar.insert(0,itemlist[7])
    rre.delete(0, 'end')
    rre.insert(0,itemlist[8])
    thr.delete(0, 'end')
    thr.insert(0,itemlist[9])
    p_entry.delete(0,'end')
    p_entry.insert(0,itemlist[10])
    cb0.delete(0, 'end')
    cb0.insert(0, itemlist[11])
    cb1.delete(0, 'end')
    cb1.insert(0,itemlist[12])
    carde.delete(0, 'end')
    carde.insert(0,itemlist[13])
    cpe.delete(0, 'end')
    cpe.insert(0,itemlist[14])
    ref_mode.delete(0, 'end')
    ref_mode.insert(0,itemlist[15])

def equipment_profil(name='default'):
    if(name=='default'):
        f = filedialog.askopenfilename(initialdir='/Users/Travail/Desktop/Docs/Link_Budget',title='Select File',filetypes = (("Link Configuration files","*.*"),("all files","*.*")))
        f = open(f, 'r')
    else:
        f = open("/Users/Travail/Desktop/Docs/Link_Budget/"+name+".csv","r")
    i=0
    j=0
    str_file = str(f.read())
    f.close()
    for line in str_file.split('\n'):
        print(i)
        split_line = line.split(';')
        if i==0:
            list_mod=line.split(';')
        else:
            if split_line[0]!='':
                for mods in list_mod:
                    if j>0:
                        modulation_level[(split_line[0],mods)] = split_line[j]
                    j=j+1
        i=i+1
        j=0
    print(modulation_level)


def clicked():
    def get_cmap(n, name='hsv'):
        '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
        RGB color; the keyword argument name must be a standard mpl colormap name.'''
        return plt.cm.get_cmap(name, n)

    current_profil = list()

    pi= scipy.constants.pi
    #Tx Level
    tx1=float(txee.get()) #dBm
    current_profil.append(tx1)

    #Antenna gains
    g1a=float(gae.get()) #dBi
    g1b=float(gbe.get()) #dBi
    current_profil.append(g1a)
    current_profil.append(g1b)

    #Distance
    d=np.arange(0.001,20,0.001) #km

    #Frequency
    f=float(fe.get()) #GHz
    current_profil.append(f)

    #Wavelengths
    wl = float(scipy.constants.speed_of_light / (f * (10 ** 9)))

    #Coordinates of the receiving antenna
    if(xe.get()==''):
        x=0
    else:
        x=xe.get()
    if(ye.get()==''):
        y=0
    else:
        y=ye.get()
    current_profil.append(xe)
    current_profil.append(ye)
    geoloc = (float(x), float(y))

    #Minimum Rx Level Threshold
    if thr.get()=='' or ref_mode.get() != '':
        rx_thr= float(getRxThr())
    else:
        rx_thr=thr.get()
    current_profil.append(rx_thr)

    #Elevation
    el=float(ele.get()) #degrees
    current_profil.append(el)

    #Polar
    if(polar.get()=='Horizontal'):
        tau=float(0)
        tau_str = "H"
    else:
        tau=float(90)
        tau_str = "V"
    current_profil.append(tau)
    #Rainrate
    if rre.get()!='':
        rr=float(rre.get()) #mm/h
        lbl_plot = str(f) + 'GHz - '+str(rr)+' mm/h'
    else:
        rr=rainfall_rate(geoloc[0], geoloc[1], 0.01).value
        lbl_plot = str(f) + 'GHz - '+str(round(rr,3))+' mm/h (estimated)'
    current_profil.append(rr)

    if p_entry.get()!='':
        p = float(p_entry.get())
    else:
        p=0.01
    current_profil.append(p)
    big_lgd1 = "Elevation : "+str(el)+"  |  Polar : "+tau_str+'\nProbability :'+str(p)+' %'
    big_lgd2 = "Tx Power : "+str(tx1)+"\nGain A : "+str(g1a)+"  |  Gain B : "+str(g1b)+"\nElevation : "+str(el)+"  |  Polar : "+tau_str+'\nProbability :'+str(p)+' %'
    big_lgd3 = "Tx Power : "+str(tx1)+"\nGain A : "+str(g1a)+"  |  Gain B : "+str(g1b)+"\nElevation : "+str(el)+"  |  Polar : "+tau_str+"\nRx Threshold : "+str(rx_thr)
    flag = True
    flag1 = True
    flag2 = True

    plots_set = [0, 0, 0]

    for sets in profils:
        if sets[0]==current_profil :
            flag1 = False
            if sets[1] == str(var1.get()) + str(var2.get()) + str(var3.get()):
               if ((var1.get()==1 and plt.fignum_exists(1)== False) or (var2.get()==1 and plt.fignum_exists(2)== False) or (var3.get()==1 and plt.fignum_exists(0)== False)):
                   flag2 = True
               else:
                flag2 = False
            plots_set = [max(plots_set[0],int(sets[1][0])), max(plots_set[1],int(sets[1][1])), max(plots_set[2],int(sets[1][2]))]


    flag = flag1 or flag2
    if flag and (var1.get()+var2.get()+var3.get())>0:
        activated_plots[1] = plt.fignum_exists(0)
        activated_plots[2] = plt.fignum_exists(1)
        activated_plots[3] = plt.fignum_exists(2)

        profils.append((current_profil,str(var1.get())+str(var2.get())+str(var3.get())))
        if var3.get()==1 and (plots_set[2]==0 or plt.fignum_exists(0)== False):
            plt.figure(0)
            # inverse_rain_attenuation (lat, lon, d, f, el, Ap, tau=45, R001=None)
            res = list()
            for dcrt in d:

                att_max = tx1 + g1a + g1b - float(rx_thr) - 20 * np.log10((4 * pi * dcrt*1000) / wl)
                val= float()

                val = itur.models.itu530.inverse_rain_attenuation(geoloc[0], geoloc[1], dcrt, f, el, att_max, tau, rr).value
                val = 100-round(val,5)
                res.append(val)
            # z = np.polyfit(d,res,10)
            # f = np.poly1d(z)
            # print(f(d))
            line = plt.plot(d, res, label=lbl_plot,drawstyle ='steps-pre')

            plt.legend()
            if not activated_plots[1]:
                plt.grid()
            plt.ylim(top=100)
            plt.ylim(bottom=99.5)
            plt.xlim(left=-0.01)
            plt.xlabel('Distance (km)')
            plt.ylabel('Availability (%)')
            plt.title('Percentage of availability for a year')
            plt.locator_params(axis='y', nbins=6)
            plt.locator_params(axis='x', nbins=10)

            big_lgd3 = big_lgd3 + '\nAvailability : {y:.2f} dB - Distance : {x:.2f} km'
            mpldatacursor.datacursor(line, formatter=big_lgd3.format, draggable=True)

        if var1.get()==1 and (plots_set[0]==0 or plt.fignum_exists(1)== False):
            plt.figure(1)
            line2 = plt.plot(d, itur.models.itu530.rain_attenuation(geoloc[0], geoloc[1], d, f, el, p, tau, rr), label=lbl_plot)
            # plt.plot(itur.models.itu530.rain_attenuation(geoloc[0],geoloc[1], d, f2, el, 0.01,tau,rr),label='66GHz')
            plt.xlabel('Distance (km)')
            plt.ylabel('Attenuation (dB)')
            plt.legend()
            plt.title('Rain-caused exceeded attenuation according to the distance')
            plt.xlim(left=-0.01)
            if not activated_plots[2]:
                plt.grid()

            big_lgd1 = big_lgd1 + '\nAttenuation : {y:.2f} dB - Distance : {x:.2f} km'
            mpldatacursor.datacursor(line2, formatter=big_lgd1.format, draggable=True)


        if var2.get()==1 and (plots_set[1]==0 or plt.fignum_exists(2)== False):
            plt.figure(2)
            getThrList()
            #print(str(pi)+' -- '+str(tx1)+' -- '+str(g1a)+' -- '+str(g1b)+' -- '+str(20*np.log10((4*pi*9.94*1000)/wl)))
            rain_att = list()
            rain_att=(tx1+g1a+g1b-20*np.log10((4*pi*d*1000)/wl)-itur.models.itu530.rain_attenuation(geoloc[0],geoloc[1], d, f, el, p,tau,rr).value)
            mod_d = list()
            levels = list(modulation_level.values())
            mods_lab = list(modulation_level.keys())

            for val in rain_att:
                max_mod=-100
                for mod in levels:
                    if val > mod:
                        max_mod = mod
                mod_d.append(max_mod)

            line15 = plt.plot(d,rain_att)
            line3 = plt.plot(d,mod_d,label=lbl_plot+' - '+str(p)+'% / Year')
            cmap = get_cmap(20)


            #plt.hlines(-100,0,20,label='Rx Sensitivity',linestyles='dotted',colors=cmap(random.randint(1,20)))
            # plt.plot(tx2+g2a+g2b-itur.models.itu530.rain_attenuation(geoloc[0],geoloc[1], d, f2, el, 0.01,tau,rr).value-20*np.log((4*pi*d)/wl),label=str(f2)+'GHz')
            plt.legend()
            plt.yticks(levels,mods_lab)
            plt.ylim(top=(levels[-1]+10))
            plt.ylim(bottom=(levels[0]-10))
            plt.xlim(left=-0.01)
            plt.xlim(right=d[-1])
            plt.xlabel('Distance (km)')
            plt.ylabel('Rx Level (dBm)')
            plt.title('Rx Level according to the distance')
            big_lgd2=big_lgd2+'\nRx Level : {y:.2f} dBm - Distance : {x:.2f} km'
            mpldatacursor.datacursor(line3,formatter=big_lgd2.format, draggable=True)
            if rx_thr != '':
                plt.hlines(rx_thr, 0, 20, label='Reference Modulation', linestyles='dotted',
                           colors=cmap(random.randint(1, 20)))
                plt.grid()
        plt.show()





menubar = Menu(window)
menubar.add_command(label="Save", command=save)
menubar.add_command(label="Open", command=load)
menubar.add_command(label="Load equipment profil", command=equipment_profil)

btn = Button(window, text="Draw",command=clicked,pady =12,padx=30)
btn.grid(column=1, row=24)
# btn2 = Button(window, text="Get Threshold",command=getThrList)
# btn2.grid(column=1, row=25)

window.config(menu=menubar)
window.mainloop()
