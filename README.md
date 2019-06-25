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

## Graphs

#### Capacity according to the distance 
  >Specifying the link profil (Antenna diameters, tilt, geolocation/rainrate (0.01%/year), expected availability) and the equipment, returns a graph showing the expected link capacity according to the distance
