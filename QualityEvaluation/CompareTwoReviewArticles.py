import os
import re
import sys
import time
import tqdm
import json
import openai
import func_timeout
import xml.etree.ElementTree as ET
from itertools import permutations
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
def GetResponseFromOpenAlClient(Prompt,url=URL,key=KEY,model=MODEL):
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
HEAD = '''You are a professional literature review expert. Your task is to evaluate and compare two review articles on the topic of "'''
MIDDLE0 = '''" based on the provided scoring criteria. Please carefully read the following instructions and scoring criteria, then evaluate the two provided articles.
The scoring criteria are as follows:
{
  "Content Quality": {
    "Topic Relevance": {
      "Description": "Relevance and importance to the topic",
      "Maximum Score": 8
    },
    "Comprehensiveness of Information": {
      "Description": "Breadth and depth of topic coverage",
      "Maximum Score": 8
    },
    "Accuracy of Information": {
      "Description": "Correctness of data and statements",
      "Maximum Score": 8
    },
    "Innovativeness of Viewpoints": {
      "Description": "Novel insights and unique perspectives",
      "Maximum Score": 8
    },
    "Integration of Interdisciplinary Perspectives": {
      "Description": "Degree of multidisciplinary knowledge integration",
      "Maximum Score": 8
    }
  },
  "Structure and Organization": {
    "Clarity of Logical Structure": {
      "Description": "Coherence of argumentation process",
      "Maximum Score": 10
    },
    "Reasonableness of Chapter Arrangement": {
      "Description": "Balance and sequence of content distribution",
      "Maximum Score": 8
    },
    "Quality of Introduction and Conclusion": {
      "Description": "Effectiveness of opening and closing",
      "Maximum Score": 7
    }
  },
  "Academic Standards": {
    "Accuracy and Completeness of Citations": {
      "Description": "Correctness of citation format and content",
      "Maximum Score": 10
    },
    "Timeliness and Relevance of References": {
      "Description": "Recency and relevance of literature",
      "Maximum Score": 8
    },
    "Avoidance of Plagiarism and Appropriate Citation": {
      "Description": "Originality and appropriateness of citations",
      "Maximum Score": 7
    }
  },
  "Innovation and Contribution": {
    "Critical Analysis of Existing Research": {
      "Description": "Depth of analysis and insight",
      "Maximum Score": 8
    },
    "Proposal of New Research Directions or Questions": {
      "Description": "Foresight and inspirational quality",
      "Maximum Score": 9
    },
    "Potential Contribution to the Field": {
      "Description": "Degree of theoretical or practical advancement",
      "Maximum Score": 8
    }
  },
  "Methodology Assessment": {
    "Clarity of Research Method Description": {
      "Description": "Clarity of methodological explanation",
      "Maximum Score": 7
    },
    "Rationality of Method Selection": {
      "Description": "Match between method and research question",
      "Maximum Score": 7
    },
    "Rigor of Research Design": {
      "Description": "Scientific nature and reliability of design",
      "Maximum Score": 6
    }
  },
  "Timeliness and Cutting-edge Nature": {
    "Inclusion of Latest Research Results": {
      "Description": "Degree of citation of latest literature",
      "Maximum Score": 8
    },
    "Reflection of Current Research Hotspots": {
      "Description": "Coverage of hot issues",
      "Maximum Score": 7
    }
  },
  "Writing Quality": {
    "Fluency of Language Expression": {
      "Description": "Smooth writing, easy to understand",
      "Maximum Score": 5
    },
    "Appropriateness of Professional Terminology Use": {
      "Description": "Accuracy and consistency of terminology use",
      "Maximum Score": 5
    },
    "Conciseness of Expression": {
      "Description": "Degree of language refinement",
      "Maximum Score": 5
    }
  },
  "Practicality and Application Value": {
    "Practical Application Potential of Research Results": {
      "Description": "Guiding significance for practice",
      "Maximum Score": 8
    },
    "Feasibility of Proposed Suggestions": {
      "Description": "Realism and operability of suggestions",
      "Maximum Score": 7
    }
  },
  "Critical Thinking": {
    "Logic of Argumentation": {
      "Description": "Rationality of reasoning process",
      "Maximum Score": 7
    },
    "Multi-angle Analysis of Problems": {
      "Description": "Diversity and comprehensiveness of perspectives",
      "Maximum Score": 7
    },
    "Identification and Discussion of Research Limitations": {
      "Description": "Recognition and analysis of limiting factors",
      "Maximum Score": 6
    }
  }
}
Please follow these steps for the evaluation:
1. Carefully read the two provided review articles.
2. Score each article based on every evaluation dimension and specific item in the scoring criteria.
3. Provide a concise scoring rationale for each point, and indicate the strengths and weaknesses of both articles.
4. Calculate the overall score for each article.
5. Determine which review is superior based on the overall scores and analysis.
6. Output the evaluation results in the specified JSON format.
During the evaluation process, please note the following:
- Maintain objectivity: Base your evaluation on facts and article content, avoiding subjective bias.
- Provide concise scoring rationales: Summarize the basis for scoring in brief sentences or phrases.
- Consider disciplinary characteristics: Judge the quality and contribution of the reviews based on the characteristics of their respective disciplines.
- Note subtle differences: Even if the overall quality is similar, strive to identify and articulate the differences between the two articles.
- Weigh pros and cons: When drawing final conclusions, consider performance across all dimensions comprehensively.
<file-attachment-contents filename="Review A.txt"> 
'''
MIDDLE1='''
</file-attachment-contents>
<file-attachment-contents filename="Review B.txt"> 
'''
END = """
</file-attachment-contents>
Please output the evaluation results in the following JSON format:
{
  "Content Quality": {
    "Topic Relevance": {
      "Requirement": "Relevance and importance to the topic",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Comprehensiveness of Information": {
      "Requirement": "Breadth and depth of topic coverage",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Accuracy of Information": {
      "Requirement": "Correctness of data and statements",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Innovativeness of Viewpoints": {
      "Requirement": "Novel insights and unique perspectives",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Integration of Interdisciplinary Perspectives": {
      "Requirement": "Degree of multidisciplinary knowledge integration",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    }
  },
  "Structure and Organization": {
    "Clarity of Logical Structure": {
      "Requirement": "Coherence of argumentation process",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Reasonableness of Chapter Arrangement": {
      "Requirement": "Balance and sequence of content distribution",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Quality of Introduction and Conclusion": {
      "Requirement": "Effectiveness of opening and closing",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    }
  },
  "Academic Standards": {
    "Accuracy and Completeness of Citations": {
      "Requirement": "Correctness of citation format and content",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Timeliness and Relevance of References": {
      "Requirement": "Recency and relevance of literature",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Avoidance of Plagiarism and Appropriate Citation": {
      "Requirement": "Originality and appropriateness of citations",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    }
  },
  "Innovation and Contribution": {
    "Critical Analysis of Existing Research": {
      "Requirement": "Depth of analysis and insight",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Proposal of New Research Directions or Questions": {
      "Requirement": "Foresight and inspirational quality",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Potential Contribution to the Field": {
      "Requirement": "Degree of theoretical or practical advancement",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    }
  },
  "Methodology Assessment": {
    "Clarity of Research Method Description": {
      "Requirement": "Clarity of methodological explanation",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Rationality of Method Selection": {
      "Requirement": "Match between method and research question",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Rigor of Research Design": {
      "Requirement": "Scientific nature and reliability of design",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    }
  },
  "Timeliness and Cutting-edge Nature": {
    "Inclusion of Latest Research Results": {
      "Requirement": "Degree of citation of latest literature",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Reflection of Current Research Hotspots": {
      "Requirement": "Coverage of hot issues",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    }
  },
  "Writing Quality": {
    "Fluency of Language Expression": {
      "Requirement": "Smooth writing, easy to understand",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Appropriateness of Professional Terminology Use": {
      "Requirement": "Accuracy and consistency of terminology use",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Conciseness of Expression": {
      "Requirement": "Degree of language refinement",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    }
  },
  "Practicality and Application Value": {
    "Practical Application Potential of Research Results": {
      "Requirement": "Guiding significance for practice",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Feasibility of Proposed Suggestions": {
      "Requirement": "Realism and operability of suggestions",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    }
  },
  "Critical Thinking": {
    "Logic of Argumentation": {
      "Requirement": "Rationality of reasoning process",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Multi-angle Analysis of Problems": {
      "Requirement": "Diversity and comprehensiveness of perspectives",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    },
    "Identification and Discussion of Research Limitations": {
      "Requirement": "Recognition and analysis of limiting factors",
      "Scoring Rationale": "",
      "Review A Score": 0,
      "Review B Score": 0,
      "Superior Article": ""
    }
  },
  "Overall Evaluation": {
    "Review A Total Score": 0,
    "Review B Total Score": 0,
    "Superior Review": "",
    "Summary": ""
  }
}
In your output, please ensure:
1. The scoring rationale for each point is concise yet substantive, not exceeding 20 words.
2. Scores are precise to one decimal place and show differentiation.
3. Indicate the superior article for each scoring point (output "A" or "B", if scores are equal, mark as "AB").
4. The total score is the sum of all scoring point scores.
5. Provide a brief comparison and conclusion in the overall evaluation, explaining why one review is superior, not exceeding 50 words.
When evaluating, please note:
- Maintain objectivity and conciseness.
- Provide accurate scores based on the content of the articles.
- Only provide the most critical observations or judgments in the scoring rationales.
- When comparing the two articles, focus on their significant differences.
Now, please begin your evaluation work. Remember, your goal is to provide a concise yet comprehensive comparison, highlighting the key differences between the two reviews.
"""
def replace_with_html_entities(text):
    entities = {
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
def extract_sections_with_tags(content):
    english_matches = re.findall(r"<English>(.*?)</English>", content, re.DOTALL)
    chinese_matches = re.findall(r"<Chinese>(.*?)</Chinese>", content, re.DOTALL)
    reference_matches = re.findall(r"<References>(.*?)</References>", content, re.DOTALL)
    reference_matches = reference_matches if reference_matches else re.findall(r"<Reference>(.*?)</Reference>", content, re.DOTALL)
    return '\n'.join(english_matches), '\n'.join(chinese_matches), '\n'.join(reference_matches)
def GetResponseConcurrent(prompts, Threads, STDOUT):
    prompt_queue = Queue()
    for item in prompts:
        prompt_queue.put(item)
    semaphore1 = Semaphore(value=0)
    semaphore2 = Semaphore(value=26)
    progress_bar = tqdm.tqdm(total=len(prompts), position=0, desc='CompareTwoReviewArticles', file=STDOUT)
    def worker():
        while True:
            try:
                i, folder,Repeat, part, prompt = prompt_queue.get_nowait()
            except Empty:
                break
            if os.path.exists(os.path.join(f'CompareParagraph', f'Comparison{Repeat}_{part}.txt')):
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
                        response = GetResponseFromOpenAlClient(prompt)
                        semaphore2.release()
                    else:
                        open('Waitlog', 'a').write('\t'.join([str(i), folder, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()), 'waiting\n']))
                        time.sleep(0.5)
                        continue
                    try:
                        json_response = json.loads(response)
                        if not all(key in json_response for key in ["Content Quality", "Structure and Organization", "Academic Standards", "Overall Evaluation"]):
                            raise ValueError("Invalid JSON structure")
                    except (json.JSONDecodeError, ValueError):
                        open(os.path.join(f'CompareParagraph', f'Comparison{Repeat}_{part}_{TRY}.txt'), 'w', encoding='UTF8').write(response + '\n')
                        TRY += 1
                        continue
                    with open(os.path.join(f'CompareParagraph', f'Comparison{Repeat}_{part}.txt'), 'w', encoding='UTF8') as file:
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
def Main(Folder, Threads,REPEAT, STDOUT):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    os.makedirs('CompareParagraph',exist_ok=True)
    ParagraphQuestionsForReview = [i.strip() for i in open('../../ParagraphQuestionsForReview', 'r', encoding='UTF8').readlines() if i.strip()]
    paragraph_files = [f for f in os.listdir() if re.match(r"Paragraph\d+_\d+\.txt", f) and not re.match(r"Paragraph\d+_\d+_\d+\.txt", f)]
    paragraph_files.sort()
    comparisons = [i for i in permutations(paragraph_files, 2) if i[0].split('_')[0]==i[1].split('_')[0]]
    prompts = []
    for i, (file1, file2) in enumerate(comparisons):
        with open(file1, 'r', encoding='UTF8') as f1, open(file2, 'r', encoding='UTF8') as f2:
            content1 = f1.read().strip().replace('※※※','')
            content1= "\n".join(re.findall(r"<English>(.*?)</English>",content1, re.DOTALL)).strip() if "\n".join(re.findall(r"<English>(.*?)</English>",content1, re.DOTALL)).strip() else content1
            content2 = f2.read().strip().replace('※※※','')
            content2= "\n".join(re.findall(r"<English>(.*?)</English>",content2, re.DOTALL)).strip() if "\n".join(re.findall(r"<English>(.*?)</English>",content2, re.DOTALL)).strip() else content2
        question_index = int(re.search(r"Paragraph(\d+)_", file1).group(1)) - 1
        prompt = replace_with_html_entities(HEAD + ParagraphQuestionsForReview[question_index] + MIDDLE0 + content1 + MIDDLE1 + content2 + END)
        comparison_id = f"{file1.split('.')[0]}@{file2.split('.')[0]}"
        open(f'CompareParagraph{os.sep}PromptCompare{comparison_id}.txt', 'w', encoding='UTF8').write(prompt)
        for Repeat in range(REPEAT):
            prompts.append((i, Folder,Repeat, comparison_id, prompt))
    GetResponseConcurrent(prompts, Threads, STDOUT)
    os.chdir('..')
    sys.stdout = old_stdout
if __name__ == "__main__":
    Main(f'Answer{os.sep}Paragraph',26,5,sys.stdout)
