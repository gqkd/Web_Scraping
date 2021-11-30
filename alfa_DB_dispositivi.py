from bs4 import BeautifulSoup
from requests_html import HTMLSession
from urllib.parse import urljoin
import re
import pandas as pd
import numpy as np
import sys

url = "https://www.salute.gov.it/interrogazioneDispositivi/RicercaDispositiviServlet?action=ACTION_MASCHERA"
url_next = "https://www.salute.gov.it/interrogazioneDispositivi/RicercaDispositiviServlet?action=ACTION_PAGE_INC"
columns = ["TIPOLOGIA_DISPOSITIVO","IDENTIFICATIVO_DI_REGISTRAZIONE_BD/RDM","ISCRITTO_AL_REPERTORIO","CODICE_ATTRIBUITO_DAL_FABBRICANTE/ASSEMBLATORE",
            "NOME_COMMERCIALE_E_MODELLO","CND","CLASSE_CE","DATA_PRIMA_PUBBLICAZIONE","DATA_FINE_IMMISSIONE_IN_COMMERCIO",
            "FABBRICANTE","DENOMINAZIONE_FABBRICANTE","CODICE_FISCALE_FABBRICANTE","PARTITA_IVA/VAT_NUMBER_FABBRICANTE","NAZIONE_FABBRICANTE",
            "MANDATARIO","DENOMINAZIONE_MANDATARIO","CODICE_FISCALE_MANDATARIO","PARTITA_IVA/VAT_NUMBER_MANDATARIO","NAZIONE_MANDATARIO"]

#starting the session
session = HTMLSession()

#get request to url, if it is java decomment html.render()
res = session.get(url)
# res.html.render()

#parsing the HTML with soup
soup = BeautifulSoup(res.html.html, "html.parser")
forms = soup.find_all("form")

#dict for details of the form
for form in forms:
    details = {}
    # take action and method with a get request
    action = form.attrs.get("action")
    method = form.attrs.get("method", "get")
    #dict of details
    inputs = []
    for input_tag in form.find_all("input"):
        input_type = input_tag.attrs.get("type", "text")
        input_name = input_tag.attrs.get("name")
        input_value =input_tag.attrs.get("value", "")
        inputs.append({"type": input_type, "name": input_name, "value": input_value})
    details["action"] = action
    details["method"] = method
    details["inputs"] = inputs


data = {}

#this loop take in input form inputs and create the dict, is not needed
# for input_tag in details["inputs"]:
#     if input_tag["type"] == "hidden":
#         # if it is hidden take the default
#         data[input_tag["name"]] = input_tag["value"]
#     elif input_tag["type"] != "submit":
#         # all of them in which there is the submit
#         value = input(f"Enter the value of the field '{input_tag['name']}' (type: {input_tag['type']}): ")
#         data[input_tag["name"]] = value
# print(data)

#interface
print("How do you wanna search:\n")
print(details['inputs'])
cont=0
for i,det in enumerate(details['inputs']):
    if not det['name'] == None:
        cont += 1
        print(f"{i}.{det['name']}")

firstinput = input()
try:
    if int(firstinput) >= cont or int(firstinput) < 0:
        print("Input Error, try a new input")
        sys.exit(1)
except:
    print("Input Error, try a new input")
    sys.exit(1)

for i, det in enumerate(details['inputs']):
    if i==int(firstinput):
        secondinput = input(f"{det['name']}:\n")
        data[det['name']] = secondinput
print(f"Searching in form: {list(data.keys())[0]} the value: {list(data.values())[0]}")


# join the url with the action (form request URL)
url = urljoin(url, details["action"])
print(f"Reaching URL:\n{url}")

if details["method"] == "post":
    res2 = session.post(url, data=data)
elif details["method"] == "get":
    res = session.get(url, params=data)


###########################################  page results ####################################################################
#parse the page in soup
soup2 = BeautifulSoup(res2.html.html, "html.parser")
#trovo il pezzo dove stanno scritte le info di numero di pagine e numero di risultati
#find info about number of pages and total number of results
find_limit = soup2.find(string=re.compile('Num. Pagine:'))
try:
    num_pag = int(str(find_limit).split('Num. Pagine:')[1].split('<')[0])
except IndexError:
    print("Input Error, try a new input")
    sys.exit(1)
num_disp = int(str(find_limit).split('Num. Dispositivi:')[1].split('<')[0])
print(f"Number of pages:{num_pag}       Number of results:{num_disp}")

tabella = []
for page in range(num_pag):
    print(f'-------------------------------------- page {page+1} -----------------------------------------------------')
    
    for tbody in soup2.find_all('tbody'):
        tmp=[]
        flag_fabb = 0
        #print('-------------------------------------print tbody-----------------------------------------------------')
        #print(tbody.get_text())
        for count,tr in enumerate(tbody):
            # print('----------------------------------print tag--------------------------------------------------------')
            # print(count,tag,type(tag))
            if str(type(tr)) != "<class 'bs4.element.NavigableString'>":
                #print('-------------------------------------print tr-----------------------------------------------------')
                #print(tr)
                for count,minitag in enumerate(tr.find_all('td')):
                    #print('---------------------------------print minitag---------------------------------------------------------')
                    #print(count,minitag.string)
                    if minitag.string == 'FABBRICANTE':
                        flag_fabb = 1
                    #in this case 'mandatario' comes before 'fabbricante', so 'fabbricante' is not in the row
                    if minitag.string == 'MANDATARIO' and flag_fabb==0:
                        tmp.append(['-']*5)
                    tmp.append(minitag.string.replace('\xa0','-'))
                    #print(tmp)
        tabella.append(tmp)
    risultato = session.get(url_next)
    soup2 = BeautifulSoup(risultato.html.html, "html.parser")

#need to resize all the rows in the tabella
max_num_elements = max(len(row) for row in tabella)
for row in tabella:
    if not len(row) == max_num_elements:
        row.extend(['-']*(max_num_elements-len(row)))


df = pd.DataFrame(tabella,columns=columns)
df.to_csv('export.csv')
    



