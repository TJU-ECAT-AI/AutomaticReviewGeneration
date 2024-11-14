import multiprocessing
import os.path
import queue
import signal
import csv
from multiprocessing import Process, Queue, Value
import time
import os
import time
from .Advanced_Download import download_paper
from multiprocessing import Pool
import pandas as pd
import csv
import csv
import multiprocessing
import time
from multiprocessing import Process, Queue
import threading
from multiprocessing import Process, Queue
import time
import pandas as pd
import multiprocessing
import time
from queue import Empty
import csv
from multiprocessing import Process, Queue, current_process
from multiprocessing import queues
import signal
from time import sleep
import os
from multiprocessing import Pool, Queue, Manager
import csv
import time
lock = threading.Lock()
def doi_DownloadAdvance(doi, key_words, only_high_IF=False, only_second=False):
    """
    处理传递给它的行的函数。
    参数rows是一个包含CSV文件中行的列表。
    """
    download_list = []
    if os.path.exists('./already_download.csv'):
        download_lists = pd.read_csv('./already_download.csv', header=None)
        for already in download_lists.values:
            download_list.append(already[-1])
        if doi in download_list:
            lock.acquire()
            try:
                print('{} already downloaded'.format(doi))
                logs = 'already_download'
            finally:
                lock.release()
        else:
            logs = download_paper(doi, key_words, only_high_IF, only_second)
    else:
        logs = download_paper(doi, key_words, only_high_IF, only_second)
    return logs
def Stable_doi_DownloadAdvance(doi, key_words, only_high_IF, only_second):
    key_words = key_words
    only_high_IF = only_high_IF
    only_second = only_second
    print('Advanced : {}'.format(key_words))
    print('only_high_IF : {}'.format(only_high_IF))
    print('only_second : {}'.format(only_second))
    try:
        print('doi', doi)
        logs = doi_DownloadAdvance(doi, key_words, only_high_IF, only_second)
        if 'succeed' in logs:
            lock.acquire()
            try:
                with open('./already_download.csv', 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([doi])
            finally:
                lock.release()
        elif 'already_download' in logs:
            print('already download {}'.format(doi))
        else:
            logs = logs
    finally:
        try:
            if len(logs) < 5:
                logs = 'Error {}'.format(doi)
        except UnboundLocalError:
            logs = 'Error {}'.format(doi)
        finally:
            pass
def monitor_process(process, max_time):
    start_time = time.time()
    while process.is_alive():
        current_time = time.time()
        if current_time - start_time > max_time:
            process.terminate()
            print(f"Process terminated due to timeout of {max_time} seconds.")
            break
        time.sleep(0.1)
def worker(queue, max_time, screen_word, only_high_IF, only_second):
    while True:
        param = queue.get()
        if param is None:
            break
        process = Process(target=Stable_doi_DownloadAdvance, args=(param, screen_word, only_high_IF, only_second))
        process.start()
        monitor = threading.Thread(target=monitor_process, args=(process, max_time))
        monitor.start()
        process.join()
        monitor.join()
def run_functions(max_run, csv_path, screen_word, only_high_IF,only_second,max_time=500):
    print("Starting Multi_download {} processes".format(max_run))
    queue = Queue(maxsize=max_run)
    processes = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for i, row in enumerate(reader):
            if i < max_run:
                queue.put(row[-1])
            else:
                break
    for _ in range(max_run):
        p = Process(target=worker, args=(queue, max_time, screen_word, only_high_IF, only_second))
        processes.append(p)
        p.start()
    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for i, row in enumerate(reader):
            if i >= max_run:
                queue.put(row[-1])
    for _ in range(max_run):
        queue.put(None)
    for p in processes:
        p.join()
    print("All processes finished.")
if __name__ == '__main__':
    run_functions(5, 'search_results/propanedehydrogenation2020_2024ACS_high_IF.csv', ['cat', 'fish'],500)
