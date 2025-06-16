import difflib
import os
import re
import sys
import time
import pandas as pd
import requests
import tqdm
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.common.exceptions import InvalidArgumentException
from selenium.common.exceptions import NoSuchDriverException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from . import Global_Journal
def get_journal_and_url(doi):
    base_url = "https://api.crossref.org/works/"
    doi = doi.replace('/full', '')
    try:
        response = requests.get(base_url + doi)
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code}")
        data = response.json()['message']
        journal_name = data.get('container-title', [None])[0]
        article_url = data.get('URL')
        Global_Journal.Print(journal_name.replace('&amp;', '&'))
        return journal_name.replace('&amp;', '&'), article_url
    except Exception:
        if doi.find('mdpi') != -1:
            return 'MDPI', doi
        return 'error', 'error'
def is_similar(A, B, threshold=0.95):
    s = difflib.SequenceMatcher(None, A, B)
    return s.ratio() >= threshold
def get_publications(journal_name, only_high_if=False, only_second=False):
    if only_high_if:
        main_group = False
        Other_publications = []
    else:
        main_group = True
        Other_publications = []
    custom_journals = load_custom_journals()
    print('custom_journals added: ')
    for i in custom_journals:
        print(i)
    User_defined = Global_Journal.User_defined
    ACS_publications = Global_Journal.ACS_publications
    Wiley_publications = Global_Journal.Wiley_publications
    ELSEVIER_publications = Global_Journal.ELSEVIER_publications_1 + Global_Journal.ELSEVIER_publications_2 + Global_Journal.ELSEVIER_publications_3
    springer_publications = Global_Journal.springer_publications_1 + Global_Journal.springer_publications_2
    springer_special = "Nature communications"
    Science = ["Science"]
    RSC_publications = Global_Journal.RSC_publications_1 + Global_Journal.RSC_publications_2
    MDPI_publications = []
    Frontiers_publications = []
    Taylor_publications = []
    ACS_second = Global_Journal.ACS_second+Global_Journal.ACS_second_2
    Wiley_second = Global_Journal.Wiley_second_search_1 + Global_Journal.Wiley_second_search_2 + Global_Journal.Wiley_second_search_3
    ELSEVIER_second = Global_Journal.ELSEVIER_second_search_1 + Global_Journal.ELSEVIER_second_search_2 + Global_Journal.ELSEVIER_second_search_3 + Global_Journal.ELSEVIER_second_search_4 + Global_Journal.ELSEVIER_second_search_5
    springer_second = Global_Journal.springer_second + Global_Journal.springer_second_2
    RSC_second = Global_Journal.RSC_second
    MDPI_second = Global_Journal.MDPI_second
    Frontiers_second = Global_Journal.Frontiers_second
    Taylor_second = Global_Journal.Taylor_second
    Other_second = Global_Journal.Other_second
    if only_second:
        Global_Journal.Print('Only download low IF papers')
        ACS_publications = []
        Wiley_publications = []
        ELSEVIER_publications = []
        springer_publications = []
        RSC_publications = []
        Taylor_publications = []
        Other_publications = []
    else:
        pass
    if main_group:
        ACS_publications = ACS_publications + ACS_second
        Wiley_publications = Wiley_publications + Wiley_second
        ELSEVIER_publications = ELSEVIER_publications + ELSEVIER_second
        springer_publications = springer_publications + springer_second
        RSC_publications = RSC_publications + RSC_second
        MDPI_publications = MDPI_publications + MDPI_second
        Frontiers_publications = Frontiers_publications + Frontiers_second
        Taylor_publications = Taylor_publications + Taylor_second
        Other_publications = Other_publications + Other_second
    else:
        Global_Journal.Print('Only download high IF papers')
    if len(custom_journals) >0:
        warning_art = '''
        +-------------------------------------------+
        |           ! CAUTION WARNING !              |
        |      ! PROCEED WITH CAUTION !              |
        +-------------------------------------------+
        '''
        print(warning_art)
        print(
     '''other journal list will be cleaned!!!
     you should check the journal carefully!!!''')
        ACS_publications = []
        Wiley_publications = []
        ELSEVIER_publications = []
        springer_publications = []
        RSC_publications = []
        MDPI_publications = []
        Frontiers_publications = []
        Taylor_publications = []
        Other_publications = []
    Global_Journal.Print('journal_name is : ', journal_name)
    if is_similar(journal_name.lower().replace(' ', ''), springer_special.lower().replace(' ', '')):
        return 'springer_special'
    else:
        pass
    for MDPI in MDPI_publications:
        if is_similar(journal_name.lower().replace(' ', ''), MDPI.lower().replace(' ', '')):
            Global_Journal.Print(journal_name, MDPI)
            return 'MDPI'
        else:
            pass
    for Frontiers in Frontiers_publications:
        if is_similar(journal_name.lower().replace(' ', ''), Frontiers.lower().replace(' ', '')):
            Global_Journal.Print(journal_name, Frontiers)
            return 'Frontiers'
        else:
            pass
    for journal in custom_journals:
        if is_similar(journal_name.lower().replace(' ', ''), journal.lower().replace(' ', '')):
            Global_Journal.Print(journal_name, journal)
            return 'User_defined'
    for ACS in ACS_publications:
        if is_similar(journal_name.lower().replace(' ', ''), ACS.lower().replace(' ', '')):
            Global_Journal.Print(journal_name, ACS)
            return 'ACS'
        else:
            pass
    for science_journal in Science:
        if is_similar(journal_name.lower().replace(' ', ''), science_journal.lower().replace(' ', '')):
            Global_Journal.Print(journal_name, science_journal)
            return 'Science'
        else:
            pass
    for wiley in Wiley_publications:
        if is_similar(journal_name.lower().replace(' ', ''), wiley.lower().replace(' ', '')):
            Global_Journal.Print(journal_name, wiley)
            return 'wiley'
        else:
            pass
    for ELSEVIER in ELSEVIER_publications:
        if is_similar(journal_name.lower().replace(' ', ''), ELSEVIER.lower().replace(' ', '')):
            Global_Journal.Print(journal_name, ELSEVIER)
            return 'ELSEVIER'
        else:
            pass
    for springer in springer_publications:
        if is_similar(journal_name.lower().replace(' ', ''), springer.lower().replace(' ', '')):
            Global_Journal.Print(journal_name, springer)
            return 'springer'
        else:
            pass
    for RSC in RSC_publications:
        if is_similar(journal_name.lower().replace(' ', ''), RSC.lower().replace(' ', '')):
            Global_Journal.Print(journal_name, RSC)
            return 'RSC'
        else:
            pass
    for user_journal in User_defined:
        if is_similar(journal_name.lower().replace(' ', ''), user_journal.lower().replace(' ', '')):
            Global_Journal.Print(journal_name, user_journal)
            return 'User_defined'
    for Taylor in Taylor_publications:
        if is_similar(journal_name.lower().replace(' ', ''), Taylor.lower().replace(' ', '')):
            Global_Journal.Print(journal_name, Taylor)
            return 'Taylor'
        else:
            pass
    try:
        for other in Other_publications:
            if is_similar(journal_name.lower().replace(' ', ''), other.lower().replace(' ', '')):
                Global_Journal.Print(journal_name, other)
                return 'other'
            else:
                pass
    except UnboundLocalError:
        return 'other'
    print('ERROR : ', journal_name, 'cannot find publications')
    return None
def load_custom_journals():
    RootDir = os.path.abspath('..')
    """读取自定义期刊文件并更新 Global_Journal.User_defined"""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    journal_file_path = f'{RootDir}{os.sep}Temp{os.sep}custom_journals.txt'
    if os.path.exists(journal_file_path):
        try:
            with open(journal_file_path, 'r', encoding='utf-8') as f:
                journals = [line.strip() for line in f.readlines()
                            if line.strip() and not line.startswith('#')]
            Global_Journal.User_defined.clear()
            Global_Journal.User_defined.extend(journals)
            Global_Journal.Print(f"Loaded {len(journals)} custom journals")
            return Global_Journal.User_defined
        except Exception as e:
            print(f"Error loading custom journals: {str(e)}")
            return []
    else:
        print("No custom journals file found")
        return []
def loading(driver):
    driver.implicitly_wait(2)
    while True:
        page_state = driver.execute_script('return document.readyState;')
        Global_Journal.Print(f'Current page state: {page_state}')
        if page_state == 'complete':
            Global_Journal.Print("Page is fully loaded.")
            break
        elif page_state == 'interactive':
            Global_Journal.Print("Page is partially loaded and is interactive.")
def get_Xpath(publications):
    if publications == 'ACS':
        paper_type = ['//*[@id="pb-page-content"]/div/main/article/div[2]/div/div[2]/div/div/div[1]/div[1]/div/div',
                      '//*[@id="pb-page-content"]/div/main/article/div[2]/div/div[2]/div/div/div[1]/div[1]/div/div/span'
                      ]
        title = ['//*[@id="pb-page-content"]/div/main/article/div[4]/div[1]/div[1]/div/div/h1',
                 '//*[@id="pb-page-content"]/div/main/article/div[2]/div/div[2]/div/div/div[1]/h1',
                 '//*[@id="pb-page-content"]/div/main/article/div[4]/div[1]/div[1]/div/div/h1/span'
                 ]
        abstract = ['//*[@id="abstractBox"]/p',
                    '//*[@id="pb-page-content"]/div/main/article/div[3]',
                    '//*[@id="pb-page-content"]/div/main/article/div[4]/div[1]/div[2]',
                    ]
        full_text = ['//*[@id="pb-page-content"]/div/main/article/div[4]',
                     '//*[@id="pb-page-content"]/div/main/article/div[3]',
                     '//*[@id="pb-page-content"]/div/main/article/div[2]',
                     '//*[@id="pb-page-content"]/div/main/article/div[1]',
                     '/html/body'
                     ]
        return paper_type, title, abstract, full_text
    elif publications == 'Science':
        paper_type = ['//*[@id="main"]/div/article/header/div/div[2]/div[1]/div[2]']
        title = ['//*[@id="main"]/div/article/header/div/h1']
        abstract = ['//*[@id="abstracts"]']
        full_text = ['//*[@id="bodymatter"]']
        return paper_type, title, abstract, full_text
    elif publications == 'wiley':
        paper_type = ['//*[@id="article__content"]/div[2]/div/div[2]']
        title = ['//*[@id="article__content"]/div[2]/div/h1']
        abstract = ['//*[@id="article__content"]/div[5]/article/div[1]']
        full_text = ['//*[@id="article__content"]/div[5]/article/section']
        return paper_type, title, abstract, full_text
    elif publications == 'ELSEVIER':
        paper_type = ['//*[@id="screen-reader-main-title"]/div'
                      ]
        title = ['//*[@id="screen-reader-main-title"]',
                 '//*[@id="sect216"]'
                 ]
        abstract = ['//*[@id="abs0010"]',
                    '//*[@id="abstracts"]'
                    ]
        full_text = ['//*[@id="body"]',
                     '//*[@id="wrapper"]'
                     ]
        return paper_type, title, abstract, full_text
    elif publications == 'springer':
        Global_Journal.Print('Springer cat')
        paper_type = ['//*[@id="content"]/main/article/div[1]/header/ul[1]/li[1]']
        title = ['//*[@id="content"]/main/article/div[1]/header/h1',
                 '//*[@id="main-content"]/main/article/div[1]/header/h1',
                 '//*[@id="main-content"]/main/article/div[1]',
                 '//*[@id="main"]/header/div/div/div[1]/h1',
                 '//*[@id="main-content"]/main/article/div[1]/header/h1',
                 '//*[@id="main"]/header/div/div/div[1]/h1']
        abstract = ['//*[@id="Abs1-content"]',
                    '//*[@id="Abs1-section"]']
        full_text = ['//*[@id="content"]/main/article/div[2]/div[2]',
                     '//*[@id="main-content"]/main/article/div[2]/div[3]',
                     '//*[@id="main-content"]/main/article/div[2]/div[3]',
                     '//*[@id="main-content"]/main/div[3]/div[3]']
        return paper_type, title, abstract, full_text
    elif publications == 'springer_special':
        paper_type = ['//*[@id="content"]/main/article/div[2]/header/ul[1]/li[1]']
        title = ['//*[@id="content"]/main/article/div[2]/header/h1']
        abstract = ['//*[@id="Abs1-content"]']
        full_text = ['//*[@id="content"]/main/article/div[3]/div[1]']
        return paper_type, title, abstract, full_text
    elif publications == 'RSC':
        Global_Journal.Print('RSC')
        paper_type = ['//*[@id="divAbout"]/div[3]/dl/div[2]/dd']
        title = ['//*[@id="maincontent"]/div[2]/div/div[1]/section/article/div[1]/h2']
        abstract = ['//*[@id="maincontent"]/div[2]/div/div[1]/section/article/div[4]/div[1]']
        full_text = ['//*[@id="pnlArticleContent"]']
        return paper_type, title, abstract, full_text
    elif publications == 'MDPI':
        Global_Journal.Print('MDPI')
        paper_type = ['//*[@id="abstract"]/div[2]/article/div/div[1]']
        title = ['//*[@id="abstract"]/div[2]/article/div/h1']
        abstract = ['//*[@id="abstract"]/div[2]/article/div/div[10]']
        full_text = ['//*[@id="abstract"]/div[2]/article/div/div[12]/div[1]']
        return paper_type, title, abstract, full_text
    elif publications == 'Frontiers':
        Global_Journal.Print('Frontiers')
        paper_type = ['//*[@id="similar-articles"]/div[1]/main/div/div/div/div[2]/h1']
        title = ['//*[@id="similar-articles"]/div[1]/main/div/div/div/div[2]/h1']
        abstract = ['//*[@id="similar-articles"]/div[1]/main/div/div/div/div[2]']
        full_text = ['//*[@id="similar-articles"]/div[1]/main/div/div/div/div[3]']
        return paper_type, title, abstract, full_text
    elif publications == 'Taylor':
        Global_Journal.Print('Taylor')
        paper_type = ['//*[@id="fa57727f-b942-4eb8-9ed2-ecfe11ac03f5"]/div/div/div[2]']
        title = ['//*[@id="fa57727f-b942-4eb8-9ed2-ecfe11ac03f5"]/div/div/h1',
                 '//*[@id="fa57727f-b942-4eb8-9ed2-ecfe11ac03f5"]/div']
        abstract = ['//*[@id="mainTabPanel"]/article/div[2]/div[1]']
        full_text = ['//*[@id="mainTabPanel"]/article/div[2]']
        return paper_type, title, abstract, full_text
    elif publications == 'User_defined':
        Global_Journal.Print('User_defined')
        paper_type = ['/html']
        title = ['/html']
        abstract = ['/html']
        full_text = ['/html']
        print('Warning : User Defined Paper Type used, return the whole HTML body, you should compute the paper '
              'download carefully to get better performance!!!')
        return paper_type, title, abstract, full_text
    elif publications == 'other':
        Global_Journal.Print('Other publications!!!')
        paper_type = ['//*[@id="docContent"]/div[1]/div/div[1]/div',
                      '//*[@id="ContentColumn"]/div/div[2]/div[2]/div[1]/div/div[1]/span[1]',
                      '//*[@id="page-content"]/div[1]/div[1]',
                      '//*[@id="main-content"]/div/div/section[1]/article/div[1]',
                      '//*[@id="954036c0-260c-4364-bf69-7d32d1aca475"]/div/div/article/div[3]/div[1]',
                      '//*[@id="__next"]/section/main/div[2]/div[2]/div/div[1]/strong',
                      '//*[@id="goTop"]/div[5]/div[1]/div/div/div[1]/div[1]/h3[2]',
                      '//*[@id="lite-page"]/main/section/section[1]/div/div/h1']
        title = ['//*[@id="docContent"]/div[1]/div/div[1]/div',
                 '//*[@id="docContent"]/div[1]/div/div[1]',
                 '//*[@id="ContentColumn"]/div/div[2]/div[2]/div[1]/div/div[2]',
                 '//*[@id="ContentColumn"]/div/div[2]/div[2]/div[1]/div/div[2]/h1',
                 '//*[@id="page-content"]/div[1]/h1',
                 '//*[@id="main-content"]/div/div/section[1]/article/div[1]',
                 '//*[@id="954036c0-260c-4364-bf69-7d32d1aca475"]/div/div/article/div[3]/div[1]',
                 '//*[@id="__next"]/section/main/div[2]/div[2]/div/div[1]/h1',
                 '//*[@id="goTop"]/div[5]/div[1]/div/div/div[1]/div[1]/h3[2]',
                 '//*[@id="lite-page"]/main/section/section[1]/div/div/h1'
                 ]
        abstract = ['//*[@id="text-container"]/div/div/div[1]',
                    '//*[@id="text-container"]/div/div',
                    '//*[@id="85509154"]/section',
                    '//*[@id="page-content"]/div[3]/div[2]/div[1]',
                    '//*[@id="main-content"]/div/div/section[1]/article/div[3]/div/div[2]/div'
                    '//*[@id="954036c0-260c-4364-bf69-7d32d1aca475"]/div/div/div/div[2]/div/div[1]/article/div[1]',
                    '//*[@id="__next"]/section/main/div[2]/div[2]/div/div[2]/div/p[1]',
                    '//*[@id="p00005"]',
                    '//*[@id="lite-page"]/main/section/div[1]/div[1]/div/div[2]/div[1]']
        full_text = ['//*[@id="text-container"]/div/div/div[1]',
                     '//*[@id="text-container"]/div/div/div[3]',
                     '//*[@id="ContentColumn"]/div/div[2]/div[2]/div[3]/div[2]',
                     '//*[@id="page-content"]/div[3]/div[2]/div[4]',
                     '//*[@id="__next"]/section/main/div[2]/div[2]/div/div[2]'
                     ]
        return paper_type, title, abstract, full_text
    else:
        return None, None, None, None
def find_element(driver, Xpath_name):
    type_num = 0
    type_text = 'element not found'
    while type_num < len(Xpath_name):
        try:
            type_text = driver.find_element(By.XPATH, Xpath_name[type_num]).text
            break
        except NoSuchElementException:
            type_num = type_num + 1
            type_text = 'element not found'
    return type_text
def get_text(doi, paper_type, title, abstract, text):
    driver = None
    try:
        try:
            os.system("taskkill /f /im msedgedriver.exe")
            os.system("pkill -f msedgedriver")
        except Exception:
            pass
        import uuid
        import tempfile
        temp_dir = os.path.join(tempfile.gettempdir(), f"edge_data_{uuid.uuid4().hex}")
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
        os.makedirs(temp_dir, exist_ok=True)
        options = webdriver.EdgeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--incognito")
        options.add_argument(f"--user-data-dir={temp_dir}")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--no-user-data-dir")
        from selenium.webdriver.edge.service import Service
        service = Service(log_path=os.path.devnull)
        driver = webdriver.Edge(options=options, service=service)
        driver.set_page_load_timeout(30)
        wall_time = 0
        while wall_time <= 3:
            wall_time += 1
            try:
                driver.get(doi)
                break
            except InvalidArgumentException:
                if driver:
                    driver.quit()
                return 'InvalidArgumentException', 'InvalidArgumentException', 'InvalidArgumentException', 'InvalidArgumentException'
            except TimeoutException:
                print(f"超时，尝试第 {wall_time} 次...")
                if wall_time == 3 and driver:
                    driver.quit()
                    return 'TimeoutException', 'TimeoutException', 'TimeoutException', 'TimeoutException'
                continue
        loading(driver)
        Wait_num = 0
        judge_loading = ""
        while Wait_num < 5:
            judge_loading = find_element(driver, text)
            if len(judge_loading) < 50:
                Wait_num += 1
                time.sleep(5)
                Global_Journal.Print('sleep 5 second')
            else:
                break
        return (find_element(driver, paper_type),
                find_element(driver, title),
                find_element(driver, abstract),
                judge_loading)
    except Exception as e:
        print(f"获取文本时出错: {str(e)}")
        return 'Exception', 'Exception', 'Exception', f'Error: {str(e)}'
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        try:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
def judge_relevance(key_words, text, relevance_coefficient=0):
    related_keyword_number = 0
    for key_word in key_words:
        if key_word.lower().replace(' ', '') in text.lower().replace(' ', ''):
            related_keyword_number = related_keyword_number + 1
            Global_Journal.Print('Key word: {} found!'.format(key_word))
        else:
            pass
    if related_keyword_number / len(key_words) > relevance_coefficient:
        Global_Journal.Print('related paper (coefficient is {})'.format(related_keyword_number / len(key_words)))
        return True
    else:
        Global_Journal.Print('No-related paper')
        return False
def download_paper(doi, key_words, only_high_IF=False, only_second=False):
    journal, url = get_journal_and_url(doi)
    print(url, journal)
    paper_type, title, abstract, text = get_Xpath(get_publications(journal, only_high_IF, only_second))
    if paper_type is None:
        return 'the paper type of doi ： {} is None'.format(doi)
    type_text, title_text, abstract_text, full_text = get_text(url, paper_type, title, abstract, text)
    if type_text == 'InvalidArgumentException':
        Global_Journal.Print('InvalidArgumentException Error')
        return 'No related paper : {}'.format(doi)
    review_titles = ['review', 'perspective', 'viewpoint']
    if judge_relevance(key_words, title_text + abstract_text):
        is_review = False
        for review_title in review_titles:
            if review_title.lower() in type_text.lower().replace(' ', ''):
                is_review = True
        paper_content = title_text + '\n' + abstract_text + '\n' + full_text
        bytes_data = paper_content.encode('utf-8')
        if is_review:
            txt_name = '{}_Review.txt'.format(doi.replace('/', '_').replace('*', ''))
        else:
            txt_name = '{}.txt'.format(doi.replace('/', '_').replace('*', ''))
            if txt_name.find(':') != -1:
                txt_name = txt_name.replace(':', '').replace('https', '').replace('__pubs.acs.org_', '').replace('=',
                                                                                                                 '').replace(
                    '/', '_').replace('?', '')
        txt_name = process_doi_string(txt_name)
        file_path = './LiteratureSearchWorkDir/{}'.format(txt_name)
        if os.path.exists(file_path):
            Global_Journal.Print(f'File already exists: {txt_name}')
            return f'File already exists: {doi}'
        try:
            with open(file_path, 'wb') as f:
                f.write(bytes_data)
                f.close()
                Global_Journal.Print(f'Successfully downloaded: {txt_name}')
                return 'succeed download {}'.format(doi)
        except Exception as e:
            Global_Journal.Print(f'Error saving file {txt_name}: {str(e)}')
            return f'Error saving file: {doi}'
    else:
        return 'No related paper : {}'.format(doi)
def process_doi_string(input_string):
    pattern = r'(^|_)(10\..+)'
    match = re.search(pattern, input_string)
    if match:
        return match.group(2)
    else:
        return "No valid DOI found"
def download_in_csv(csv_name, keyword, only_high_IF=False, only_second=False, Demo=True, max_papers=100, STDOUT=sys.stdout):
    log_file_name = csv_name.replace(' ', '').replace('/', '')
    with open('./LiteratureSearchWorkDir/{}.log'.format(log_file_name), 'a') as f:
        start = f'start download files! Target: {max_papers} papers'
        f.write(start)
        f.write('\n')
        f.close()
    papers = pd.read_csv(csv_name)
    papers = papers.values
    num = 0
    downloaded_count = 0
    if hasattr(Global_Journal, 'downloaded_papers_count'):
        current_total = Global_Journal.downloaded_papers_count
    else:
        current_total = 0
        Global_Journal.downloaded_papers_count = 0
    target_papers = getattr(Global_Journal, 'max_papers_target', max_papers)
    print(f'Starting download: Current total: {current_total}, Target: {target_papers}')
    for paper in tqdm.tqdm((papers[:Global_Journal.DemoNumber] if Demo else papers), desc='下载文献', file=STDOUT):
        if Global_Journal.downloaded_papers_count >= target_papers:
            print(f'Target paper count ({target_papers}) reached. Stopping download in this CSV.')
            break
        num = num + 1
        Global_Journal.Print(f'Processing paper {num}, Current total downloaded: {Global_Journal.downloaded_papers_count}')
        doi = paper[-1]
        logs = ""
        try:
            logs = download_paper(doi, keyword, only_high_IF, only_second)
            if logs.startswith('succeed download'):
                downloaded_count += 1
                Global_Journal.downloaded_papers_count += 1
                print(f'Successfully downloaded paper {Global_Journal.downloaded_papers_count}/{target_papers}: {doi}')
        except Exception as e:
            logs = f'Error {doi}: {str(e)}'
        finally:
            if len(logs) < 5:
                logs = 'Error {}'.format(doi)
            with open('./LiteratureSearchWorkDir/{}.log'.format(log_file_name), 'a') as f:
                f.write(str(num))
                f.write('\n')
                f.write(logs)
                f.write('\n')
                f.write(f'Total downloaded so far: {Global_Journal.downloaded_papers_count}\n')
                f.close()
    print(f'Completed processing CSV {csv_name}')
    print(f'Downloaded {downloaded_count} papers from this CSV')
    print(f'Total papers downloaded: {Global_Journal.downloaded_papers_count}/{target_papers}')
    with open('./LiteratureSearchWorkDir/{}.log'.format(log_file_name), 'a') as f:
        f.write(f'Completed: Downloaded {downloaded_count} papers from this CSV\n')
        f.write(f'Total downloaded: {Global_Journal.downloaded_papers_count}/{target_papers}\n')
        f.close()
if __name__ == '__main__':
    Key_words = ['spin']
    download_in_csv('./search_results/spin1980_2023RSC.csv', Key_words,
                    only_high_IF=True, only_second=False)
