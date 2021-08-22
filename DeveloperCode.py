# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 20:06:51 2020

@author: Nikos Pavlidis

"""

"""
This program builds the pharmacy db in neon4j seting labels,properties and connections.
The program works only the first time that is executed because the id of the graphs in neon4j
are not deleted each time you run the program.
If you want to run the program again, FIRSTLY delete the db in neon4j and SECONDLY stop the db
and start it again.
"""

import requests
from neo4j import GraphDatabase
from bs4 import BeautifulSoup

def addNode(tx, entry):
        
        tx.run("CREATE (n:Pharmacy {name: $name, address: $address, phone: $phone, latitude: $latitude, longtitude: $longtitude})", name=entry[0], address = entry[1], phone = entry[2], latitude=entry[3], longtitude=entry[4])
        
def addLabelNode(tx):
    
        tx.run("CREATE (n:Αντηλιακά)")
        tx.run("CREATE (n:Καλλωπισμός)")
        tx.run("CREATE (n:Βρεφικά)")
        tx.run("CREATE (n:Στοματική_Υγιεινή)")
        tx.run("CREATE (n:Ομοιοπαθητικά)")

#the connections are built cyclically so that we have equal possible results     
        
def setConnections(tx, pharmaciesNum):
    
    for i in range(pharmaciesNum):
        
        rem = i%5
        if rem == 0:
            tx.run("MATCH (a:Pharmacy),(b:Ομοιοπαθητικά) WHERE ID(a)=$counter CREATE (a)-[r:RELTYPE {name:'IN_STOCK'}]->(b)", counter=i)
        elif rem == 1:
            tx.run("MATCH (a:Pharmacy),(b:Αντηλιακά) WHERE ID(a)=$counter CREATE (a)-[r:RELTYPE {name:'IN_STOCK'}]->(b)", counter=i)
        elif rem == 2:
            tx.run("MATCH (a:Pharmacy),(b:Καλλωπισμός) WHERE ID(a)=$counter CREATE (a)-[r:RELTYPE {name:'IN_STOCK'}]->(b)", counter=i)
        elif rem == 3:
            tx.run("MATCH (a:Pharmacy),(b:Βρεφικά) WHERE ID(a)=$counter CREATE (a)-[r:RELTYPE {name:'IN_STOCK'}]->(b)", counter=i)
        else:
            tx.run("MATCH (a:Pharmacy),(b:Στοματική_Υγιεινή) WHERE ID(a)=$counter CREATE (a)-[r:RELTYPE {name:'IN_STOCK'}]->(b)", counter=i)      
            
            
#main function       

if __name__ == "__main__":
    
    
    # DataBase Graph Creation and Connect
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "1234"))
              

    # Web Scraping    
    URL = "https://fskozanis.gr/efhmeries/kozanh/"
    
    r = requests.get(URL)            
    soup = BeautifulSoup(r.content, 'html5lib')
        
    tags_check = soup.find_all('li', attrs = {'class':''})
        
    # Web Scraping the Address
    table_tags = soup.find_all('li', attrs = {'class':''})
    
    pharmaciesNum = len(table_tags)-4
    
    # Get the Latitude and Longtitude
    for i in range(len(table_tags)-4):
                
        geo_text = table_tags[i].find('a', attrs={'class':'btn btn-default streetview'})
        x = str(geo_text)
        pos = x.find('cbll')
        pos_comma = x.find(',',pos)
        
        latitude = x[pos+5 : pos_comma]
        
        pos_and = x.find('&', pos_comma)
        
        longtitude = x[pos_comma+1: pos_and]
        
        tag_text_newline = table_tags[i].text.split('\n')
        
        # Store only desired string values (phone, name, address)
        temp_list = []
        
        for text in tag_text_newline:
            strip_string = text.strip()
           
            if strip_string == '' or strip_string == 'Οδηγίες' or strip_string == 'StreetView':
                    continue
            temp_list.append(strip_string)        
          
        name = temp_list[0]
        address = temp_list[1]
        phone = "+30" + temp_list[2]
        
        entry = [name, address, phone, latitude, longtitude]   
                
        
        with driver.session() as session:
            session.write_transaction(addNode, entry)
    
    #SetLabels
    with driver.session() as session:
        session.write_transaction(addLabelNode)
        
        
    #Connections
    with driver.session() as session:
        session.write_transaction(setConnections, pharmaciesNum)
          
    
    driver.close()