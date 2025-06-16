import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from queue import Queue, Empty
from threading import Thread, Semaphore
import json
import func_timeout
import tqdm
HEAD='''Based on the attached content below containing multiple review paragraphs focused on the topic of "'''
MIDDLE0='''", evaluate each paragraph on the following dimensions:
1. **Clarity** (10 points): Is the paragraph clearly written and easy to understand?
2. **Depth** (10 points): Does the paragraph delve deep into the topic and offer nuanced insights?
3. **Relevance** (10 points): Is the content of the paragraph directly related to the topic "'''
MIDDLE1='''?
4. **Coherence** (10 points): Does the paragraph maintain a logical flow and coherence in its discussion?
5. **Originality** (10 points): Does the paragraph offer new perspectives or original ideas related to the topic?
6. **Evidence-based** (10 points): Is the content backed by relevant evidence or references?
7. **Structure** (10 points): Is the paragraph well-structured with a clear beginning, middle, and end?
8. **Text Length** (20 points): Does the paragraph maintain an appropriate length? The longer, the better.
9. **DistinctNumberOfDOIs** (20 points): Count the distinct DOIs (format '10\.\d{4,9}[/_]+[-._;()/:A-Za-z0-9]+') in each paragraph and compare. Assign a relative score based on the number of unique references compared to other paragraphs; the paragraph with the most unique references gets the highest score.
10. **Comprehensiveness** (10 points): Does the paragraph cover all pertinent aspects related to the topic in a comprehensive manner?
11. **Relatedness** (20 points): Does the paragraph exhibit thematic consistency with other paragraphs when discussing similar or identical DOI references? Is the paragraph’s explanation and context concerning a specific DOI analogous to that in other paragraphs that cite the same DOI?
Regarding the new **Relatedness** criterion:
- Analyze the paragraphs that share common DOI references, assessing the degree of similarity in the contextual use and discussion surrounding those references.  
- Evaluate whether the paragraph aligns with or diverges from the shared thematic discussions related to the DOI in question when compared to other paragraphs that cite the same DOI.
- Ensure that the relatedness is not merely surface-level or lexical but digs deeper into the thematic and contextual consistency across different paragraphs that cite the same DOI.
Using these criteria, evaluate each paragraph methodically, ensuring that each dimension is assessed with rigor and impartiality. Subsequently, the paragraph that amasses the highest cumulative score across all dimensions should be selected as the one that most effectively addresses the topic at hand, while also maintaining cohesion, depth, and thematic alignment with related discussions in different paragraphs. Remember to be meticulous and transparent in the scoring to ensure that the selection is justifiable and replicable.
<file-attachment-contents filename="Paragraphs.txt"> 
<Paragraphs>
'''
END="""
</Paragraphs>
</file-attachment-contents>
After evaluating all the paragraphs for each dimension, all the information is stored in a dictionary in the JSON format as shown below. Remember that "scores" is a list containing the score details of each paragraph and "best_paragraph_ID" is a string containing the best paragraph ID. Only output the JSON result, don't output anything else.
For example:
{
    "scores": [
        {
            "paragraph_id": "1",
            "clarity": 8,
            "depth": 7,
            "relevance": 9,
            "coherence": 7,
            "originality": 6,
            "evidence_based": 8,
            "structure": 9,
            "text_length": 16,
            "distinct_number_of_dois": 18,
            "comprehensiveness": 8,
            "total_score": 88
        }
    ],
    "best_paragraph_ID": "-1"
}
"""
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
    progress_bar = tqdm.tqdm(total=len(prompts), position=0, desc='选择最优段落',file=STDOUT)
    def worker():
        while True:
            try:
                i, folder, part, prompt = prompt_queue.get_nowait()
            except Empty:
                break
            if os.path.exists(os.path.join(f'Paragraph', f'Best{part}.txt')):
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
                    if (not (re.search(r'"scores"\s*:\s*\[\s*\{\s*"paragraph_id"', response))
                           or ('total_score'not in response)
                           or ('best_paragraph_ID'not in response)):
                        open(os.path.join(f'Paragraph', f'Best{part}_{TRY}.txt'),'w',encoding='UTF8').write(response+'\n')
                        TRY+=1
                        continue
                    try:
                        json_content = '{' + response.split('{',1)[-1].rsplit('}',1)[0] + '}'
                        try:
                            data = json.loads(json_content)
                        except json.JSONDecodeError:
                            data = json.loads(json_content[:-1])
                        total_scores = []
                        if 'scores' in data and isinstance(data['scores'], list) and 'best_paragraph_ID' in data and (isinstance(data['best_paragraph_ID'], str) or isinstance(data['best_paragraph_ID'], int)):
                            for paragraph in data['scores']:
                                if 'total_score' in paragraph:
                                    total_scores.append(int(paragraph['total_score']))
                            total_scores.append(int(data['best_paragraph_ID']))
                        if not total_scores:
                            raise ValueError("No valid total_scores found")
                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        open(os.path.join(f'Paragraph', f'Best{part}_{TRY}.txt'),'w',encoding='UTF8').write(response+'\n')
                        TRY+=1
                        continue
                    with open(os.path.join(f'Paragraph', f'Best{part}.txt'), 'w', encoding='UTF8') as file:
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
def extract_sections_with_tags(content):
    content='{'+content.split('{',1)[-1].rsplit('}',1)[0]+'}'
    content=json.loads(content)
    content_matches=content['Content']
    reference_matches=content['References']
    return content_matches,'\n'.join(reference_matches)
def Main(Folder,Threads,FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    ParagraphQuestionsForReview=[i.strip() for i in open('../ParagraphQuestionsForReview.txt','r',encoding='UTF8').readlines() if i.strip()]
    prompts = []
    filtered_files = [file for file in os.listdir('Paragraph') if re.match( r"Paragraph(\d+)_(\d+)\.txt", file)]
    filtered_files.sort()
    file_dict = {}
    for file in filtered_files:
        match = re.match(r"Paragraph(\d+)_(\d+)\.txt", file)
        i = int(match.group(1))
        if i not in file_dict:
            file_dict[i] = []
        file_dict[i].append(file)
    for key in file_dict:
        file_dict[key].sort()
    file_dict={k:v for k,v in file_dict.items()}
    for i in sorted(file_dict.keys()):
        merged_content=[]
        for file_name in file_dict[i]:
            with open(os.path.join('Paragraph', file_name), 'r',encoding='UTF8') as file:
                content_matches, reference_matches=extract_sections_with_tags(file.read())
                merged_content.append(f'    <Paragraph id="{file_name.split("_")[1].split(".")[0]}">\n'+content_matches.strip()+'\n<References>\n'+reference_matches.strip()+'\n</References>\n</Paragraph>')
        prompt = replace_with_html_entities(HEAD + ParagraphQuestionsForReview[i-1] + MIDDLE0 + ParagraphQuestionsForReview[i-1] + MIDDLE1) +'\n'.join(merged_content)+END
        open(f'Paragraph{os.sep}PromptBest{i}.txt', 'w', encoding='UTF8').write(prompt)
        prompts.append((i, f"{i}", f"Paragraph{i}", prompt))
    GetResponseConcurrent(prompts,Threads,FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT)
    os.chdir('..')
    sys.stdout = old_stdout
