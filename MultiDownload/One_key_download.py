import os
import sys
import tqdm
from .Advanced_Research import search_online
from .Multi_download import run_functions
from . import Global_Journal
def One_key_download(research_keys_fun, screen_keys_fun, Target_Journal, API, year_start, year_end, Publication_name,
                     only_high_IF=True, only_second_third=False, Demo=True, max_run=5, maxtime=500, STDOUT=sys.stdout):
    try:
        os.mkdir('./LiteratureSearchWorkDir')
    except FileExistsError:
        pass
    csv_name = search_online(research_keys_fun, Target_Journal, API, year_start, year_end,
                             Journal_name=Publication_name, Demo=Demo, STDOUT=STDOUT)
    print('cat Meow: {}'.format(csv_name))
    run_functions(max_run, './search_results/{}.csv'.format(csv_name), screen_keys_fun, max_time=500,
                  only_high_IF=only_high_IF,
                  only_second=only_second_third)
    Global_Journal.Print('success!!!')
    return 0
ACS_publications = Global_Journal.ACS_publications
Wiley_publications = Global_Journal.Wiley_publications
ELSEVIER_publications_1 = Global_Journal.ELSEVIER_publications_1
ELSEVIER_publications_2 = Global_Journal.ELSEVIER_publications_2
springer_publications = Global_Journal.springer_publications_1 + Global_Journal.springer_publications_2
Science = Global_Journal.Science
RSC_publications = Global_Journal.RSC_publications_1 + Global_Journal.RSC_publications_2
High_IF_publications = {'ACS_high_IF': ACS_publications,
                        'Wiley_high_IF': Wiley_publications,
                        'ELSEVIER_high_IF_1': ELSEVIER_publications_1,
                        'ELSEVIER_high_IF_2': ELSEVIER_publications_2,
                        'springer_high_IF': springer_publications,
                        'Science': Science,
                        'RSC_high_IF': RSC_publications}
ACS_second = Global_Journal.ACS_second
Wiley_second_search_1 = Global_Journal.Wiley_second_search_1
Wiley_second_search_2 = Global_Journal.Wiley_second_search_2
ELSEVIER_second_search_1 = Global_Journal.ELSEVIER_second_search_1
ELSEVIER_second_search_2 = Global_Journal.ELSEVIER_second_search_2
ELSEVIER_second_search_3 = Global_Journal.ELSEVIER_second_search_3
springer_second = Global_Journal.springer_second
RSC_second = Global_Journal.RSC_second
Low_IF_publications = {'ELSEVIER_low_IF_4': Global_Journal.ELSEVIER_second_search_4,
                       'ELSEVIER_low_IF_5': Global_Journal.ELSEVIER_second_search_5,
                       'Springer_Low_IF_2': Global_Journal.springer_second_2,
                       'Wiley_low_IF_3': Global_Journal.Wiley_second_search_3,
                       'ACS_low_IF_2': Global_Journal.ACS_second_2,
                       'MDPI_low_IF': Global_Journal.MDPI_second,
                       'Frontiers_low_IF': Global_Journal.Frontiers_second,
                       'Taylor_low_IF': Global_Journal.Taylor_second,
                       'Other_low_IF': Global_Journal.Other_second}
def User_pages(API_key, Key_words_fun2, Screen_words_fun2, year_start, year_end, only_High_if_fun2=True,
               only_low_if_fun2=False, Demo=True, STDOUT=sys.stdout, maxrun=5):
    if only_High_if_fun2 and only_low_if_fun2:
        only_High_if_fun2 = False
        only_low_if_fun2 = False
    if len(API_key) != 0:
        pass
    else:
        print('No API keys')
        return 0
    if len(Key_words_fun2) != 0:
        pass
    else:
        print('No Key words')
        return 0
    if len(Screen_words_fun2) != 0:
        pass
    else:
        print('No Screen words')
        return 0
    if only_High_if_fun2:
        print('only High IF')
        for publisher in tqdm.tqdm(([list(High_IF_publications.keys())[0]] if Demo else High_IF_publications),
                                   desc='High IF publishers', file=STDOUT):
            name = publisher
            publisher_list = High_IF_publications[name]
            One_key_download(Key_words_fun2, Screen_words_fun2, publisher_list, API_key, year_start, year_end,
                             name, only_high_IF=only_High_if_fun2, only_second_third=only_low_if_fun2, Demo=Demo,
                             STDOUT=STDOUT, max_run=maxrun)
        print('all is down, Thanks !!!')
        return 0
    else:
        if only_low_if_fun2:
            print('only Low IF')
            for publisher in tqdm.tqdm(([list(Low_IF_publications.keys())[0]] if Demo else Low_IF_publications),
                                       desc='Low IF publishers', file=STDOUT):
                name = publisher
                publisher_list = Low_IF_publications[name]
                One_key_download(Key_words_fun2, Screen_words_fun2, publisher_list, API_key, year_start, year_end,
                                 name, only_high_IF=only_High_if_fun2, only_second_third=only_low_if_fun2, Demo=Demo,
                                 STDOUT=STDOUT)
        else:
            print('download_all')
            print('High IF')
            for publisher in tqdm.tqdm(([list(High_IF_publications.keys())[0]] if Demo else High_IF_publications),
                                       desc='High IF publishers', file=STDOUT):
                name = publisher
                publisher_list = High_IF_publications[name]
                One_key_download(Key_words_fun2, Screen_words_fun2, publisher_list, API_key, year_start, year_end,
                                 name, only_high_IF=only_High_if_fun2, only_second_third=only_low_if_fun2, Demo=Demo,
                                 STDOUT=STDOUT)
            print('LOW IF')
            for publisher in tqdm.tqdm(([list(Low_IF_publications.keys())[0]] if Demo else Low_IF_publications),
                                       desc='Low IF publishers', file=STDOUT):
                name = publisher
                publisher_list = Low_IF_publications[name]
                One_key_download(Key_words_fun2, Screen_words_fun2, publisher_list, API_key, year_start, year_end,
                                 name, only_high_IF=only_High_if_fun2, only_second_third=only_low_if_fun2, Demo=Demo,
                                 STDOUT=STDOUT)
if __name__ == '__main__':
    apikeys = []
    Key_words_fun2 = ['propane dehydrogenation']
    Screen_words_fun2 = ['PDH', 'ODH', 'propane dehydrogenation']
    User_pages(apikeys, Key_words_fun2, Screen_words_fun2, 2020, 2024, only_High_if_fun2=True,
               only_low_if_fun2=False, Demo=True)
