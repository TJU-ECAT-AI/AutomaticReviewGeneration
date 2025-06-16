import json
import os
import re
import sys
import time
import json
from queue import Queue, Empty
from threading import Thread, Semaphore
import func_timeout
import tqdm
def replace_with_html_entities(text):
    entities = {
        '[':'\[',
        ']':'\]',
        '_':'\_',
        '&': '&amp;',
        '©': '&copy;',
        '®': '&reg;',
        '™': '&trade;',
        '€': '&euro;',
        '£': '&pound;',
        '¥': '&yen;',
        '¢': '&cent;',
        '—': '&mdash;',
        '–': '&ndash;',
        '•': '&bull;',
        '…': '&hellip;'
    }
    for char, entity in entities.items():
        text = text.replace(char, entity)
    return text
def wrap_specific_tags_with_cdata(tag_name, content):
    tag_pattern = f'<{tag_name}>(.*?)</{tag_name}>'
    replacement = f'<{tag_name}><![CDATA[\\1]]></{tag_name}>'
    return re.sub(tag_pattern, replacement, content, flags=re.DOTALL)
def GetResponseConcurrent(prompts,Threads,FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT):
    prompt_queue = Queue()
    for item in prompts:
        prompt_queue.put(item)
    ClaudeAPISemaphore=[]
    OpenAIAPISemaphore=[]
    FunctionClaudeAPI={k:v for k,v in FunctionClaudeAPI.items() if v}
    FunctionOpenAIAPI={k:v for k,v in FunctionOpenAIAPI.items() if v}
    for i in FunctionClaudeAPI:
        ClaudeAPISemaphore.append(Semaphore(value=1))
    for i in FunctionOpenAIAPI:
        OpenAIAPISemaphore.append(Semaphore(value=3))
    progress_bar = tqdm.tqdm(total=len(prompts), position=0, desc='综述撰写',file=STDOUT)
    def worker():
        while True:
            try:
                i, Time,folder, part, prompt,DOI = prompt_queue.get_nowait()
            except Empty:
                break
            if os.path.exists(os.path.join(f'Paragraph{"All" if "All" in part else ""}', f'{part}_{Time}.txt')):
                progress_bar.update(1)
                continue
            TRY = 0
            while True:
                semaphore_acquired = None
                response=None
                try:
                    for semaphore,GetResponseFunction in zip(ClaudeAPISemaphore,FunctionClaudeAPI.values()):
                        if semaphore.acquire(blocking=False):
                            semaphore_acquired = semaphore
                            response = GetResponseFunction(prompt)
                            semaphore.release()
                            break
                    if not response:
                        for semaphore,GetResponseFunction in zip(OpenAIAPISemaphore,FunctionOpenAIAPI.values()):
                            if semaphore.acquire(blocking=False):
                                semaphore_acquired = semaphore
                                response = GetResponseFunction(prompt)
                                semaphore.release()
                                break
                    if not response:
                        open('Waitlog', 'a').write('\t'.join([str(i), folder, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()), 'waiting\n']))
                        time.sleep(0.5)
                        continue
                    if not bool(re.search(r'\[\s*10\.\d+[/_]+[-._;()/:A-Za-z0-9]+', response)):
                        TRY+=1
                        with open(os.path.join(f'Paragraph{"All" if "All" in part else ""}', f'{part}_{Time}_{TRY}.txt'), 'w', encoding='UTF8') as file:
                            file.write(response + '\n')
                        continue
                    try:
                        json_content = '{' + response.split('{',1)[-1].rsplit('}',1)[0] + '}'
                        content_dict = json.loads(json_content)
                        required_fields = ["Content", "References"]
                        for field in required_fields:
                            if field not in content_dict:
                                raise RuntimeError(f"Missing required field: {field}")
                        WrongDOI=[]
                        references = content_dict.get("References", [])
                        if isinstance(references, str):
                            DOIFromResponse = [doi.strip() for doi in references.split('\n') if doi.strip()]
                        elif isinstance(references, list):
                            DOIFromResponse = [str(doi).strip() for doi in references if str(doi).strip()]
                        else:
                            raise RuntimeError("References field must be string or list")
                        WrongDOI=[doi for doi in DOIFromResponse if doi not in DOI]
                        if WrongDOI:
                            raise RuntimeError('WrongDOI')
                    except (json.JSONDecodeError, ValueError, RuntimeError) as e:
                        TRY+=1
                        with open(os.path.join(f'Paragraph{"All" if "All" in part else ""}', f'{part}_{Time}_{TRY}.txt'), 'w', encoding='UTF8') as file:
                            file.write(f'\nJSON Error: {str(e)}\n\n\n'+response)
                        continue
                    with open(os.path.join(f'Paragraph{"All" if "All" in part else ""}', f'{part}_{Time}.txt'), 'w', encoding='UTF8') as file:
                        file.write(response + '\n')
                    break
                except (Exception,func_timeout.exceptions.FunctionTimedOut) as e:
                    pattern = r"Function\s+(\S+).*?timed out after\s+(\d+\.\d+)\s+seconds."
                    replacement = r"\1 timed out after \2 s"
                    if semaphore_acquired:
                        semaphore_acquired.release()
                    open('Exceptionlog', 'a').write('\t'.join([str(i), folder, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()),
                                                               re.sub(pattern, replacement, str(e), flags=re.DOTALL),'\n']))
                    continue
            progress_bar.update(1)
    threads = [Thread(target=worker) for _ in range(Threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    progress_bar.close()
def Main(Folder,TOPIC,Threads,FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT,REPEAT=9):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    ParagraphQuestionsForReview=[i.strip() for i in open('../ParagraphQuestionsForReview.txt','r',encoding='UTF8').readlines() if i.strip()]
    QuestionsForReview=[i.strip() for i in open('../QuestionsForReview.txt','r',encoding='UTF8').readlines() if i.strip()]
    NumberOfParts=len(QuestionsForReview)
    HEAD="""Based on the in-depth details extracted from the file related to '"""
    MIDDLE0=f"""', construct an analytical and comprehensive review section on {TOPIC}, emphasizing '"""
    MIDDLE1="""'.
    While developing the content, adhere to the following protocols:
    1. **Accurate Citations**: When referencing content from files, ALWAYS include the exact DOI number found in the source material immediately after the relevant sentence using the format '[actual DOI number]'. CRITICAL: Use only real DOI numbers from the documents without any alterations - never use placeholder text, generic formats, or made-up DOIs.
    2. **Strict Adherence**: Stick to the particulars and DOI details from the file; avoid integrating external or speculative data.
    3. **Scientific Language**: Uphold a technical and scholarly diction akin to chemical engineering literature.
    4. **Format**: After creating the main review content, append an 'integrative understanding and prospective outlook' section within the "Content" field. This segment should transcend a mere summation and foster a forward-thinking discussion, potentially elucidating future directions and broader horizons grounded in the file's content.
    5. **Length**: Note that the total length of the output should be controlled within 8k Tokens.
    The content structure should be in JSON format and resemble:
    {
        "Content": "Detailed analysis established from the study of reference [Placeholder_Of_DOI]. Synthesized comprehension stemming from references [Placeholder_Of_DOI] and [Placeholder_Of_DOI]. Integrative understanding and prospective outlook: Taking into consideration the advancements and findings discussed in the file, there lies an opportunity to explore emerging fields and innovative methodologies. Future research endeavors might focus on ...",
        "References": [
            "Placeholder_Of_DOI",
            "Placeholder_Of_DOI", 
            "Placeholder_Of_DOI"
        ]
    }
    In the 'integrative understanding and prospective outlook' segment, aspire to:
    - **Offer an expansive perspective**: Illuminate potential pathways and pioneering research opportunities, grounded in the details divulged in the file.
    - **Propose forward-thinking suggestions**: Advocate for innovative angles and burgeoning domains that might take center stage in future explorations, while rooted in the file's details.
    Finally, compile all the cited DOIs in the 'References' field as an array, using the exact DOIs designated in the file.
    <file-attachment-contents filename="""
    END="""
    </file-attachment-contents>
    Keep in mind all the previous requirements, especially the requirement to use accurate DOI references. Note that Placeholder_Of_DOI in the content is strictly prohibited and should be replaced with the actual DOI of the provided material. Now, start the task.
    """
    prompts = []
    os.makedirs('Paragraph',exist_ok=True)
    for Time in range(0,REPEAT):
        for i in range(NumberOfParts):
            if os.path.exists(f'{i+1}') :
                document = open(f'{i+1}/EnglishWithQuotes.txt', 'r', encoding='UTF8').read().strip()[:-1]
                DOI=[j['Doi'] for j in json.loads('['+document+']')]
                prompt = (HEAD + QuestionsForReview[i] + MIDDLE0 + ParagraphQuestionsForReview[i] + MIDDLE1 + f'"Paragraph{i+1}Info.txt">\n') + document + END
                open(f'Paragraph{os.sep}Prompt{i+1}.txt', 'w', encoding='UTF8').write(prompt)
                prompts.append((i,Time, f"{i+1}", f"Paragraph{i+1}", prompt,DOI))
    GetResponseConcurrent(prompts,Threads,FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT)
    os.chdir('..')
    sys.stdout = old_stdout
