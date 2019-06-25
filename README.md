# link_budget

Flask Application (Python) using ITU-R P530 Recommandations in order to provide graphs and tables as microwave links planning tools.

Based on Huawei RTN and Ericsson MINI-LINK data files.

Graphs :

- Capacity according to the distance :
  Specifying the link profil (Antenna diameters, tilt, geolocation/rainrate (0.01%/year), expected availability) and the equipment, returns a graph showing the expected link capacity according to the distance
