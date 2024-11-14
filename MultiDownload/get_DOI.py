import csv
import serpapi
import time
import os
import json
import pandas as pd
from elsapy.elsclient import ElsClient
from elsapy.elsdoc import FullDoc
from crossref.restful import Works
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup
import requests
import Global_Journal
works = Works()
ElsevierClient = ElsClient('elsevier_apiKEY')
ACS_new = []
ACS = pd.read_csv('carbondeposit2005_2015ACSyears_list.csv')
for i in ACS.values:
    print(i[-1])
    if 'http' in i[-1]:
        if 'meta' in i[-1]:
            tmp = i[-1].split('/')
            ACS_new.append(tmp[-3]+ '/' + tmp[-2]+ '/' + tmp[-1])
        else:
            tmp = i[-1].split('/')
            ACS_new.append(tmp[-2] + '/' + tmp[-1])
    else:
        ACS_new.append(i[-1])
for j in ACS_new:
    print(j)
with open('./carbondeposit2005_2015ACSyears_list_correct.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    for j in ACS_new:
        writer.writerow([-1,j])
Springer_new = []
Springer = pd.read_csv('carbondeposit2005_2015Springeryears_list.csv')
for i in Springer.values:
    if 'nature' in i[-1]:
        Springer_new.append('10.1038' + '/' + i[-1].split('/')[-1])
        pass
    else:
        tmp = i[-1].split('/')
        Springer_new.append(tmp[-2] + '/' + tmp[-1])
with open('./carbondeposit2005_2015Springeryears_list_correct.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    for j in Springer_new:
        writer.writerow([-1,j.replace('.pdf', '')])
Wiley_new = []
Wiley = pd.read_csv('carbondeposit2015_2015Wileyyears_list.csv')
for i in Wiley.values:
    if 'http' in i[-1]:
        tmp = i[-1].split('/')
        Wiley_new.append(tmp[-2] + '/' + tmp[-1])
    else:
        Wiley_new.append(i[-1])
with open('./carbondeposit2005_2015Wileyyears_list_correct.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    for j in Wiley_new:
        writer.writerow([-1,j.replace('.pdf', '')])
