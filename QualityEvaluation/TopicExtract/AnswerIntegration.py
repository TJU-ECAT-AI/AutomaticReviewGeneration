from GetResponse import *
import re
import os
import tqdm
from queue import Queue, Empty
from threading import Thread, Semaphore
import xml.etree.ElementTree as ET
from io import StringIO
import time
import json
import shutil
import requests
URL=''
KEY=''
MODEL=''
HEAD='''# Integration of Multiple Topic Extractions and Questions
You are an expert in academic writing, text analysis, and information synthesis. Your task is to integrate multiple topic extractions and generated questions from the same document into a cohesive and comprehensive summary. Follow these steps carefully:
1. Review all provided topic extractions and generated questions.
2. Identify common themes, key concepts, and overlapping ideas across all inputs.
3. Synthesize this information into a unified topic and comprehensive question.
4. Ensure the final output reflects a deep understanding of the entire document, not just individual sections.
Use the following XML template for your output, integrating all relevant information into a single, cohesive entry:
```xml
<integrated_analysis>
  <synthesized_topic_extraction>
    <common_themes>
      [List the common themes identified across all inputs]
    </common_themes>
    <key_concepts>
      [Enumerate the key concepts that appear consistently across inputs]
    </key_concepts>
    <integration_process>
      [Explain your process of synthesizing the various topics and ideas]
    </integration_process>
    <final_extracted_topic>
      [Present the final, synthesized topic that encompasses all inputs]
    </final_extracted_topic>
  </synthesized_topic_extraction>
  <synthesized_question_generation>
    <question_integration_approach>
      [Describe how you're combining and refining the individual questions]
    </question_integration_approach>
    <final_generated_question>
      <english>[Present the final, comprehensive question in English that covers all aspects of the synthesized topic]</english>
      <chinese>[Present the Chinese translation of the final generated question]</chinese>
    </final_generated_question>
  </synthesized_question_generation>
</integrated_analysis>
```
Remember to:
- Focus on creating a cohesive narrative that captures the essence of all inputs.
- Avoid simply listing or concatenating individual items.
- Ensure the final topic and question are broad enough to encompass all key points from the inputs, yet specific enough to guide a focused discussion.
- Use academic language appropriate for the field of study.
- Provide both English and Chinese versions of the final generated question.
<file-attachment-contents filename="Analysis.txt"> 
<Analysis>
'''
END="""
</Analysis>
</file-attachment-contents>
"""
Folders=[i for i in os.listdir('.') if i.startswith('10.')]
Folders.sort()
def wrap_specific_tags_with_cdata(tag_name, content):
    tag_pattern = f'<{tag_name}>(.*?)</{tag_name}>'
    replacement = f'<{tag_name}><![CDATA[\\1]]></{tag_name}>'
    return re.sub(tag_pattern, replacement, content, flags=re.DOTALL)
def GetResponseConcurrent(prompts):
    prompt_queue = Queue()
    for folder, prompt in prompts:
        prompt_queue.put((folder, prompt))
    semaphore1 = Semaphore(value=0)
    semaphore2 = Semaphore(value=32)
    progress_bar = tqdm.tqdm(total=len(prompts), position=0, leave=True)
    def worker():
        while True:
            try:
                folder, prompt = prompt_queue.get_nowait()
            except Empty:
                break
            try_num = 0
            while True:
                semaphore_acquired = None
                try:
                    if semaphore1.acquire(blocking=False):
                        semaphore_acquired = semaphore1
                        response = GetResponseFromClaude(prompt,KEY)
                        semaphore1.release()
                    elif semaphore2.acquire(blocking=False):
                        semaphore_acquired = semaphore2
                        response = GetResponseFromOpenAlClient(prompt,URL,KEY,MODEL)
                        semaphore2.release()
                    else:
                        open('Waitlog','a').write('\t'.join([folder,time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime()),'waiting\n']))
                        time.sleep(0.5)
                        continue
                    try:
                        if ('<integrated_analysis>' not in response )or ('<final_extracted_topic>' not in response )or ('<final_generated_question>' not in response):
                            raise RuntimeError('Error Response')
                        content='<?xml version="1.0" encoding="UTF-8"?>\n<integrated_analysis>\n'+response.strip().split('<integrated_analysis>')[-1]
                        content=content.split('</integrated_analysis>')[0]+'\n</integrated_analysis>'
                        tags_to_wrap=['common_themes','key_concepts',
                                      'integration_process','final_extracted_topic',
                                      'question_integration_approach','english','chinese']
                        for tag in tags_to_wrap:
                            content = wrap_specific_tags_with_cdata(tag, content.strip())
                        root = ET.fromstring(content)
                    except:
                        with open(os.path.join(folder, f'ParagraphTopicExtract-{try_num}.txt'), 'w', encoding='UTF8') as file:
                            file.write(response + '\n')
                        try_num += 1
                        continue
                    with open(os.path.join(folder, f'ParagraphTopicExtract.txt'), 'w', encoding='UTF8') as file:
                        file.write(response.replace('>Not mentioned<','>N/A<') + '\n')
                    break
                except Exception as e:
                    if semaphore_acquired:
                        semaphore_acquired.release()
                    open('Exceptionlog','a').write('\t'.join([folder,time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime()),str(e),'\n']))
                    continue
            progress_bar.update(1)
    threads = [Thread(target=worker) for _ in range(32)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    progress_bar.close()
def remove_original_paragraphs(response):
    content='<?xml version="1.0" encoding="UTF-8"?>\n<analysis>\n'+response.strip().split('<analysis>')[-1]
    content=content.split('</analysis>')[0]+'\n</analysis>'
    tags_to_wrap=['original_paragraph','step1_initial_thoughts',
                  'step2_key_concepts','step3_topic_formulation',
                  'extracted_topic','step1_question_formulation',
                  'english','chinese']
    for tag in tags_to_wrap:
        content = wrap_specific_tags_with_cdata(tag, content.strip())
    tree = ET.ElementTree(ET.fromstring(content))
    root = tree.getroot()
    for parent in root.iter():
        for child in list(parent):
            if child.tag == 'original_paragraph':
                parent.remove(child)
    output = StringIO()
    tree.write(output, encoding='unicode', xml_declaration=False)
    result = output.getvalue()
    result = re.sub(r'^\s*<analysis>\s*', '', result)
    result = re.sub(r'\s*</analysis>\s*$', '', result)
    return result.strip()
def GetFinalResult(response):
    content='<?xml version="1.0" encoding="UTF-8"?>\n<analysis>\n'+response.strip().split('<analysis>')[-1]
    content=content.split('</analysis>')[0]+'\n</analysis>'
    tags_to_wrap=['common_themes','key_concepts',
                                      'integration_process','final_extracted_topic',
                                      'question_integration_approach','english','chinese']
    for tag in tags_to_wrap:
        content = wrap_specific_tags_with_cdata(tag, content.strip())
    tree = ET.ElementTree(ET.fromstring(content))
    root = tree.getroot()
    Data={}
    for parent in root.iter():
        for child in list(parent):
            if child.tag == 'final_extracted_topic':
                Data.update({'topic':child.text.strip()})
            if child.tag == 'english':
                Data.update({'QuestionEnglish':child.text.strip()})
            if child.tag == 'chinese':
                Data.update({'QuestionChinese':child.text.strip()})
    return Data
prompts_to_check = []
Repeat=5
for Folder in Folders:
    print(Folder)
    if all([ os.path.exists(f'{Folder}{os.sep}ParagraphTopicExtract_{i}.txt') for i in range(Repeat)]):
        Prompt=[HEAD]
        for i in range(Repeat):
            Prompt.append(f'\t<analysis_{i}>\n\n')
            Prompt.append(remove_original_paragraphs(open(f'{Folder}{os.sep}ParagraphTopicExtract_{i}.txt', 'r', encoding='UTF8').read()))
            Prompt.append(f'\n\n\t</analysis_{i}>\n')
        Prompt.append(END)
        Prompt = ''.join(Prompt)
        if os.path.exists(Folder) and not os.path.exists(f'{Folder}{os.sep}ParagraphTopicExtract.txt') :
            open(f'{Folder}{os.sep}PromptAnswerIntegrationParagraphTopicExtract.txt', 'w', encoding='UTF8').write(Prompt)
            prompts_to_check.append((Folder, Prompt))
GetResponseConcurrent(prompts_to_check)
AllResult={}
for Folder in tqdm.tqdm(Folders):
    AllResult.update({Folder:GetFinalResult(open(f'{Folder}{os.sep}ParagraphTopicExtract.txt', 'r', encoding='UTF8').read())})
json.dump(AllResult,open('TopicAndQuestion.json','w',encoding='utf8'),ensure_ascii=False,indent=4)
