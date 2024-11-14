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
URL=
KEY=
MODEL=
max_tokens=524288
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
def wrap_specific_tags_with_cdata(tag_name, content):
    tag_pattern = f'<{tag_name}>(.*?)</{tag_name}>'
    replacement = f'<{tag_name}><![CDATA[\\1]]></{tag_name}>'
    return re.sub(tag_pattern, replacement, content, flags=re.DOTALL)
def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens
def GetResponseConcurrent(prompts, Threads, STDOUT):
    prompt_queue = Queue()
    for item in prompts:
        prompt_queue.put(item)
    semaphore1 = Semaphore(value=0)
    semaphore2 = Semaphore(value=16)
    progress_bar = tqdm.tqdm(total=len(prompts), position=0, desc='GenerateParagraphOfReview', file=STDOUT)
    def worker():
        while True:
            try:
                i, Time, folder, part, prompt, DOI = prompt_queue.get_nowait()
            except Empty:
                break
            if os.path.exists(os.path.join(f'Paragraph{"All" if "All" in part else ""}', f'{part}_{Time}.txt')):
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
                    if not bool(re.search(r'\[\s*10\.\d+[/_]+[-._;()/:A-Za-z0-9]+', response)):
                        TRY += 1
                        with open(os.path.join(f'Paragraph{"All" if "All" in part else ""}', f'{part}_{Time}_{TRY}.txt'), 'w', encoding='UTF8') as file:
                            file.write(response + '\n')
                        continue
                    content = '<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n<English>\n' + response.strip().split('<English>')[-1]
                    content = content.split('</References>')[0] + '\n</References>\n</Response>'
                    tags_to_wrap = ["English", "Chinese", "References"]
                    for tag in tags_to_wrap:
                        content = wrap_specific_tags_with_cdata(tag, content.strip())
                    WrongDOI = []
                    try:
                        root = ET.fromstring(content)
                        DOIFromResponse = [doi.strip() for doi in root.findall('References')[0].text.split('\n') if doi.strip()]
                        WrongDOI = [doi for doi in DOIFromResponse if doi not in DOI]
                        if WrongDOI:
                            raise RuntimeError('WrongDOI')
                    except Exception as e:
                        TRY += 1
                        with open(os.path.join(f'Paragraph{"All" if "All" in part else ""}', f'{part}_{Time}_{TRY}.txt'), 'w', encoding='UTF8') as file:
                            file.write(response + '\nWrongDOI\n')
                        continue
                    with open(os.path.join(f'Paragraph{"All" if "All" in part else ""}', f'{part}_{Time}.txt'), 'w', encoding='UTF8') as file:
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
def process_compress_item(INPUT):
    item,TOPIC,QUESTION,CompressHEAD,CompressEND=INPUT
    QUOTES = item['Quotes']
    ENGLISH = item['English']
    CompressMIDDLE = f'''Topic: {TOPIC}
Question: {QUESTION}
Quotes: {QUOTES}
English Text: {ENGLISH}
'''
    prompt = CompressHEAD + CompressMIDDLE + CompressEND
    Response = ''
    while not Response:
        try:
            Response = json.loads('{' + GetResponseFromClaudeViaWebAgent(prompt).split('{', 1)[1].rsplit('}', 1)[0] + '}')['compressed_text']
        except Exception as e:
            pass
    return json.dumps({'Quotes': QUOTES, 'English': Response, 'Doi': item['Doi']}, ensure_ascii=False)
def CompressDocument(RawDocument, TOPIC, QUESTION,ExtremeCompression=False, num_processes=4):
    items=[json.loads(s) for s in {json.dumps(d, sort_keys=True) for d in json.loads('[' + RawDocument + ']')}]
    QUOTES=''
    ENGLISH=''
    CompressHEAD='''# Text Compression Task
You will be provided with the following information:
'''
    CompressMIDDLE=f'''Topic: {TOPIC}
Question: {QUESTION}
Quotes: {QUOTES}
English Text: {ENGLISH}
'''
    CompressEND='''
Understanding the inputs:
1. Topic: This provides the overall context or subject area of the text. Use this to understand the broader theme and to ensure your compressed text remains relevant to the main subject.
2. Question: This is the specific query that the English text is attempting to answer. Your compressed text should focus on addressing this question effectively.
3. Quotes: These are relevant excerpts that may provide key information or support the main points of the text. Consider integrating these into your compressed version if they are crucial to answering the question.
4. English Text: This is the main body of text that you need to compress. It contains the detailed information addressing the question within the context of the topic.
Based on this information, create a compressed version of the English paragraph. Follow these guidelines:
1. Carefully read and analyze all provided inputs, understanding how they relate to each other.
2. Use the Chain of Thought (COT) method to compress the text:
   a. Identify the main themes and key information in the paragraph, considering how they relate to the topic and question.
   b. Determine which information is core to answering the question and which is secondary.
   c. Consider how to express the same meanings using more concise language.
   d. Think about how to combine related ideas to reduce redundancy.
   e. Evaluate how the quotes can be integrated to support key points.
3. Create a compressed version ensuring that you:
   - Retain all key concepts and main ideas relevant to the topic and essential for answering the question
   - Maintain the logical flow of information
   - Preserve important details and examples, especially those from the quotes that directly support the answer
   - Remove redundant or less critical information that doesn't directly contribute to addressing the question
   - Use concise language without altering the original meaning
   - Maintain the original tone and writing style
4. The compressed text should stand alone as a coherent summary that effectively addresses the question within the context of the topic.
5. Do not introduce new information not present in the original text or quotes.
Output format:
```json
{
  "thought_process": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "compressed_text": "Your compressed English text here"
}
```
In the "thought_process", detail your compression process, explaining:
- How you used the topic and question to guide your compression
- Why you chose to keep certain information while removing others
- How you integrated relevant quotes
- How you ensured the core meaning of the original text was preserved while effectively addressing the question and staying relevant to the topic'''
    if ExtremeCompression:
        CompressHEAD='''# # High Compression Text Task
You will be provided with the following information:
'''
        CompressEND='''
Understanding the inputs:
1. Topic: The overall context or subject area. Use this to maintain relevance in your highly compressed text.
2. Question: The specific query the text aims to answer. Your compressed version should address this concisely.
3. Quotes: Key excerpts that may be crucial. Consider their essence when compressing.
4. English Text: The main body to compress drastically while retaining core meaning.
Your task is to create a highly compressed version of the English paragraph, aiming for the shortest possible text while preserving essential information. Follow these guidelines:
1. Analyze all inputs, understanding their interrelations.
2. Use an enhanced Chain of Thought (COT) method for extreme compression:
   a. Identify the absolutely crucial information needed to answer the question within the topic's context.
   b. Ruthlessly eliminate any information that isn't vital to addressing the question.
   c. Find the most concise way to express each essential point.
   d. Merge related ideas aggressively to eliminate any redundancy.
   e. Distill quotes to their bare essence if they're crucial to the answer.
   f. Review and further compress by removing any remaining non-essential words or phrases.
3. Create an extremely compressed version that:
   - Retains only the most critical concepts essential for answering the question
   - Maintains a bare-bones logical flow
   - Preserves only the most crucial details or examples
   - Uses ultra-concise language, potentially employing abbreviations where clear
   - Maintains clarity and accuracy, but prioritizes brevity over style
4. The compressed text should be as short as possible while still coherently answering the question within the topic's context.
5. Absolutely no new information should be introduced.
Output format:
```json
{
  "thought_process": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ...",
    "Final compression step: ..."
  ],
  "compressed_text": "Your highly compressed English text here"
}
```
In the "thought_process", detail your extreme compression process, explaining:
- How you identified and retained only the most crucial information
- Your strategies for achieving maximum brevity
- How you ensured the core question was still answered despite severe compression
- Any trade-offs made between information preservation and achieving high compression
Remember, the goal is to create the shortest possible text that still effectively answers the question within the topic's context. Prioritize extreme brevity while maintaining essential meaning.'''
    with Pool(num_processes) as pool:
        results = list(tqdm.tqdm(
            pool.imap(process_compress_item, [[item,TOPIC,QUESTION,CompressHEAD,CompressEND] for item in items]),
            total=len(items),
            desc="Compressing documents"
        ))
    return ',\n'.join(set(results))
def Main(Folder, TOPIC, Threads, MaxToken,STDOUT, REPEAT=9):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    ParagraphQuestionsForReview = [i.strip() for i in open('../ParagraphQuestionsForReview', 'r', encoding='UTF8').readlines() if i.strip()]
    QuestionsForReview = [i.strip() for i in open('../QuestionsForReview', 'r', encoding='UTF8').readlines() if i.strip()]
    NumberOfParts = len(QuestionsForReview)
    HEAD = """Based on the in-depth details extracted from the file related to '"""
    MIDDLE0 = f"""', construct an analytical and comprehensive review section on {TOPIC}, emphasizing '"""
    MIDDLE1 = """'.
    While developing the content, adhere to the following protocols:
    1. **Accurate Citations**: Reference specific content from the file by embedding the actual DOI numbers furnished, without any alterations. Utilize the format '[Placeholder_Of_DOI]' right after the sentence where the reference is applied. 
    2. **Strict Adherence**: Stick to the particulars and DOI details from the file; avoid integrating external or speculative data.
    3. **Scientific Language**: Uphold a technical and scholarly diction akin to chemical engineering literature.
    4. **Format & Translation**: After creating the main review content, append an 'integrative understanding and prospective outlook' section within the same <English></English> and <Chinese></Chinese> XML tags, demarcated with '※※※'. This segment should transcend a mere summation and foster a forward-thinking discussion, potentially elucidating future directions and broader horizons grounded in the file's content. 
    The content structure should resemble:
    <example>
            <English> 
                    Detailed analysis established from the study of reference [Placeholder_Of_DOI1]. Synthesized comprehension stemming from references [Placeholder_Of_DOI2] and [Placeholder_Of_DOI3]. 
                    ※※※
                    Integrative understanding and prospective outlook: Taking into consideration the advancements and findings discussed in the file, there lies an opportunity to explore emerging fields and innovative methodologies. Future research endeavors might focus on ...
            </English>
            <Chinese> 
                    基于[Placeholder_Of_DOI1]参考文献的深度分析。从[Placeholder_Of_DOI2]和[Placeholder_Of_DOI3]的参考文献中获得的综合理解。
                    ※※※
                    综合理解与未来展望: 考虑到文件中讨论的先进成果和发现，我们有机会探索新兴领域和创新方法。未来的研究努力可能会集中在...
            </Chinese>
            <References> 
                    Placeholder_Of_DOI1
                    Placeholder_Of_DOI2
                    Placeholder_Of_DOI3
            </References>
    </example>
    In the 'integrative understanding and prospective outlook' segment, aspire to:
    - **Offer an expansive perspective**: Illuminate potential pathways and pioneering research opportunities, grounded in the details divulged in the file.
    - **Propose forward-thinking suggestions**: Advocate for innovative angles and burgeoning domains that might take center stage in future explorations, while rooted in the file's details.
    Finally, compile all the cited DOIs in the 'References' compartment, adhering to the <References></References> XML tag, using the exact DOIs designated in the file.
    <file-attachment-contents filename="""
    END = """
    </file-attachment-contents>
    """
    prompts = []
    os.makedirs('Paragraph', exist_ok=True)
    for Time in range(0, REPEAT):
        for i in range(NumberOfParts):
            if os.path.exists(f'{i+1}') and not os.path.exists(f'Paragraph{os.sep}BestParagraph{i+1}.txt'):
                RawDocument = open(f'{i+1}/EnglishWithQuotes.txt', 'r', encoding='UTF8').read().strip()[:-1]
                document=RawDocument
                DOI = [j['Doi'] for j in json.loads('[' + document + ']')]
                prompt_framework = HEAD + MIDDLE0 + MIDDLE1+END
                framework_tokens = num_tokens_from_string(prompt_framework)        
                max_doc_tokens = MaxToken - framework_tokens
                prompt = replace_with_html_entities(HEAD + QuestionsForReview[i] + MIDDLE0 + ParagraphQuestionsForReview[i] + MIDDLE1 + f'"Paragraph{i+1}Info.txt">\n') + document + END
                open(f'Paragraph{os.sep}Prompt{i+1}_{Time}.Compress0.txt', 'w', encoding='UTF8').write(prompt)
                CompressTry=0
                while num_tokens_from_string(document)>max_doc_tokens:
                    CompressTry+=1
                    if num_tokens_from_string(document)>max_doc_tokens:
                        RawDocument=CompressDocument(RawDocument, QuestionsForReview[i], ParagraphQuestionsForReview[i],CompressTry>3,Threads)
                        document=RawDocument
                    if num_tokens_from_string(document)>max_doc_tokens:    
                        document=[{'DOC':i['English'],"Doi":i["Doi"]} for i in json.loads('[' + document + ']')]
                        document=',\n'.join(json.dumps(i,ensure_ascii=False) for i in document)
                    prompt = replace_with_html_entities(HEAD + QuestionsForReview[i] + MIDDLE0 + ParagraphQuestionsForReview[i] + MIDDLE1 + f'"Paragraph{i+1}Info.txt">\n') + document + END
                    open(f'Paragraph{os.sep}Prompt{i+1}_{Time}.Compress{CompressTry}.txt', 'w', encoding='UTF8').write(prompt)
                prompt = replace_with_html_entities(HEAD + QuestionsForReview[i] + MIDDLE0 + ParagraphQuestionsForReview[i] + MIDDLE1 + f'"Paragraph{i+1}Info.txt">\n') + document + END
                open(f'Paragraph{os.sep}Prompt{i+1}_{Time}.txt', 'w', encoding='UTF8').write(prompt)
                prompts.append((i, Time, f"{i+1}", f"Paragraph{i+1}", prompt, DOI))
    GetResponseConcurrent(prompts, Threads, STDOUT)
    os.chdir('..')
    sys.stdout = old_stdout
if __name__ == "__main__":
    Main(Folder='Answer', TOPIC='propane dehydrogenation catalysts',
         Threads=16, MaxToken=25000, STDOUT=sys.stdout, REPEAT=9)
