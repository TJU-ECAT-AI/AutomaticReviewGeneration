from threading import Thread, Semaphore
from queue import Queue, Empty
import time
import re
import os
import sys
import tqdm
import shutil
import func_timeout
def GetResponse(PromptList, PromptDir, Threads, FunctionClaudeAPI, FunctionOpenAIAPI, STDOUT):
    results = [None] * len(PromptList)
    prompt_queue = Queue()
    ClaudeAPISemaphore = []
    OpenAIAPISemaphore = []
    FunctionClaudeAPI = {k: v for k, v in FunctionClaudeAPI.items() if v}
    FunctionOpenAIAPI = {k: v for k, v in FunctionOpenAIAPI.items() if v}
    for i in FunctionClaudeAPI:
        ClaudeAPISemaphore.append(Semaphore(value=1))
    for i in FunctionOpenAIAPI:
        OpenAIAPISemaphore.append(Semaphore(value=3))
    Repeat = 5
    progress_bar = tqdm.tqdm(total=len(PromptList) * Repeat, position=0, desc='信息提取', file=STDOUT)
    for i, PromptFile in enumerate(PromptList):
        Name = PromptFile.split('.txt')[0].strip('Prompt')
        PART = PromptFile.split(".txt")[-1]
        prompt_queue.put((i, Name,
                          PART,
                          PromptFile,
                          open(f'{PromptDir}{os.sep}{PromptFile}', encoding='UTF-8').read()))
    def worker():
        while True:
            try:
                i, name, part, PromptFile, prompt = prompt_queue.get_nowait()
            except Empty:
                break
            open('log', 'a').write(
                '\t'.join([str(i), name, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()), 'start\n']))
            if not os.path.exists(f'{name}{os.sep}{part[1:]}Finished'):
                os.makedirs(name, exist_ok=True)
                shutil.copy(f'{PromptDir}{os.sep}{PromptFile}',
                            f'{name}{os.sep}question{part}.txt')
                PASS = 0
                for Time in range(Repeat):
                    TRY = 0
                    while True:
                        semaphore_acquired = None
                        response = None
                        try:
                            for semaphore, GetResponseFunction in zip(ClaudeAPISemaphore, FunctionClaudeAPI.values()):
                                if semaphore.acquire(blocking=False):
                                    semaphore_acquired = semaphore
                                    response = GetResponseFunction(prompt)
                                    semaphore.release()
                                    break
                            if not response:
                                for semaphore, GetResponseFunction in zip(OpenAIAPISemaphore,
                                                                          FunctionOpenAIAPI.values()):
                                    if semaphore.acquire(blocking=False):
                                        semaphore_acquired = semaphore
                                        response = GetResponseFunction(prompt)
                                        semaphore.release()
                                        break
                            if not response:
                                open('Waitlog', 'a').write('\t'.join(
                                    [str(i), name, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()),
                                     'waiting\n']))
                                time.sleep(0.5)
                                continue
                            with open(f'{name}{os.sep}answer{part}_{Time}.txt', 'w', encoding='UTF-8') as file:
                                file.write(response + '\n')
                            results[i] = response
                            PASS += 1
                            break
                        except (Exception, func_timeout.exceptions.FunctionTimedOut) as e:
                            pattern = r"Function\s+(\S+).*?timed out after\s+(\d+\.\d+)\s+seconds."
                            replacement = r"\1 timed out after \2 s"
                            if semaphore_acquired:
                                semaphore_acquired.release()
                            open('Exceptionlog', 'a').write(
                                '\t'.join([str(i), name, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()),
                                           re.sub(pattern, replacement, str(e), flags=re.DOTALL), '\n']))
                            TRY += 1
                            continue
                    progress_bar.update(1)
                if PASS == Repeat:
                    with open(f'{name}{os.sep}{part[1:]}Finished', 'w', encoding='UTF-8') as file:
                        file.write('\n')
            else:
                progress_bar.update(Repeat)
            open('log', 'a').write(
                '\t'.join([str(i), name, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()), 'end\n']))
    threads = [Thread(target=worker) for _ in range(Threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    progress_bar.close()
    return results
def Main(Folder, Threads, FunctionClaudeAPI, FunctionOpenAIAPI, STDOUT):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    PromptDir = 'Prompt'
    PromptList = os.listdir(PromptDir)
    file_size_dict = {f: -(os.path.getsize(f'{PromptDir}{os.sep}{f}')) for f in PromptList}
    PromptList = sorted(PromptList, key=lambda x: file_size_dict[x])
    responses = GetResponse(PromptList, PromptDir, Threads, FunctionClaudeAPI, FunctionOpenAIAPI, STDOUT)
    os.chdir('..')
    sys.stdout = old_stdout
