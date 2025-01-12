import re
import os
import sys
import openai
import time
import tqdm
import shutil
import func_timeout
from threading import Thread, Semaphore
from queue import Queue, Empty
import xml.etree.ElementTree as ET
URL=''
KEY=''
MODEL=''
max_tokens=32768
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
def GetResponseFromOpenAlClient(Prompt,url=URL,key=KEY,model=MODEL):
    client = openai.OpenAI(api_key=key,base_url=url)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": 'You are a helpful assistant. You are good at summarizing and will not repeat the same sentence. The quotes must be strictly relevant to the target answer. Be intelligent.'},
                  {"role": "user", "content":Prompt}]
        )
    return completion.choices[0].message.content
def GetResponseFromClaudeViaWebAgentExample(prompt,url,key):
    time.sleep(1)
    return f'GetResponseFromClaudeViaWebAgent {prompt}\t{url}\t{key}'
def wrap_specific_tags_with_cdata(tag_name, content):
    tag_pattern = f'<{tag_name}>(.*?)</{tag_name}>'
    replacement = f'<{tag_name}><![CDATA[\\1]]></{tag_name}>'
    return re.sub(tag_pattern, replacement, content, flags=re.DOTALL)
def GetResponse(PromptList, PromptDir, Threads, STDOUT):
    results = [None] * len(PromptList)
    prompt_queue = Queue()
    Repeat = 5
    progress_bar = tqdm.tqdm(total=len(PromptList)*Repeat, position=0, desc='GetResponse', file=STDOUT)
    for i, PromptFile in enumerate(PromptList):
        Name = PromptFile.split('.txt')[0].strip('Prompt')
        PART = PromptFile.split(".txt")[-1]
        prompt_queue.put((i, Name,
                          PART,
                          PromptFile,
                          open(f'{PromptDir}{os.sep}{PromptFile}', encoding='UTF-8').read()))
    semaphore1 = Semaphore(value=0)
    semaphore2 = Semaphore(value=16)
    def worker():
        while True:
            try:
                i, name, part, PromptFile, prompt = prompt_queue.get_nowait()
            except Empty:
                break
            open('log', 'a').write('\t'.join([str(i), name, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()), 'start\n']))
            if not os.path.exists(f'{name}{os.sep}{part[1:]}Finished'):
                os.makedirs(name, exist_ok=True)
                shutil.copy(f'{PromptDir}{os.sep}{PromptFile}',
                            f'{name}{os.sep}question{part}.txt')
                PASS = 0
                for Time in range(Repeat):
                    try_num = 0
                    while try_num<100:
                        semaphore_acquired = None
                        response = None
                        try:
                            if semaphore2.acquire(blocking=False):
                                semaphore_acquired = semaphore2
                                response = GetResponseFromClaudeViaWebAgent(prompt)
                                semaphore2.release()
                            else:
                                open('Waitlog', 'a').write('\t'.join([name, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()), 'waiting\n']))
                                time.sleep(0.5)
                                continue
                            try:
                                if ('<quotes>' not in response )or ('<ChineseVersionAnswer>' not in response ):
                                    raise RuntimeError('Error Response')
                                content='<?xml version="1.0" encoding="UTF-8"?>\n<Answer>\n<quotes>\n'+response.strip().split('<quotes>')[-1]
                                content=content.split('</ChineseVersionAnswer>')[0]+'\n</ChineseVersionAnswer>\n</Answer>'
                                tags_to_wrap = ["quotes", "EnglishVersionAnswer", "ChineseVersionAnswer"]
                                for tag in tags_to_wrap:
                                    content = wrap_specific_tags_with_cdata(tag, content.strip())
                                root = ET.fromstring(content)
                            except:
                                with open(os.path.join(name, f'answer{part}_{Time}-{try_num}.txt'), 'w', encoding='UTF8') as file:
                                    file.write(response + '\n')
                                try_num += 1
                                continue
                            with open(os.path.join(name, f'answer{part}_{Time}.txt'), 'w', encoding='UTF8') as file:
                                file.write(response + '\n')
                            results[i] = response
                            PASS += 1
                            break
                        except (Exception, func_timeout.exceptions.FunctionTimedOut) as e:
                            if semaphore_acquired:
                                semaphore_acquired.release()
                            open('Exceptionlog', 'a').write('\t'.join([name, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()), str(e), '\n']))
                            continue
                    progress_bar.update(1)
                if PASS == Repeat:
                    with open(f'{name}{os.sep}{part[1:]}Finished', 'w', encoding='UTF-8') as file:
                        file.write('\n')
            else:
                progress_bar.update(Repeat)
            open('log', 'a').write('\t'.join([str(i), name, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()), 'end\n']))
    threads = [Thread(target=worker) for _ in range(Threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    progress_bar.close()
    return results
def Main(Folder, Threads, STDOUT):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    PromptDir = 'Prompt'
    PromptList = os.listdir(PromptDir)
    file_size_dict = {f: -(os.path.getsize(f'{PromptDir}{os.sep}{f}')) for f in PromptList}
    PromptList = sorted(PromptList, key=lambda x: file_size_dict[x])
    responses = GetResponse(PromptList, PromptDir, Threads, STDOUT)
    os.chdir('..')
    sys.stdout = old_stdout
if __name__ == "__main__":
    Main('.',16,sys.stdout)
