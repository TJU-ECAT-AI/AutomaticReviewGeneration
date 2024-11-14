import os
import re
import sys
import time
import tqdm
import json
import openai
import func_timeout
import xml.etree.ElementTree as ET
from threading import Thread, Semaphore
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
HEAD = '''Based on the attached content below containing multiple review paragraphs focused on the topic of "'''
MIDDLE0 = '''", evaluate each paragraph on the following dimensions:
1. **Clarity** (10 points): Is the paragraph clearly written and easy to understand?
2. **Depth** (10 points): Does the paragraph delve deep into the topic and offer nuanced insights?
3. **Relevance** (10 points): Is the content of the paragraph directly related to the topic "'''
MIDDLE1 = '''?
4. **Coherence** (10 points): Does the paragraph maintain a logical flow and coherence in its discussion?
5. **Originality** (10 points): Does the paragraph offer new perspectives or original ideas related to the topic?
6. **Evidence-based** (10 points): Is the content backed by relevant evidence or references?
7. **Structure** (10 points): Is the paragraph well-structured with a clear beginning, middle, and end?
8. **Text Length** (20 points): Does the paragraph maintain an appropriate length? The longer, the better.
9. **DistinctNumberOfDOIs** (20 points): Count the distinct DOIs (format '10\.\d{4,9}[/_]+[-._;()/:A-Za-z0-9]+') in each paragraph and compare. Assign a relative score based on the number of unique references compared to other paragraphs; the paragraph with the most unique references gets the highest score.
10. **Comprehensiveness** (10 points): Does the paragraph cover all pertinent aspects related to the topic in a comprehensive manner?
11. **Relatedness** (20 points): Does the paragraph exhibit thematic consistency with other paragraphs when discussing similar or identical DOI references? Is the paragraph's explanation and context concerning a specific DOI analogous to that in other paragraphs that cite the same DOI?
Regarding the new **Relatedness** criterion:
- Analyze the paragraphs that share common DOI references, assessing the degree of similarity in the contextual use and discussion surrounding those references.  
- Evaluate whether the paragraph aligns with or diverges from the shared thematic discussions related to the DOI in question when compared to other paragraphs that cite the same DOI.
- Ensure that the relatedness is not merely surface-level or lexical but digs deeper into the thematic and contextual consistency across different paragraphs that cite the same DOI.
Using these criteria, evaluate each paragraph methodically, ensuring that each dimension is assessed with rigor and impartiality. Subsequently, the paragraph that amasses the highest cumulative score across all dimensions should be selected as the one that most effectively addresses the topic at hand, while also maintaining cohesion, depth, and thematic alignment with related discussions in different paragraphs. Remember to be meticulous and transparent in the scoring to ensure that the selection is justifiable and replicable.
<file-attachment-contents filename="Paragraphs.txt"> 
<Paragraphs>
'''
END = """
</Paragraphs>
</file-attachment-contents>
After evaluating all paragraphs for each dimension, provide scores for each dimension individually. 
For example:
<Scores>
    <Paragraph id="1">
        <Clarity>8</Clarity>
        <Depth>7</Depth>
        <Relevance>9</Relevance>
        <Coherence>7</Coherence>
        <Originality>6</Originality>
        <Evidence-based>8</Evidence-based>
        <Structure>9</Structure>
        <TextLength>16</TextLength>
        <DistinctNumberOfDOIs>18</DistinctNumberOfDOIs>
        <Comprehensiveness>8</Comprehensiveness>
        <TotalScore>88</TotalScore>
    </Paragraph>
    <!-- Scores for additional paragraphs -->
</Scores>
Finally, identify and present the paragraph that achieved the highest combined score:
<BestParagraphResult>
    <ParagraphID>1</ParagraphID>
    <Content>
        {Raw content of the top-scoring paragraph}
        <References>
        {Raw references from the top-scoring paragraph}
        </References>
    </Content>
</BestParagraphResult>
"""
def replace_with_html_entities(text):
    entities = {
        '[': '\[',
        ']': '\]',
        '_': '\_',
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
def GetResponseConcurrent(prompts, Threads, STDOUT):
    prompt_queue = Queue()
    for item in prompts:
        prompt_queue.put(item)
    semaphore1 = Semaphore(value=0)
    semaphore2 = Semaphore(value=16)
    progress_bar = tqdm.tqdm(total=len(prompts), position=0, desc='GenerateRatingsForReviewParagraphs', file=STDOUT)
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
                response = None
                try:
                    if semaphore1.acquire(blocking=False):
                        semaphore_acquired = semaphore1
                        response = GetResponseFromClaude(prompt)
                        semaphore1.release()
                    elif semaphore2.acquire(blocking=False):
                        semaphore_acquired = semaphore2
                        response = GetResponseFromClaudeViaWebAgent(prompt)
                        semaphore2.release()
                    else:
                        open('Waitlog', 'a').write('\t'.join([str(i), folder, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()), 'waiting\n']))
                        time.sleep(0.5)
                        continue
                    if (not (re.search(r'<Scores>\s*<Paragraph\s*id="\d+">\s*<Clarity>', response))
                           or ('※※' not in response)
                           or ('TotalScore' not in response)
                           or ('<References>' not in response)):
                        open(os.path.join(f'Paragraph', f'Best{part}_{TRY}.txt'), 'w', encoding='UTF8').write(response + '\n')
                        TRY += 1
                        continue
                    try:
                        content = '<?xml version="1.0" encoding="UTF-8"?>\n<Scores>\n' + response.strip().split('<Scores>')[-1]
                        content = content.split('</Scores>')[0] + '\n</Scores>'
                        root = ET.fromstring(content)
                        total_scores = []
                        for paragraph in root.findall('Paragraph'):
                            total_scores.append(int(paragraph.find('TotalScore').text))
                    except:
                        open(os.path.join(f'Paragraph', f'Best{part}_{TRY}.txt'), 'w', encoding='UTF8').write(response + '\n')
                        TRY += 1
                        continue
                    with open(os.path.join(f'Paragraph', f'Best{part}.txt'), 'w', encoding='UTF8') as file:
                        file.write(response + '\n')
                    break
                except (Exception, func_timeout.exceptions.FunctionTimedOut) as e:
                    pattern = r"Function\s+(\S+).*?timed out after\s+(\d+\.\d+)\s+seconds."
                    replacement = r"\1 timed out after \2 s"
                    if semaphore_acquired:
                        semaphore_acquired.release()
                    open('Exceptionlog', 'a').write('\t'.join([str(i), folder, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()),
                                                               re.sub(pattern, replacement, str(e), flags=re.DOTALL), '\n']))
                    continue
            progress_bar.update(1)
    threads = [Thread(target=worker) for _ in range(Threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    progress_bar.close()
def extract_sections_with_tags(content):
    english_matches = re.findall(r"<English>(.*?)</English>", content, re.DOTALL)
    chinese_matches = re.findall(r"<Chinese>(.*?)</Chinese>", content, re.DOTALL)
    reference_matches = re.findall(r"<References>(.*?)</References>", content, re.DOTALL)
    reference_matches = reference_matches if reference_matches else re.findall(r"<Reference>(.*?)</Reference>", content, re.DOTALL)
    return '\n'.join(english_matches), '\n'.join(chinese_matches), '\n'.join(reference_matches)
def Main(Folder, Threads, STDOUT):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    ParagraphQuestionsForReview = [i.strip() for i in open('../ParagraphQuestionsForReview', 'r', encoding='UTF8').readlines() if i.strip()]
    prompts = []
    filtered_files = [file for file in os.listdir('Paragraph') if re.match(r"Paragraph(\d+)_(\d+)\.txt", file)]
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
    file_dict = {k: v for k, v in file_dict.items()}
    for i in sorted(file_dict.keys()):
        merged_content = []
        for file_name in file_dict[i]:
            with open(os.path.join('Paragraph', file_name), 'r', encoding='UTF8') as file:
                english_matches, chinese_matches, reference_matches = extract_sections_with_tags(file.read())
                merged_content.append(f'    <Paragraph id="{file_name.split("_")[1].split(".")[0]}">\n' + english_matches.strip() + '\n<References>\n' + reference_matches.strip() + '\n</References>\n</Paragraph>')
        prompt = replace_with_html_entities(HEAD + ParagraphQuestionsForReview[i-1] + MIDDLE0 + ParagraphQuestionsForReview[i-1] + MIDDLE1) + '\n'.join(merged_content) + END
        open(f'Paragraph{os.sep}PromptBest{i}.txt', 'w', encoding='UTF8').write(prompt)
        prompts.append((i, f"{i}", f"Paragraph{i}", prompt))
    GetResponseConcurrent(prompts, Threads, STDOUT)
    os.chdir('..')
    sys.stdout = old_stdout
if __name__ == "__main__":
    Main('Answer',8,sys.stdout)
