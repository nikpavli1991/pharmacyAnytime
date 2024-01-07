# -*- coding: utf-8 -*-
"""
Created on Fri Aug 14 14:01:51 2020

@author: Nikos Pavlidis
@department: Life sciences
"""

"""
This program implements the query "find the closest to me,open-pharmacy that sells the product that I desire".
First, a sorting is done based on the product chosen by the user and the pharmacies that are open. Then
calculate all the distances between the selected pharmacies and the position of the user. Next, we calculate
the minimun distance of the previous distances. Finally, print the closest pharmacy to the user along with
properties(name,address,etc.).
All these are presented to the user through a gui, which handles the operations requested.
"""


import requests
from neo4j import GraphDatabase
from bs4 import BeautifulSoup
from math import sin, cos, sqrt, atan2, radians

import tkinter as tk
import tkinter.ttk as ttk
from ttkthemes import ThemedStyle

from geopy.geocoders import Nominatim

def getNodeViaClass(tx,productClass):
    
    if productClass == "Ομοιοπαθητικά":
        returnedNodes = tx.run("MATCH (a:Pharmacy)--(:Ομοιοπαθητικά) RETURN(a)")
    elif productClass == "Αντηλιακά":
        returnedNodes = tx.run("MATCH (a:Pharmacy)--(:Αντηλιακά) RETURN(a)")
    elif productClass == "Καλλωπισμός":
        returnedNodes = tx.run("MATCH (a:Pharmacy)--(:Καλλωπισμός) RETURN(a)")
    elif productClass == "Βρεφικά":
        returnedNodes = tx.run("MATCH (a:Pharmacy)--(:Βρεφικά) RETURN(a)")
    elif productClass == "Στοματική_Υγιεινή":
        returnedNodes = tx.run("MATCH (a:Pharmacy)--(:Στοματική_Υγιεινή) RETURN(a)")
       
    results = [record for record in returnedNodes.data()]
    
    return(results)
   
def selectProduct():
    global productClass
    productClass = comboClasses.get()
    comboClasses.configure(state='disabled')
    
    if (str(comboClasses["state"]) == 'disabled') and (str(LocationEntry["state"]) == 'disabled'):
        showResults(userLocation, productClass)
    

def takeLocation():
    global userLocation
    userLocation = LocationEntry.get()
    userLocation = userLocation + " Κοζάνη Ελλάδα"
    LocationEntry.configure(state='disabled')
    
    if (str(comboClasses["state"]) == 'disabled') and (str(LocationEntry["state"]) == 'disabled'):
        showResults(userLocation, productClass)
    
def showResults(userLocation,productClass):
    
    geolocator = Nominatim(user_agent="pharmacyAnytime")
    location = geolocator.geocode(userLocation)
    latlong = [location.latitude, location.longitude]
    
    
    # Web Scraping    
    URL = "https://fskozanis.gr/efhmeries/kozanh/"
        
    r = requests.get(URL)
    soup = BeautifulSoup(r.content, 'html5lib')
        
    # Web Scraping the Address
    table_tags = soup.find_all('li', attrs = {'class':''})
    
    # Check for open pharmacies
    openPharmaciesTags = []
    openPharmacies = []
    
    for i in range(len(table_tags)-4):
        
        tag_text_newline = table_tags[i].text.split('\n')
            
        # Store only desired string values (phone, name, address)
        temp_list = []
            
        for text in tag_text_newline:
            strip_string = text.strip()
            if strip_string == '' or strip_string == 'Οδηγίες' or strip_string == 'StreetView':
                continue
            temp_list.append(strip_string)
            
        name = temp_list[0]
        
        openPharmaciesTags = table_tags[i].find('span', attrs = {'class':'icon li_location li_location_on'})
        
        if openPharmaciesTags != None:
            openPharmacies.append(name)    
    
    #Float convertions
    usersLatitude = float(latlong[0])
    usersLongtitude = float(latlong[1])
    
    # Connect to the Base
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "1234"))
    
    # We must find all the phramcies that has the chosen product class
    with driver.session() as session:
            results = session.write_transaction(getNodeViaClass, productClass)
        
    # Check if the open pharmacies match the chosen class of product
    matchedOpenPharmacies = []
    
    for i in range(len(results)):
        tempName = results[i]['a'].get('name')
        for j in range(len(openPharmacies)):
            if tempName == openPharmacies[j]:
                matchedOpenPharmacies.append(i)
                break;
    
    if len(matchedOpenPharmacies)==0:
        outputInfoText = "Δεν υπάρχουν διαθέσιμα φαρμακεία για τη συγκεκριμένη κατηγορία προιόντων αυτή τη στιγμή."
    
    else:
    
        min_distance = 1000000000
        # Find the nearest one
        for i in range(len(matchedOpenPharmacies)):
            x = results[i]['a'].get('latitude')
            y = results[i]['a'].get('longtitude')
            
            R = 6373.0
        
            lat1 = radians(float(x))
            lon1 = radians(float(y))
            lat2 = radians(usersLatitude)
            lon2 = radians(usersLongtitude)
        
            dlon = lon2 - lon1
            dlat = lat2 - lat1
        
            a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
            distance = R * c
            
            if distance < min_distance:
                min_distance = distance
                min_index = i
        
        #print
        s0 = "Κοντινότερο Φαρμακείο:\n"
        s1 = results[min_index]['a'].get('name') + "\n"
        s2 = results[min_index]['a'].get('address') + "\n"
        s3 = results[min_index]['a'].get('phone') + "\n"
        s4 = "Απόσταση: %5.1f" % (min_distance*1000) + " m"
        
        outputInfoText = s0 + s1 + s2 + s3 + s4
       
    
    
    #graphical user interface
    InfoText = tk.Text(app, wrap='word', bg='white', height=10, width=48, font="Verdana 9 italic bold")
    InfoText.insert(tk.INSERT, outputInfoText)
    InfoText.place(x=23,y=260)
    InfoText.config(state='disable')
    
    thankLabel = tk.Label(app, bg='spring green', height=2, width=54, padx = 5, justify='center', font="Verdana 11 italic bold", text="Πάντα δίπλα σας!                 ")
    thankLabel.place(x=0,y=405)


# Global Variable
productClass = ''
userLocation = ''

app = tk.Tk()
#app.iconbitmap('C:\\Users\\Nikos Pavlidis\\Desktop\\PharmacyAnytime\\Icons-Land-Gis-Gps-Map-Pharmacy.ico')
app.iconbitmap('C:\\Users\\Nikos Pavlidis\\Dropbox\\UNIVERSITY\\Advanced Data Management\\Project\\Pavlidis_Nikolaos_1185_PharmacyAnytime\\Icons-Land-Gis-Gps-Map-Pharmacy.ico')
app.geometry("480x480+200+200")
app.title("Pharmacy AnyTime")
app.resizable(False, False)
app.configure(bg='spring green')

style = ThemedStyle(app)

style.set_theme("black")

welcomeLabel = tk.Label(app, bg='spring green', height=2, width=54, padx = 5, justify='center', font="Verdana 11 italic bold", text='Καλωσήρθατε στο PharmacyAnyTime!            ')
welcomeLabel.place(x=0,y=0)

T = tk.Label(app, bg='light grey', height=3, width=480, wraplength=480 ,anchor='w', justify='left', font="Arial 10 bold", text='Διαλέξτε την κατηγορία προιόντος που επιθυμείτε:')
T.place(x=0, y=50)

comboClasses = ttk.Combobox(app, state='readonly', values=["Αντηλιακά", "Βρεφικά", "Καλλωπισμός", "Στοματική_Υγιεινή",  "Ομοιοπαθητικά"])
comboClasses.place(x=100, y=112)
comboClasses.current(0)

okButton = ttk.Button(app, width=10, text="       OK",  command = selectProduct)
okButton.place(x=270, y=110)

T2 = tk.Label(app, bg='light grey', height=3, width=480, wraplength=480 ,anchor='w', justify='left', font="Arial 10 bold", text='Δώστε την τοποθεσία σας (π.χ. Ροδόπης 10)')
T2.place(x=0, y=140)

LocationEntry = ttk.Entry(app, width=45)
LocationEntry.place(x=45, y=210)

okButton2 = ttk.Button(app, width=10, text="       OK", command = takeLocation)
okButton2.place(x=335, y=208)

app.mainloop()
