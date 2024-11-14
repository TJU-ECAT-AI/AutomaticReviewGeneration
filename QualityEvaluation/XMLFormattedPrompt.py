import os
import re
import json
import tiktoken
import math
TrainFolders=[i for i in os.listdir('RawFromPDF') if i.startswith('10')]
file_path_prompt16 = os.path.join('.', 'QuestionsForReview')
FormattedPromptHead='''I'm going to give you a scientific literature. Then I'm going to ask you some questions about it. I'd like you to first write down exact quotes of parts of the document word by word that would help answer the question, and then I'd like you to answer the question using facts from the quoted content. Do not omit any relevant information from the text, and avoid introducing any falsehoods or assumptions that aren't directly supported by the literature. Here is the literature, in <literature></literature> XML tags:
<literature>
'''
FormattedPromptMiddle='''
</literature>
Here are the question lists, in <questions></questions>XML tags:
<questions>
'''
FormattedPromptEnd='''
</questions>
First, you need to sequentially extract any quotes in the literature that are most relevant to each question, and print them in numbered order, separated by newlines. Quotes should be relatively brief. Do not attempt to summarize or answer questions at this stage, but simply repeat exactly what the corresponding part of the literature says.
Please enclose the full list of quotes in <quotes></quotes> XML tags. If there are no relevant quotes, write "No relevant quotes" instead.
Then, answer the question, starting with "Answer:".  Do not include or reference quoted content verbatim in the answer. Don't say "According to Quote [1]" when answering. Do not write reference number of quotes after answer. Put your answer to the user inside <EnglishVersionAnswer></EnglishVersionAnswer> XML tags. Output formatted text, with line breaks for each question.Separate quotes and answers with a blank line. Provide the answers to all questions in English. After completing the English answers, translate all those answers into Chinese and provide the Chinese version inside <ChineseVersionAnswer></ChineseVersionAnswer> XML tags.
Thus, the format of your overall response should look like what's shown between the <example></example> tags.  Make sure to follow the formatting and spacing exactly.
<example>
<quotes>
[1] "Company X reported revenue of $12 million in 2021."
</quotes>
<EnglishVersionAnswer>
1.Company X earned $12 million in 2021.
</EnglishVersionAnswer>
<ChineseVersionAnswer>
1.X公司在2021年赚了1200万美元。
</ChineseVersionAnswer>
<quotes>
[1] "Almost 90% of revenue came from widget sales, with gadget sales making up the remaining 10%."
</quotes>
<EnglishVersionAnswer>
2.Almost 90% of it came from widget sales.
</EnglishVersionAnswer>
<ChineseVersionAnswer>
2.几乎90%的收入来自小部件销售。
</ChineseVersionAnswer>
</example>
If the question cannot be answered by the document, say so.If deemed necessary, the answer to the question can be extended entirely from the content of the document.
Answer all of the questions immediately without preamble. '''
TitlePattern = r'^[^a-zA-Z0-9\u4e00-\u9FFF\s]*\s*(' + '|'.join([
                                'ACKNOWLEDGMENT',
                                'ACKNOWLEDGEMENT',
                                'SUPPLEMENTARY MATERIAL',
                                'REFERENCE',
                                'References',
                                'DATA AVAILABILITY',
                                'Declaration of competing interest',
                                'ABBREVIATIONS',
                                'ASSOCIATED CONTENT',
                                'Conflicts of interest',
                                'Supporting Information',
                                ]) + ')'
InvaildSymbolPattern = r"[^a-zA-Z0-9\u4e00-\u9fa5\u0370-\u03FF ,.!?\-_:;'\"(){}\[\]&<>%\$@\*/=#·Å+•×\\]"
def MergeParagraphs(text):
    ending_punctuation = '.!?。！？'
    paired_punctuation = {
        '(': ')', '[': ']', '{': '}', '<': '>', 
        '（': '）', '【': '】', '《': '》', '「': '」', '『': '』',
        '"': '"', "'": "'", '`': '`'
    }
    all_opening = ''.join(paired_punctuation.keys())
    all_closing = ''.join(paired_punctuation.values())
    lines = text.split('\n')
    processed_lines = []
    current_paragraph = ""
    in_special_structure = False
    special_structure_lines = []
    punctuation_stack = []
    def is_sentence_end(s):
        return (s and s[-1] in ending_punctuation and 
                (len(punctuation_stack) == 0 or punctuation_stack[-1] in ['"', '"', ''', ''']))
    def is_heading(line):
        return (re.match(r'^#{1,6}\s', line) or
                re.match(r'^[A-Z0-9\u4e00-\u9fa5]{1,20}[.、:：]', line) or
                (len(line) <= 40 and line.isupper())
                ) 
    for line in lines:
        line = line.strip()
        if re.match(r'^[-+|]{3,}$', line) or re.match(r'^```', line):
            in_special_structure = not in_special_structure
            if in_special_structure:
                if current_paragraph:
                    processed_lines.append(current_paragraph)
                    current_paragraph = ""
                special_structure_lines = [line]
            else:
                processed_lines.extend(special_structure_lines)
                special_structure_lines = []
            continue
        if in_special_structure:
            special_structure_lines.append(line)
            continue
        if line:
            for char in line:
                if char in all_opening:
                    punctuation_stack.append(char)
                elif char in all_closing:
                    if punctuation_stack and paired_punctuation[punctuation_stack[-1]] == char:
                        punctuation_stack.pop()
            if is_heading(line):
                if current_paragraph:
                    processed_lines.append(current_paragraph)
                processed_lines.append(line)
                current_paragraph = ""
                punctuation_stack.clear()
            else:
                if (current_paragraph and 
                    is_sentence_end(current_paragraph) and
                    (line[0].isupper() or line[0] in all_opening)):
                    processed_lines.append(current_paragraph)
                    current_paragraph = line
                else:
                    if current_paragraph:
                        if (current_paragraph[-1] in ending_punctuation and line[0].isupper()) or \
                           (current_paragraph[-1] in ',:;，：；' and not line[0].isupper()):
                            current_paragraph += "\n" + line
                        else:
                            current_paragraph += " " + line
                    else:
                        current_paragraph = line
        else:
            if current_paragraph:
                processed_lines.append(current_paragraph)
                current_paragraph = ""
                punctuation_stack.clear()
    if current_paragraph:
        processed_lines.append(current_paragraph)
    return '\n\n'.join([i.replace('\n','').replace('. . . ','').replace('. . . ','').replace('. . . ','')  for i in processed_lines]).replace('. . . ','').replace('. . . ','').replace('. . . ','').replace('. . . ','').replace('. . . ','')
def GetRefineContents(Contents):
    for i in range(10):
        Contents=Contents.replace('. . . ','')
    Contents=Contents.replace('ﬀ', 'ff').replace('','fi').replace('ﬁ', 'fi').replace('ﬂ', 'fl').replace('ﬃ', 'ffi').replace('ﬄ', 'ffl').replace('ﬅ', 'ft').replace('ﬆ', 'st').split('\n')
    Contents=[re.sub(InvaildSymbolPattern, '', Content) for  Content in Contents]
    Final=[]
    threshold=320
    for x in Contents:
        if len(x) < threshold and re.match(TitlePattern, x.strip(), re.IGNORECASE) and Final:
            break
        else:
            Final.append(x)
    return MergeParagraphs('\n'.join(Final))
def get_encoding_for_model(model_name):
    """Returns the appropriate encoding for the specified model."""
    if model_name in ["gpt-4", "gpt-3.5-turbo", "text-embedding-ada-002"]:
        return "cl100k_base"
    elif model_name.startswith("text-davinci-002") or model_name.startswith("text-davinci-003"):
        return "p50k_base"
    elif model_name.startswith("davinci"):
        return "r50k_base"
    elif model_name.endswith("edit-001"):
        return "p50k_edit"
    else:
        raise ValueError(f"Unknown model: {model_name}")
def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens
def split_text(text, max_tokens):
    """Split text into chunks that don't exceed max_tokens while preserving paragraphs."""
    total_tokens = num_tokens_from_string(text)
    if total_tokens <= max_tokens:
        return [text]
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    current_tokens = 0
    for paragraph in paragraphs:
        paragraph_tokens = num_tokens_from_string(paragraph)
        if paragraph_tokens > max_tokens:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                sentence_tokens = num_tokens_from_string(sentence)
                if current_tokens + sentence_tokens > max_tokens and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                    current_tokens = sentence_tokens
                else:
                    current_chunk += sentence
                    current_tokens += sentence_tokens
        else:
            if current_tokens + paragraph_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
                current_tokens = paragraph_tokens
            else:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += paragraph
                current_tokens += paragraph_tokens
    if current_chunk:
        chunks.append(current_chunk.strip())
    if num_tokens_from_string(chunks[-2]+chunks[-1])<max_tokens*1.2:
        chunks=chunks[:-2]+[chunks[-2]+chunks[-1]]    
    return chunks
chunk_size=7
AllPrompt=[]
with open(file_path_prompt16, 'r') as f:
    content = [i for i in f.readlines() if i.strip()]
    SPLIT=False    
    if len(content)>chunk_size:
        SPLIT=True
        for i in range(0, len(content), chunk_size):
            AllPrompt.append('\n'.join(content[i:i+chunk_size]))
    else:
        AllPrompt.extend(content)
def GetDataList(folders, MaxToken):
    data_list = []
    for folder in folders:
        file_path_doc = f'RawFromPDF/{folder}'
        with open(file_path_doc,'r',encoding='utf8') as f:
            doc = GetRefineContents(f.read())
        prompt_framework = FormattedPromptHead + FormattedPromptMiddle + FormattedPromptEnd
        framework_tokens = num_tokens_from_string(prompt_framework)
        max_doc_tokens = MaxToken - framework_tokens
        doc_tokens = num_tokens_from_string(doc)
        if doc_tokens > max_doc_tokens:
            num_chunks = math.ceil(doc_tokens / max_doc_tokens)
            tokens_per_chunk = math.floor(doc_tokens / num_chunks)
            doc_chunks = split_text(doc, tokens_per_chunk)
        else:
            doc_chunks = [doc]
        for chunk_index, doc_chunk in enumerate(doc_chunks):
            for i, j in enumerate(AllPrompt):
                full_prompt = (FormattedPromptHead + '\n' + doc_chunk.strip().replace('\n\n', '\n') + 
                               '\n' + FormattedPromptMiddle + '\n' + j.strip().replace('\n\n', '\n') + 
                               '\n' + FormattedPromptEnd)
                output_filename = f'Prompt{folder}.PART{i}.CHUNK{chunk_index}'
                with open(output_filename, 'w',encoding='utf8') as f:
                    f.write(full_prompt)
GetDataList(TrainFolders,MaxToken=25000)
