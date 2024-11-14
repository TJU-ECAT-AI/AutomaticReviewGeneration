from GetResponse import *
import re
import os
import tqdm
from queue import Queue, Empty
from threading import Thread, Semaphore
import xml.etree.ElementTree as ET
import time
import json
import shutil
import requests
URL=
KEY=
MODEL=
HEAD='''# Paragraph Topic Extractor and Question Generator
You are an expert in academic writing and text analysis. Your task is to extract the main topic from a given paragraph of an academic review and then generate a single comprehensive question based on that topic. Follow these steps carefully:
1. Read the provided paragraph carefully.
2. Analyze its content to identify the main topic.
3. Formulate a concise topic statement.
4. Based on the extracted topic, create a single comprehensive question that can guide the extraction of detailed information from the paragraph.
5. Translate the question into Chinese.
Output your results in the following XML format:
```xml
<analysis>
  <original_paragraph>
    [Insert the original paragraph here]
  </original_paragraph>
  <topic_extraction>
    <step1_initial_thoughts>
      [Provide your initial thoughts about the paragraph's content]
    </step1_initial_thoughts>
    <step2_key_concepts>
      [List the key concepts or ideas present in the paragraph]
    </step2_key_concepts>
    <step3_topic_formulation>
      [Explain how you're formulating the topic based on the key concepts]
    </step3_topic_formulation>
    <extracted_topic>
      [State the extracted topic in a clear, concise manner]
    </extracted_topic>
  </topic_extraction>
  <question_generation>
    <step1_question_formulation>
      [Explain how you're formulating the question based on the extracted topic]
    </step1_question_formulation>
    <generated_question>
      <english>[Present the final version of your generated question in English]</english>
      <chinese>[Present the Chinese translation of the generated question]</chinese>
    </generated_question>
  </question_generation>
</analysis>
```
Remember to:
- Be thorough in your analysis and explanation.
- Ensure that the extracted topic accurately represents the main idea of the paragraph.
- Create a single, comprehensive question that can elicit detailed information about the topic from the paragraph.
- Use academic language appropriate for the field of study.
- Provide both English and Chinese versions of the generated question.
<file-attachment-contents filename="Paragraphs.txt"> 
<Paragraphs>
'''
END="""
</Paragraphs>
</file-attachment-contents>
"""
Folders=[f'{i}{os.sep}{j}' for i in os.listdir('RawFromPDF') for j in os.listdir(f'RawFromPDF{os.sep}{i}') if '_Review_' in j]
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
    progress_bar = tqdm.tqdm(total=len(prompts)*Repeat, position=0, leave=True)
    def worker():
        while True:
            try:
                folder, prompt = prompt_queue.get_nowait()
            except Empty:
                break
            for Time in range(Repeat):
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
                            response = GetResponseFromClaudeViaWebAgent(prompt,URL,KEY,MODEL)
                            semaphore2.release()
                        else:
                            open('Waitlog','a').write('\t'.join([folder,time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime()),'waiting\n']))
                            time.sleep(0.5)
                            continue
                        try:
                            if ('<analysis>' not in response )or ('<extracted_topic>' not in response )or ('<generated_question>' not in response ):
                                raise RuntimeError('Error Response')
                            content='<?xml version="1.0" encoding="UTF-8"?>\n<analysis>\n'+response.strip().split('<analysis>')[-1]
                            content=content.split('</analysis>')[0]+'\n</analysis>'
                            tags_to_wrap=['original_paragraph','step1_initial_thoughts',
                                          'step2_key_concepts','step3_topic_formulation',
                                          'extracted_topic','step1_question_formulation',
                                          'english','chinese']
                            for tag in tags_to_wrap:
                                content = wrap_specific_tags_with_cdata(tag, content.strip())
                            root = ET.fromstring(content)
                        except:
                            with open(os.path.join(folder, f'ParagraphTopicExtract_{Time}-{try_num}.txt'), 'w', encoding='UTF8') as file:
                                file.write(response + '\n')
                            try_num += 1
                            continue
                        with open(os.path.join(folder, f'ParagraphTopicExtract_{Time}.txt'), 'w', encoding='UTF8') as file:
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
prompts_to_check = []
Repeat=5
for File in Folders:
    print(File)
    file_content = open(f'RawFromPDF{os.sep}{File}', 'r', encoding='UTF8').read()
    Prompt = HEAD + file_content + END
    File_path = File.strip(".txt").split(os.sep)[1]
    os.makedirs(File_path,exist_ok=True)
    if os.path.exists(File_path) and not os.path.exists(f'{File_path}{os.sep}ParagraphTopicExtract_{Repeat-1}.txt') and len(Prompt)<333333:
        open(f'{File_path}{os.sep}PromptParagraphTopicExtract.txt', 'w', encoding='UTF8').write(Prompt)
        prompts_to_check.append((File_path, Prompt))
GetResponseConcurrent(prompts_to_check)
