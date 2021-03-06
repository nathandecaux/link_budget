# Link Budget

Flask Application (Python) using ITU-R P530 Recommandations in order to provide graphs and tables as microwave links planning tools.

Based on Huawei RTN and Ericsson MINI-LINK data files.

## Forms
To get access to the different features, different forms need to be filled in :
#### Link Profil
The link parameters are used in order to calculate the free space loss + the attenuation caused by the rain

- Antenna Diameter A & B : Selection field to set the antenna diameter of both site. 
- Rx Antenna Elevation : Text field waiting for a float value to set the tilt angle. This value will influence the air index gradient and then provide the actual link distance
- Polar : Selection field to set the antenna polarization
- Availability : Text field waiting for a float value to set the expected availability in % / year for the Capacity / Distance graph
- Site Location : Text field waiting for an address (complete or not). A  geocode of this address is get by requesting the [OpenStreetMap API](https://nominatim.openstreetmap.org). Then, a approximate rainrate (mm/h for 0.01% of a year) is processed using those coordinates and the ITU-R P 837 recommandations
- Rainrate : In case of offline using / unavailability of the OpenStreetMap API, the rainrate can be directly specified in this field

#### Equipment Profil
The equipment should be specified in order to get received level thresholds that will be useful to process graphs.

This is a dynamic form : it consists in selection field whose choices are dynamically set according to previous selected values. Choices are then updated using the equipment database.

- XPIC : Not implemented yet, but need a 'Yes' or 'No' choice anyway
- Equipment : Equipment series name
- Frequency : Band designator
- Modem Card (+ODU for Huawei) : Workin RF modem card name. 
> *Note : In the case of Huawei full outdoors equipment, the only possible choice is the equipment name itself*
- Bandwidth : Working channel spacing
- Reference modulation : The working modulation that will be use for the Availability / Distance graph, in order to fix the Rx Level threshold
- Adaptative Modulation : Specify if the AM feature is activated or not
> *Note : In the Ericsson form, this field replace the XPIC one*

### Scenario Profil
A scenario form must be filled in the 'Scenario' feature, in order to set those expected parameters :

- Capacity : Corresponding to the expected CIR (Commited Information Rate)
- Margin : Let the possibility to set an absolute margin for the CIR and the PIR
- PIR (optionnal) :  Permit setting a second target capacity
- Availability PIR : Must be set if the PIR field is filled 
- Distance

> *Note : The CIR availability must be set in the 'Availability' field from the Link Profil subform*

## Graphs

1. Capacity / Distance 

Returns a graph showing the expected link capacity according to the distance. 

>*The link capacity is calculated according to the highest modulation that can be use, relativly to it Rx threshold and the current Rx level.*

The Rx level / link budget is obtained calculating the following sum 
>*Free space loss + The attenuation caused by the rain (according to the specified availability and using the equation 33 from the ITU-R P 530 recommandations) + Antenna gain (according to their diameters) + the maximum Tx Power (depending on the equipment specified)*


2. Availability / Distance

Returns a graph showing the evolution of the expected availability according to the distance, and for a specific working modulation.

As the modulation is fixed, a target Rx threshold is set, that can be assume as maximum acceptable attenuation. Then, by manipulating the ITU-R P 530 Eq. 33, the script get the availability that fit to this specific attenuation.

3. Capacity / Availability

Returns a graph showing the maximum expected capacity according the availability, and for a specific distance.

> Example : **{x = 99.993 % ; y = 1093 Mbps}** ==> *It means that the link can work for 99.993 % of the time using a 1093 Mbps throughput*

> *Note : By clicking on the associated CheckBox in the 'Graphs' form, an additionnal text field will appear in order to set the Distance value*  

For each graph that is displayed, there's a small form aside that permit updating the initial plot line ( = Refresh button) or adding a new line ( = Add line button). 

Graphs are powered by the Bokeh Library. Uses of the graph toolbar (such as Zoom by selection, etc.) are described in the [Bokeh User Guide](https://bokeh.pydata.org/en/latest/docs/user_guide/tools.html#built-in-tools)

## Scenario

The scenario feature is a tool that will suggest a list of possibilies according to the link and some target capacities (CIR and optionnaly PIR) and related availabilities. After sending the form, the application will show several tables :

1. E-Band (1+0)
2. E-Band (XPIC 2+0) : Using XPIC (but not implemented yet, it basically just multiply by two the capacity)
3. E-Band + MW (2+0) : Suggestions of dual carrier links using a combination of an E-band link and a 18 or 23 GHz link
4. MW (1+0)
5. MW (XPIC 2+0)

For single and cross-polar links, tables are designed as follows :

> Model (Equipment+Frequency+Bandwidth+Modulation) | Total Capacity | Availability

For E-band + MW links, tables are designed as follows :

> E-Band Model | Microwave Model | E-Band Capacity | MW Capacity | Total Capacity | Availability (returns the smallest one)

Note that in case of Ericsson equipment, an additionnal 'Modulation' column was necessary.
If a PIR has been set up, each row from each table can be clicked to show an additionnal row. This additionnal shows the PIR configuration, using the same format as rows corresponding to the CIR configuration.

> *To get to the PIR configuration, the algorithm will increase the modulation and until the PIR is reached, if possible. In the RTN 380AX product, the bandwidth could also been increased following some specific upshift rules*


## Dependancies

- Flask : v1.0.3
- Flask-Bootstrap : v3.3.7.1
- Flask-Sijax : v0.4.1
- Flask-WTF : v0.14.2
- Astropy : v3.1.2
- Bokeh : v1.2.0
- Itur : Custom version
- Numpy : v1.16.3
- Scipy : v1.3.0
- TinyDB : v3.13.0
- Tornado : v6.0.2

The main web application is running with Flask, on a fixed TCP port. Graphs are running using a Bokeh Server, that is using a random TCP client port for each session (as this tool is supposed to be used by a limited number of users)

## Database

Adding new equipment is not that easy because Ericsson and Huawei has provided non-generic (not totally at least) excel files, and scripts are dealing with text to retrieve some informations. 

Then, new equipment can be added using wisely the 'database.py' script, following thoses rules :
- For ericsson :

MODEL column should be like this : {CARD}/{Bandwidth value}/{SUBCARD} (the subcard value is not important)

- For Huawei : (ONLY USE db_huawei.json)
  - If the equipment is RTN900 : The syntax is {FREQUENCY}G{BANDWIDTH}M{MODULATION}QAM_{CARD} =>  Example : 13G7M32QAM_ISM6XMC5D
  - Else, the syntax is : {CARD}\_{FREQUENCY}G_{BANDWIDTH}M_{MODULATION}QAM => Example : RTN380AX_80G_62.5M_128QAM



