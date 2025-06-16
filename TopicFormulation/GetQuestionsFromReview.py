import os
import re
import json
import shutil
import sys
import time
from math import inf
from queue import Queue, Empty
from threading import Thread, Semaphore
import func_timeout
import tqdm
overtime = inf
def construct_prompt(HEAD, END,HEADFromReview, ENDFromReview, FromReview,REPEAT, File):
    if not os.path.exists(f"{File.replace('.txt', '')}{os.sep}QuestionsFromReview_{REPEAT - 1}.txt"):
        if FromReview:
            Content = open(File, 'r', encoding='UTF8').read()
            Prompt = HEADFromReview + File + "'>\n" + Content + '\n' + ENDFromReview
        else:
            Prompt = HEAD + END
        os.makedirs(File.replace('.txt', ''), exist_ok=True)
        open(File.replace('.txt', '') + os.sep + 'PromptQuestionsFromReview', 'w', encoding='UTF8').write(Prompt)
        return File.replace('.txt', ''), Prompt
def GetResponse(prompts, REPEAT, Threads, FunctionClaudeAPI, FunctionOpenAIAPI, STDOUT, MaxToken=25000,JsonCheck=False):
    results = [None] * len(prompts)
    prompt_queue = Queue()
    for i, (folder, prompt) in enumerate(prompts):
        prompt_queue.put((i, folder, prompt))
    ClaudeAPISemaphore = []
    OpenAIAPISemaphore = []
    FunctionClaudeAPI = {k: v for k, v in FunctionClaudeAPI.items() if v}
    FunctionOpenAIAPI = {k: v for k, v in FunctionOpenAIAPI.items() if v}
    for i in FunctionClaudeAPI:
        ClaudeAPISemaphore.append(Semaphore(value=1))
    for i in FunctionOpenAIAPI:
        OpenAIAPISemaphore.append(Semaphore(value=3))
    progress_bar = tqdm.tqdm(total=len(prompts) * REPEAT, position=0, desc='主题提取', file=STDOUT)
    def worker():
        start_time = time.time()
        while True:
            if time.time() - start_time > overtime:
                print(f"Worker timed out for prompt {i}")
                break
            try:
                i, folder, prompt = prompt_queue.get_nowait()
            except Empty:
                break
            for Time in range(REPEAT):
                TRY = 0
                start_time2 = time.time()
                while True:
                    if time.time() - start_time2 > overtime:
                        print(f"Worker timed out for prompt {i}")
                        break
                    if folder.startswith('10.') and os.path.exists(os.path.join(folder, f'QuestionsFromReview_{Time}.txt')):
                        break
                    semaphore_acquired = None
                    response = None
                    try:
                        for semaphore, GetResponseFunction in zip(ClaudeAPISemaphore, FunctionClaudeAPI.values()):
                            if semaphore.acquire(blocking=False):
                                semaphore_acquired = semaphore
                                response = GetResponseFunction(prompt, max_tokens=MaxToken)
                                semaphore.release()
                                break
                        if not response:
                            for semaphore, GetResponseFunction in zip(OpenAIAPISemaphore, FunctionOpenAIAPI.values()):
                                if semaphore.acquire(blocking=False):
                                    semaphore_acquired = semaphore
                                    response = GetResponseFunction(prompt, max_tokens=MaxToken)
                                    semaphore.release()
                                    break
                        if not response:
                            time.sleep(0.5)
                            continue
                        if len(response) < 200 or response.strip().startswith('Unfortunately'):
                            with open(os.path.join(folder, f'QuestionsFromReview_{Time}-{TRY}.txt'), 'w',
                                      encoding='UTF8') as file:
                                file.write(response + '\n')
                                TRY += 1
                                continue
                        if JsonCheck:
                            try:
                                ReshapeOutlines(response)
                            except Exception:
                                with open(os.path.join(folder, f'QuestionsFromReview_{Time}-{TRY}.txt'), 'w',
                                          encoding='UTF8') as file:
                                    file.write(response + '\n')
                                    TRY += 1
                                    continue                            
                        with open(os.path.join(folder, f'QuestionsFromReview_{Time}.txt'), 'w',
                                  encoding='UTF8') as file:
                            file.write(response + '\n')
                        results[i] = response
                        break
                    except (Exception, func_timeout.exceptions.FunctionTimedOut) as e:
                        pattern = r"Function\s+(\S+).*?timed out after\s+(\d+\.\d+)\s+seconds."
                        replacement = r"\1 timed out after \2 s"
                        if semaphore_acquired:
                            semaphore_acquired.release()
                        open('Exceptionlog', 'a').write(
                            '\t'.join([str(i), folder, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()),
                                       re.sub(pattern, replacement, str(e), flags=re.DOTALL), '\n']))
                        TRY += 1
                        continue
                progress_bar.update(1)
    available_api_count = len(FunctionClaudeAPI) + len(FunctionOpenAIAPI)
    if available_api_count == 0:
        effective_threads = 1
        raise Exception('No Available API.')
    else:
        effective_threads = min(Threads, available_api_count) if Threads > 0 else available_api_count
    print(f"Using {effective_threads} threads based on {available_api_count} available APIs")
    threads = [Thread(target=worker) for _ in range(effective_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    progress_bar.close()
    return results
def ReshapeOutlines(text):
    formatted_lines = []
    try:
        if text.strip():
            data = json.loads('{'+text.split('{',1)[-1].rsplit('}',1)[0]+'}')
            if 'outlines' in data and isinstance(data['outlines'], list):
                for outline in data['outlines']:
                    if isinstance(outline, dict) and 'contents' in outline and 'section' in outline:
                        contents = outline['contents']
                        section = outline['section'].strip()
                        if contents and section:
                            for content in contents:
                                formatted_lines.append(section+' - '+content)
                        else :
                            raise Exception('不符合格式要求')
                    else:
                        raise Exception('不符合格式要求')
            else:
                raise Exception('不符合格式要求')
        else:
            raise Exception('不符合格式要求')
        if formatted_lines:
            return '\n'.join(formatted_lines)
    except json.JSONDecodeError as e:
        raise Exception(f"JSON解析错误: {e}")
    except Exception as e:
        raise Exception(f"处理过程中出错: {e}")
def GetQuestions(text):
    lines = text.split('\n')
    formatted_lines = []
    current_section = ""
    for line in lines:
        if line.strip().startswith(tuple([f"{i}. " for i in range(100)])) and (
        len(re.findall(r'[a-zA-Z]', line.strip())) / len(line.strip()) > 0.6 if line.strip() else False):
            current_section = line.split('. ')[1].strip()
            formatted_lines.append(current_section)
    return '\n'.join([f'{i + 1}. {j}' for i, j in enumerate(formatted_lines)])
def Main(Folder, TOPIC, Threads, FunctionClaudeAPI, FunctionOpenAIAPI, STDOUT,FromReview=False, MaxToken=25000):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    REPEAT = 5
    os.chdir(Folder)
    Folders = [i for i in os.listdir('.') if i.startswith('10.') and i.endswith('.txt')]
    Folders.sort()
    HEAD = f"""Your task is to craft a detailed and logical question-based outline for a comprehensive review article about {TOPIC}. The outline should first be presented entirely in English, followed by its translation in Chinese after a line break. The detailed instructions are as follows:
"""
    HEADFromReview= f"""Based on the review about {TOPIC} presented in the attached file content, your task is to craft a detailed and logical question-based outline for a comprehensive review article. The outline should first be presented entirely in English, followed by its translation in Chinese after a line break. The detailed instructions are as follows:
<file-attachment-contents filename='"""
    END = f'''
Ensure that your outline adheres to the following criteria:
1. Develop at least 17 primary themes that are intricately linked to {TOPIC}, paving the way for a structured review article.
2. Under each primary theme, identify at least 7 detailed questions that probe deep into the respective themes, fostering detailed and insightful paragraphs in the final article.
3. Integrate both experimental and computational methodologies, including aspects from DFT and other theoretical approaches, evenly and coherently in the questions to offer a rounded perspective on {TOPIC}.
4. The progression of the primary themes should mirror a traditional review trajectory: starting with the foundational concepts, transitioning to advanced nuances, discussing prevailing challenges, and culminating with future prospects and visions.
5. Formulate the questions such that when answered, they collectively offer a wide-ranging view of the {TOPIC} landscape, without any significant overlap or omission of vital aspects.
Remember that this outline should function as a structured pathway for researchers, guiding them to draft a holistic review article on {TOPIC} without overlooking any critical details.
Start with the complete English version of the outline. After finishing it, provide the Chinese translation, maintaining the depth and essence of the English version, separated by a line break.
'''
    ENDFromReview='''</file-attachment-contents>
'''+END
    IntegrationQuestionsForReview = f"""Your task is to construct a structured, question-based outline for a comprehensive review article on the topic detailed in the provided attachment, with a significant emphasis on {TOPIC}. The focus should be on presenting a thorough exploration across various dimensions of {TOPIC}, smoothly transitioning from a foundational understanding to an in-depth analysis of specific instances related to {TOPIC}. The outline should facilitate a logical flow between a broad range of themes, consistently maintaining a focal emphasis on the core elements of {TOPIC}.
Instructions:
1. **Introduction**
- Begin with a section that lays the groundwork for the {TOPIC}, detailing its background, historical developments, and the evolution of key elements or breakthroughs within this field.
2. **Foundational Theories and Principles**
- Include a section on the fundamental theories and principles that form the basis of {TOPIC}, providing a foundation for a deeper exploration into specific areas or instances in later sections.
3. **Detailed Examination of Specific Instances**
- Significantly expand the section dedicated to the specific instances or case studies of {TOPIC}, covering a broad spectrum of applications, variations, or case studies that illustrate the depth and breadth of the field.
4. **Methodologies and Techniques**
- Delve into the diverse methodologies and techniques that are vital to researching and understanding {TOPIC}, maintaining an equitable focus on both theoretical and practical approaches.
5. **Integrative Discussion Section**
- Include a single section that integrates discussions on related sub-topics, such as technological, economic, and sustainability aspects, highlighting their interconnections and impacts on the main {TOPIC}.
6. **Conclusion and Future Directions**
- Conclude with a synthesis of insights from all sections, providing a comprehensive overview and identifying potential future research avenues in the realm of {TOPIC}.
7. **Output Format**:
- Present your outline in JSON format as per the structure provided below. The outline should encompass all the aforementioned sections, each clearly identified and structured in a logical manner.
**IMPORTANT: You must strictly follow this exact JSON template format:**
```json
{{
  "outlines": [
    {{
      "id": 1,
      "section": section1,
      "contents": [content1,content2,content3,]
    }},
    {{
      "id": 2,
      "section": section2,
      "contents": [content1,content2,content3,]
    }},
    {{
      "id": 3,
      "section": section3,
      "contents": [content1,content2,content3,]
    }}
  ]
}}
```
**JSON Format Requirements:**
- The response must be a valid JSON object
- Use the exact key names: "outlines", "id", "section", "contents"
- Each outline item must have a unique sequential id (1, 2, 3, ...)
- The "contents" field should contain the detailed question or topic description
- The "section" field should indicate the thematic category
- Ensure proper JSON syntax with correct quotation marks and commas
- Generate at least 5-10 outline items covering all the required sections
- Generate at least 3 contents for each section
Ensure that the outline serves as a rich source of information, seamlessly transitioning from theoretical underpinnings to a thorough exploration of {TOPIC}, and culminating in a cohesive conclusion that offers a vision for the future. The structure should be traditional yet detailed, emphasizing extensively on the key facets of {TOPIC}.
<file-attachment-contents filename='"""
    all_prompts = []
    FromReview= FromReview and bool(Folders)
    if FromReview:
        for folder in Folders:
            all_prompts.append(construct_prompt(HEAD, END,HEADFromReview, ENDFromReview,FromReview,REPEAT, folder))
    else:
        all_prompts.append(construct_prompt(HEAD, END,HEADFromReview, ENDFromReview,FromReview,REPEAT, 'DirectGeneration'))
    all_prompts = [i for i in all_prompts if i]
    responses = GetResponse(all_prompts, REPEAT, Threads, FunctionClaudeAPI, FunctionOpenAIAPI, STDOUT, MaxToken=MaxToken,JsonCheck=False)
    IndividualFolders = [i for i in os.listdir('.') if (i.startswith('10.') and not i.endswith('.txt')) or i=='DirectGeneration']
    IndividualFolders.sort()
    individual_integration_prompts = []
    for folder in IndividualFolders:
        integration_subfolder = f"{folder}{os.sep}IndividualIntegration"
        os.makedirs(integration_subfolder, exist_ok=True)
        if not os.path.exists(f"{integration_subfolder}{os.sep}Integration_0.txt"):
            folder_content = ''
            for Time in range(REPEAT):
                try:
                    with open(f'{folder}{os.sep}QuestionsFromReview_{Time}.txt', 'r', encoding='UTF8') as f:
                        content = f.read()
                        if content.strip():
                            folder_content += content + '\n\n\n'
                except FileNotFoundError:
                    print(f'Warning: File QuestionsFromReview_{Time}.txt not found in {folder}')
                    continue
            if folder_content.strip():
                individual_prompt = IntegrationQuestionsForReview + f'{folder}_content.txt>\n' + folder_content + '\n</file-attachment-contents>'
                with open(f'{integration_subfolder}{os.sep}PromptIndividualIntegration', 'w', encoding='UTF8') as f:
                    f.write(individual_prompt)
                individual_integration_prompts.append([integration_subfolder, individual_prompt])
            else:
                print(f'No valid content found in folder: {folder}')
    if individual_integration_prompts:
        individual_responses = GetResponse(individual_integration_prompts, 1, Threads, FunctionClaudeAPI,
                                         FunctionOpenAIAPI, STDOUT, MaxToken=MaxToken, JsonCheck=True)
        for i, (integration_subfolder, _) in enumerate(individual_integration_prompts):
            try:
                if individual_responses[i]:
                    with open(f'{integration_subfolder}{os.sep}QuestionsFromReview_0.txt', 'r', encoding='UTF8') as File:
                        individual_responses=ReshapeOutlines(File.read())
                    with open(f'{integration_subfolder}{os.sep}IntegrationManual.txt', 'w', encoding='UTF8') as File:
                        File.write(individual_responses)
            except Exception as e:
                print(f'Error processing individual integration for {integration_subfolder}: {e}')
    print('AllQuestionsFromReview - Overall Integration')
    if not os.path.exists(f"AllQuestionsFromReview{os.sep}QuestionsFromReview_0.txt"):
        os.makedirs('AllQuestionsFromReview', exist_ok=True)
        AllQuestionsFromReview = ''
        for folder in IndividualFolders:
            content_added = False
            integration_subfolder = f"{folder}{os.sep}IndividualIntegration"
            try:
                manual_path = f'{integration_subfolder}{os.sep}IntegrationManual.txt'
                if os.path.exists(manual_path):
                    with open(manual_path, 'r', encoding='UTF8') as f:
                        content = f.read()
                        if content.strip():
                            AllQuestionsFromReview += content + '\n\n\n'
                            content_added = True
                if not content_added:
                    integration_path = f'{integration_subfolder}{os.sep}Integration_0.txt'
                    if os.path.exists(integration_path):
                        with open(integration_path, 'r', encoding='UTF8') as f:
                            content = f.read()
                            if content.strip():
                                try:
                                    processed_content = ReshapeOutlines(content)
                                    AllQuestionsFromReview += processed_content + '\n\n\n'
                                    print(f'Added processed integration content from {folder}')
                                    content_added = True
                                except Exception as e:
                                    print(f'Error processing integration content from {folder}: {e}')
                                    AllQuestionsFromReview += content + '\n\n\n'
                                    print(f'Added raw integration content from {folder}')
                                    content_added = True
                if not content_added and os.path.exists(f'{folder}{os.sep}QuestionsFromReview_0.txt'):
                    folder_content_list = []
                    for Time in range(REPEAT):
                        fallback_path = f'{folder}{os.sep}QuestionsFromReview_{Time}.txt'
                        if os.path.exists(fallback_path):
                            with open(fallback_path, 'r', encoding='UTF8') as f:
                                fallback_content = f.read()
                                if fallback_content.strip():
                                    folder_content_list.append(fallback_content)
                    if folder_content_list:
                        folder_content = '\n\n\n'.join(folder_content_list)
                        AllQuestionsFromReview += folder_content + '\n\n\n'
                        content_added = True
            except Exception as e:
                print(f'Error reading content from {folder}: {e}')
        if AllQuestionsFromReview.strip():
            Prompt = IntegrationQuestionsForReview + 'AllQuestionsFromReview.txt>\n' + AllQuestionsFromReview + '\n</file-attachment-contents>'
            open(f'AllQuestionsFromReview{os.sep}PromptAllQuestionsFromReview.txt', 'w', encoding='UTF8').write(Prompt)
            REPEAT = 1
            responses = GetResponse([['AllQuestionsFromReview', Prompt]], REPEAT, Threads, FunctionClaudeAPI,
                                    FunctionOpenAIAPI, STDOUT, MaxToken=MaxToken,JsonCheck=True)
            try:
                with open(f'AllQuestionsFromReview{os.sep}QuestionsFromReview_0.txt', 'r', encoding='UTF8') as File:
                    Outline = ReshapeOutlines(File.read())
                with open(f'AllQuestionsFromReview{os.sep}QuestionsFromReviewManual.txt', 'w', encoding='UTF8') as File:
                    File.write(Outline)
            except Exception as e:
                print(f'Error processing overall integration results: {e}')
        else:
            print('Warning: No content available for overall integration')
    os.chdir('..')
    sys.stdout = old_stdout
def Main2(Folder, TOPIC, Threads, FunctionClaudeAPI, FunctionOpenAIAPI, STDOUT, MaxToken=25000):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    PaperQuestionsFromParagraphQuestionsForReview =f"""Utilizing the document provided, create a set of structured questions that correlate with the specific segments related to {TOPIC} as outlined in the literature. These questions are intended to extract precise information directly from the document to construct a comprehensive review article.
**Input Format**: You will receive questions in the format:
```
Section Name - Question content
Section Name - Question content
```
**Task**: Transform these input questions by combining the main topic {TOPIC} with the pertinent questions from each section, ensuring they are tailored to uncover detailed information from the document for in-depth data accumulation.
**Process**: 
1. For each input question, reformulate it to be more comprehensive and document-specific
2. Combine the main topic {TOPIC} with the section-specific questions
3. Ensure each question is distinct and provides a clear framework for extracting detailed responses
4. Organize questions by sections in a logical sequence
**Example Transformation**:
Input:
```
Background and Significance - What is spin and catalyst?
Background and Significance - What is its industrial significance?
```
Should be transformed to:
```
Background and Significance - What are the core principles of spin and catalyst as described in the document?
Background and Significance - How has spin and catalyst impacted the industry according to the document?
```
**Output Requirements**:
English output in JSON format as follows:
```json
{{
  "outlines": [
    {{
      "id": 1,
      "section": "Section Name",
      "contents": ["Question 1", "Question 2", "Question 3"]
    }},
    {{
      "id": 2,
      "section": "Section Name",
      "contents": ["Question 1", "Question 2", "Question 3"]
    }}
  ]
}}
```
**JSON Format Requirements:**
- The response must be a valid JSON object
- Use the exact key names: "outlines", "id", "section", "contents"
- Each outline item must have a unique sequential id (1, 2, 3, ...)
- The "contents" field should contain the detailed question
- The "section" field should indicate the thematic category
- Ensure proper JSON syntax with correct quotation marks and commas
<file-attachment-contents filename='"""
    print('PaperQuestionsFromParagraphQuestionsForReview')
    shutil.copy(f'AllQuestionsFromReview{os.sep}QuestionsFromReviewManual.txt',
                f'..{os.sep}ParagraphQuestionsForReview.txt')
    os.makedirs('PaperQuestionsFromParagraphQuestionsForReview', exist_ok=True)
    if not os.path.exists(f"PaperQuestionsFromParagraphQuestionsForReview{os.sep}QuestionsFromReview_0.txt"):
        ReviewOutline = open(f"AllQuestionsFromReview{os.sep}QuestionsFromReviewManual.txt", 'r',
                             encoding='UTF8').read()
        Prompt = PaperQuestionsFromParagraphQuestionsForReview + 'ReviewOutline.txt>\n' + ReviewOutline + '\n</file-attachment-contents>'
        open(
            f'PaperQuestionsFromParagraphQuestionsForReview{os.sep}PromptPaperQuestionsFromParagraphQuestionsForReview.txt',
            'w', encoding='UTF8').write(Prompt)
        REPEAT = 1
        Questions = ''
        max_attempts = 5
        current_attempt = 0
        while (len([i for i in Questions.splitlines() if i.strip()]) != len(
                [i for i in ReviewOutline.splitlines() if i.strip()])) and current_attempt < max_attempts:
            current_attempt += 1
            responses = GetResponse([['PaperQuestionsFromParagraphQuestionsForReview', Prompt]], REPEAT, Threads,
                                    FunctionClaudeAPI, FunctionOpenAIAPI, STDOUT, MaxToken=MaxToken,JsonCheck=True)
            try:
                with open(f'PaperQuestionsFromParagraphQuestionsForReview{os.sep}QuestionsFromReview_0.txt', 'r',
                          encoding='UTF8') as File:
                    Questions = ReshapeOutlines(File.read())
                questions_count = len([i for i in Questions.splitlines() if i.strip()])
                outline_count = len([i for i in ReviewOutline.splitlines() if i.strip()])
            except Exception as e:
                print(f"处理问题时出错: {e}")
        if Questions.strip() and questions_count==outline_count:
            pass
        else:
            print("无法生成匹配的问题，创建基本问题列表")
            outline_lines = [line.strip() for line in ReviewOutline.splitlines() if line.strip()]
            Questions = "\n".join([f"{i + 1}. {TOPIC} - {line}" for i, line in enumerate(outline_lines[:20])])
        with open(f'..{os.sep}QuestionsForReview.txt', 'w', encoding='UTF8') as File:
            File.write(Questions)
    os.chdir('..')
    sys.stdout = old_stdout
def Main3(Folder, TOPIC, Threads, FunctionClaudeAPI, FunctionOpenAIAPI, STDOUT, MaxToken=25000):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    TitlesFromParagraphQuestionsForReview = f"""Utilizing the document provided, transform the structured questions related to {TOPIC} into comprehensive declarative section titles suitable for a review article. These titles should serve as clear, informative headings that capture the essence of each section's content while naturally weaving the main topic of {TOPIC} into the narrative flow.
**Input Format**: You will receive questions in the format:
```
Section Name - Question content
Section Name - Question content
```
**Task**: Transform these input questions into declarative statements that can serve as section titles.
**CRITICAL REQUIREMENT**: Instead of simply adding "{TOPIC}" as a prefix, naturally integrate the concepts and terminology of {TOPIC} into the title structure to create cohesive, contextually rich section headings that flow naturally.
**Integration Strategy**: 
1. **Contextual Fusion**: Weave {TOPIC} concepts into the title's meaning rather than just adding it as a label
2. **Natural Language Flow**: Ensure titles read smoothly and professionally without forced terminology insertion
3. **Conceptual Integration**: Connect the question's content with {TOPIC} in a way that enhances understanding
4. **Technical Precision**: Use {TOPIC}-specific terminology where it naturally fits and adds value
**Process**: 
1. For **each** input question, convert it from interrogative to declarative form
2. **Naturally weave {TOPIC} concepts and terminology** into the title structure
3. Ensure each title is comprehensive and captures the full scope of the original question
4. Maintain the technical depth while making titles readable and informative
5. Organize titles by sections in a logical sequence
6. Remove question words (What, How, Why, etc.) and rephrase as statements
7. **Integrate {TOPIC} contextually rather than as a simple prefix**
**CRITICAL REQUIREMENT**:
Convert one by one without any omission, skipping or merging. All entries should correspond exactly.
**Example Transformation** (assuming TOPIC is "spin and catalyst"):
Input:
```
Background and Significance - What is spin and catalyst?
Background and Significance - What is its industrial significance?
```
Should be transformed to:
```
Background and Significance - Spin Effects in Heterogeneous Catalysis: Fundamental Principles and Mechanistic Insights
Background and Significance - Industrial Applications and Economic Impact of Heterogeneous Catalytic Processes
```
**NOT like this (avoid simple prefix addition):**
```
Background and Significance - spin and catalyst: What is spin and catalyst
Background and Significance - spin and catalyst: Industrial significance
```
**Output Requirements**:
English output in JSON format as follows:
```json
{{
  "outlines": [
    {{
      "id": 1,
      "section": "Section Name",
      "contents": ["Title 1", "Title 2", "Title 3"]
    }},
    {{
      "id": 2,
      "section": "Section Name", 
      "contents": ["Title 1", "Title 2", "Title 3"]
    }}
  ]
}}
```
**JSON Format Requirements:**
- The response must be a valid JSON object
- Use the exact key names: "outlines", "id", "section", "contents"
- Each outline item must have a unique sequential id (1, 2, 3, ...)
- The "contents" field should contain the declarative section titles
- The "section" field should indicate the thematic category
- Ensure proper JSON syntax with correct quotation marks and commas
- Maintain a one-to-one correspondence with the original outline
**Title Style Guidelines:**
- Use declarative, assertive language
- **Naturally weave {TOPIC} concepts and terminology** into the title structure
- **Avoid simple prefix addition** - integrate contextually instead
- Include key technical terms and concepts from both the question and {TOPIC}
- Maintain academic tone appropriate for review articles
- Ensure titles are informative and comprehensive
- Create smooth, professional language flow
- **Build conceptual bridges** between the original question content and {TOPIC}
- Use {TOPIC}-specific terminology where it enhances clarity and precision
- Maintain a one-to-one correspondence with the original outline
<file-attachment-contents filename='"""
    print('TitlesFromParagraphQuestionsForReview')
    os.makedirs('TitlesFromParagraphQuestionsForReview', exist_ok=True)
    if not os.path.exists(f"TitlesFromParagraphQuestionsForReview{os.sep}QuestionsFromReview_0.txt"):
        try:
            ReviewQuestions = open(f"AllQuestionsFromReview{os.sep}QuestionsFromReview_0.txt", 'r', encoding='UTF8').read()
            ReviewQuestionsManual = open(f"AllQuestionsFromReview{os.sep}QuestionsFromReviewManual.txt", 'r', encoding='UTF8').read()
        except FileNotFoundError:
                os.chdir('..')
                sys.stdout = old_stdout
                return
        Prompt = TitlesFromParagraphQuestionsForReview + 'ReviewQuestions.txt>\n' + ReviewQuestions + '\n</file-attachment-contents>'
        open(
            f'TitlesFromParagraphQuestionsForReview{os.sep}PromptTitlesFromParagraphQuestionsForReview',
            'w', encoding='UTF8').write(Prompt)
        REPEAT = 1
        Titles = ''
        max_attempts = 5
        current_attempt = 0
        while (len([i for i in Titles.splitlines() if i.strip()]) != len([i for i in ReviewQuestionsManual.splitlines() if i.strip()])) and current_attempt < max_attempts:
            current_attempt += 1
            responses = GetResponse([['TitlesFromParagraphQuestionsForReview', Prompt]], REPEAT, Threads,
                                    FunctionClaudeAPI, FunctionOpenAIAPI, STDOUT, MaxToken=MaxToken, JsonCheck=True)
            try:
                with open(f'TitlesFromParagraphQuestionsForReview{os.sep}QuestionsFromReview_0.txt', 'r',
                          encoding='UTF8') as File:
                    Titles = ReshapeOutlines(File.read())
                titles_count = len([i for i in Titles.splitlines() if i.strip()])
                questions_count = len([i for i in ReviewQuestionsManual.splitlines() if i.strip()])
            except Exception as e:
                print(f"处理标题时出错: {e}")
        if Titles.strip() and titles_count==questions_count:
            pass
        else:
            print("无法生成匹配的标题，创建基本标题列表")
            questions_lines = [line.strip() for line in ReviewQuestionsManual.splitlines() if line.strip()]
            basic_titles = []
            for i, line in enumerate(questions_lines):
                if ' - ' in line:
                    section, question = line.split(' - ', 1)
                    title = question.replace('?', '')
                    if 'What is' in title:
                        title = title.replace('What is', f'Fundamentals of').replace(' and ', f' in {TOPIC} and ')
                    elif 'How does' in title:
                        title = title.replace('How does', f'Mechanisms of').replace(' work', f' in {TOPIC} Systems')
                    elif 'Why' in title:
                        title = title.replace('Why', f'Rationale and Significance of').replace(' important', f' in {TOPIC}')
                    elif 'What are' in title:
                        title = title.replace('What are', f'Comprehensive Analysis of')
                        if TOPIC.lower() not in title.lower():
                            title = f"{title} in {TOPIC}"
                    else:
                        if TOPIC.lower() not in title.lower():
                            title = f"{title}: Perspectives from {TOPIC}"
                    basic_titles.append(f"{section} - {title}")
                else:
                    title = line.replace('?', '')
                    if TOPIC.lower() not in title.lower():
                        title = f"{title} in {TOPIC} Context"
                    basic_titles.append(title)
            Titles = "\n".join([f"{i + 1}. {title}" for i, title in enumerate(basic_titles)])
        with open(f'..{os.sep}TitlesForReview.txt', 'w', encoding='UTF8') as File:
            File.write(Titles)
        with open(f'TitlesFromParagraphQuestionsForReview{os.sep}TitlesFromReviewManual.txt', 'w', encoding='UTF8') as File:
            File.write(Titles)
    os.chdir('..')
    sys.stdout = old_stdout
