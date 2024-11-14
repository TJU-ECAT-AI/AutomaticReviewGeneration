import os
import re
import sys
import time
import tqdm
import json
import openai
import tiktoken
import func_timeout
import xml.etree.ElementTree as ET
from threading import Thread, Semaphore
from multiprocessing import Pool
from queue import Queue, Empty
URL=''
KEY=''
MODEL=''
max_tokens=524288
@func_timeout.func_set_timeout(400)
def GetResponseFromClaude(Prompt,api_key):
    anthropic = Anthropic(api_key=api_key,max_retries=0,
                          timeout=httpx.Timeout(400,read=320, write=30, connect=19))
    message = anthropic.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4096,
        messages=[{"role": "user",
                   "content": Prompt,}])
    return message.content[0].text
@func_timeout.func_set_timeout(3600)
def GetResponseFromClaudeViaWebAgent(Prompt,url=URL,key=KEY,model=MODEL):
    client = openai.OpenAI(api_key=key,base_url=url)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": 'You are a helpful assistant. You are good at summarizing and will not repeat the same sentence.'},
                  {"role": "user", "content":Prompt}]
        )
    return completion.choices[0].message.content
def GetResponseFromClaudeViaWebAgentExample(prompt,url,key):
    time.sleep(1)
    return f'GetResponseFromClaudeViaWebAgent {prompt}\t{url}\t{key}'
def GetResponseConcurrent(prompts, Threads, STDOUT):
    prompt_queue = Queue()
    for item in prompts:
        prompt_queue.put(item)
    semaphore1 = Semaphore(value=0)
    semaphore2 = Semaphore(value=16)
    progress_bar = tqdm.tqdm(total=len(prompts), position=0, desc='DirectGeneration', file=STDOUT)
    def worker():
        while True:
            try:
                i, prompt = prompt_queue.get_nowait()
            except Empty:
                break
            if os.path.exists(f'DirectGeneration{i+1}.txt'):
                progress_bar.update(1)
                continue
            TRY = 0
            while True:
                semaphore_acquired = None
                response = None
                try:
                    if semaphore2.acquire(blocking=False):
                        semaphore_acquired = semaphore2
                        response = GetResponseFromClaudeViaWebAgent(prompt)
                        semaphore2.release()
                    else:
                        open('Waitlog', 'a').write('\t'.join([str(i), folder, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()), 'waiting\n']))
                        time.sleep(0.5)
                        continue
                    with open(f'DirectGeneration{i+1}.txt', 'w', encoding='UTF8') as file:
                        file.write(response + '\n')
                    break
                except (Exception, func_timeout.exceptions.FunctionTimedOut) as e:
                    pattern = r"Function\s+(\S+).*?timed out after\s+(\d+\.\d+)\s+seconds."
                    replacement = r"\1 timed out after \2 s"
                    if semaphore_acquired:
                        semaphore_acquired.release()
                    open('Exceptionlog', 'a').write('\t'.join([str(i), time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()),
                                                               re.sub(pattern, replacement, str(e), flags=re.DOTALL), '\n']))
                    continue
            progress_bar.update(1)
    threads = [Thread(target=worker) for _ in range(Threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    progress_bar.close()
def Main(Folder, Threads,STDOUT):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    prompts = []    
    os.chdir(Folder)
    os.makedirs('DirectGeneration',exist_ok=True)
    os.chdir('DirectGeneration')
    ParagraphQuestionsForReview = [i.strip() for i in open('../ParagraphQuestionsForReview', 'r', encoding='UTF8').readlines() if i.strip()]
    HEAD = """Write a paragraph around the following topic:\n"""
    for i in range(len(ParagraphQuestionsForReview)):
                prompt =HEAD  + ParagraphQuestionsForReview[i].strip()+'\n'
                open(f'PromptDirectGeneration{i+1}.txt', 'w', encoding='UTF8').write(prompt)
                prompts.append((i, prompt))
    GetResponseConcurrent(prompts, Threads, STDOUT)
    os.chdir('..')
    sys.stdout = old_stdout
if __name__ == "__main__":
    Main(Folder='.',Threads=16, STDOUT=sys.stdout)
