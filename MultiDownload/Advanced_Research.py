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
import tqdm
import shutil
import sys
from . import Global_Journal
works = Works()
ElsevierClient = ElsClient(os.getenv('ElsClientKey', ''))
def make_query(query, Journal):
    query_list = query
    Journal_list = Journal
    Journal_screen = ''
    query_screen = ''
    for k in query_list:
        query_screen = query_screen + '\"' + k + '\"' + ' AND '
    for i in Journal_list:
        Journal_screen = Journal_screen + ' OR ' + 'source:"{}"'.format(i)
    query_list = query_screen + '(' + Journal_screen[4:] + ')'
    return query_list
def get_MDPI_doi_and_year(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    doi_tag = soup.find('meta', attrs={'name': 'dc.identifier'})
    year_tag = soup.find('meta', attrs={'name': 'dc.date'})
    if doi_tag and year_tag:
        doi = doi_tag['content']
        year = year_tag['content'].split('-')[0]
        return doi, year
    else:
        return "DOI or year not found", None
def search_literature(query, api_key, year_start, year_end, start=0):
    client = serpapi.Client()
    params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": api_key,
        "as_ylo": year_start,
        'as_yhi': year_end,
        "num": 20,
        "start": start
    }
    Global_Journal.Print('params', params)
    results = client.search(params)
    return results
def GetYearFromDOI(DOI):
    wall_time = 0
    while wall_time <= 3:
        try:
            metadata = works.doi(DOI)
            if metadata:
                if metadata.get("published-print", ''):
                    year = metadata["published-print"]["date-parts"][0][0]
                elif metadata.get("published-online", ''):
                    year = metadata["published-online"]["date-parts"][0][0]
                elif metadata.get("created", ''):
                    year = metadata["created"]["date-parts"][0][0]
                else:
                    return -1
                return year
            else:
                return -1
        except:
            wall_time = wall_time + 1
    return -1
def get_link(results):
    link = []
    for result in results['organic_results']:
        try:
            link.append(result['link'])
        except KeyError:
            Global_Journal.Print('cannot found this result !')
            with open("./search_logs/cannot_found_link.json", "a") as f:
                json.dump(dict(result), f, indent=4)
            pass
    return link
def save_to_csv(data, csv_file_path, other_information=''):
    keyword_name = csv_file_path[0].replace(' ', '').replace(':', '') + other_information
    try:
        os.mkdir('./search_results')
    except FileExistsError:
        pass
    df = pd.DataFrame(data, columns=['year', 'DOI'])
    df.to_csv('./search_results/{}.csv'.format(keyword_name), index=False)
    return keyword_name
def get_all(key_words_fun, ACS_second_fun, api_key, year_start, year_end):
    query = make_query(key_words_fun, ACS_second_fun)
    links = []
    pages = 0
    long = 0
    api_number = 0
    retry = 0
    while True:
        long = long + 1
        try:
            if api_number >= len(api_key):
                print('all API is down')
                return links
            Global_Journal.Print('use people_{}\'s API-Key'.format(api_number))
            results = search_literature(query, api_key[api_number], year_start, year_end, start=pages * 20)
            Global_Journal.Print('type', type(results))
            try:
                os.mkdir('./search_logs')
            except FileExistsError:
                pass
            T = time.localtime()
            time_name = str(T.tm_year) + '_' + str(T.tm_mon) + '_' + str(T.tm_mday) + '_' + str(T.tm_hour) + '_' + str(
                T.tm_min) + '_' + str(T.tm_sec)
            Global_Journal.Print(time_name)
            with open("./search_logs/{}_results_log_pages_{}.json".format(time_name, pages), "w") as f:
                Global_Journal.Print('load log!!!!')
                json.dump(dict(results), f, indent=4)
        except serpapi.HTTPError:
            retry = retry + 1
            if retry <= 3:
                Global_Journal.Print('retry API, {} times'.format(retry))
                continue
            else:
                api_number = api_number + 1
                retry = 0
                continue
        try:
            page_data = get_link(results)
            for link in page_data:
                links.append(link)
                Global_Journal.Print(len(links))
        except KeyError:
            print('already get all results!')
            return links
        pages = pages + 1
        time.sleep(2)
        Global_Journal.Print('Pages {}'.format(pages))
        if pages >= 2:
            print('Too much results, please check the query!!!')
            print('pages: {}'.format(pages))
            print(links)
            return links
def search_online(key_words_fun1, Journal_list, Api_list_fun, year_start, year_end, Journal_name='', Demo=True,
                  STDOUT=sys.stdout):
    DOIs = []
    all_ans = get_all(key_words_fun1, Journal_list, Api_list_fun, year_start, year_end)
    search_info = str(year_start) + '_' + str(year_end) + Journal_name
    for ans in tqdm.tqdm((all_ans[:Global_Journal.DemoNumber] if Demo else all_ans), desc='search_online', file=STDOUT):
        if ans.find('rsc') != -1:
            tmp_doi = '10.1039/' + ans.split('/')[-1]
            DOIs.append(['DOI', tmp_doi])
        elif ans.find('mdpi') != -1:
            tmp_ans = get_MDPI_doi_and_year(ans.replace('	', ''))
            DOIs.append(['DOI', tmp_ans[0]])
        elif ans.find('pii') != -1:
            wall_time = 0
            while True:
                try:
                    DOI = FullDoc(sd_pii=ans.split('/')[-1])
                    DOI.read(ElsevierClient)
                    DOI = DOI.int_id
                    DOIs.append(['DOI', DOI])
                    Global_Journal.Print('ELSEVIER doi found, the link is : {}'.format(DOI))
                    break
                except TypeError:
                    DOIs.append(['DOI', ans])
                    Global_Journal.Print('ELSEVIER doi not found, the link is : {}'.format(ans))
                    break
                except (TimeoutError, ConnectionError):
                    wall_time = wall_time + 1
                    if wall_time >= 3:
                        break
        else:
            DOIs.append(['DOI', ans])
    filename = save_to_csv(DOIs, key_words_fun1, search_info)
    year_list = []
    for doi_year in DOIs:
        year_list.append([GetYearFromDOI(doi_year[-1]), doi_year[-1]])
    save_to_csv(year_list, key_words_fun1, search_info + 'years_list')
    return filename
if __name__ == '__main__':
    filename = ''
