import os
import re
import sys
import xml.etree.ElementTree as ET
import json
import traceback
def wrap_specific_tags_with_cdata(tag_name, content):
    tag_pattern = f'<{tag_name}>(.*?)</{tag_name}>'
    replacement = f'<{tag_name}><![CDATA[\\1]]></{tag_name}>'
    return re.sub(tag_pattern, replacement, content, flags=re.DOTALL)
def Main(Folder,STDOUT):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    tags_to_wrap = ["Quotes", "English", "Chinese"]
    chunk_size=7
    AllErrorList=[]
    PARTS=[i for i in os.listdir('.') if i.startswith('PART')]
    RemoveCommands=[]
    for PART in PARTS:
        os.chdir(PART)
        ErrorList=[]
        for Name in [i for i in os.listdir('.') if i.startswith('10.') and i.endswith('.txt')]:
            DOI=re.sub(r'_', '/', Name.split('.AnswerWithRelevanceCheck.PART')[0], count=1).replace('_Review','')
            content=open(f"{Name}", "r", encoding="utf-8").read().strip()
            content='<?xml version="1.0" encoding="UTF-8"?>\n<Questions>\n'+content.split('<Questions>')[-1]
            content=content=content.split('</Questions>')[0]+'\n</Questions>'
            for tag in tags_to_wrap:
                content = wrap_specific_tags_with_cdata(tag, content.strip())
            try:
                root = ET.fromstring(content)
                Questions={i.items()[0][1]:i for i in root.findall('Question')}            
                OutOfRange=[i for i in Questions.keys() if i not in [str(j) for j in [*range(int(PART.removeprefix('PART'))*chunk_size+1,int(PART.removeprefix('PART'))*chunk_size+chunk_size+1),*range(chunk_size+1)]]]
                [os.makedirs(i, exist_ok=True) for i in [str(i) for i in range(1,chunk_size+1)]]
                if OutOfRange:
                    print(Name,'OUT OF RANGE.',Questions.keys(),OutOfRange,sep='\t')
                    ErrorList.append(Name)
                for i in Questions.keys():
                    if i not in OutOfRange:
                        Folder=i
                        if i not in [str(i) for i in range(chunk_size+1)]:
                            Folder=f"{int(i)-int(PART.removeprefix('PART'))*chunk_size}"
                        Answer={j:Questions[i].findall(j)[0].text if Questions[i].findall(j) else '' for j in ['Quotes','English','Chinese'] }
                        Answer={k:(v.strip() if v else '') for k,v in Answer.items()}
                        Answer.update({'Doi':DOI})
                        NoChineseAnswer={j:Questions[i].findall(j)[0].text if Questions[i].findall(j) else '' for j in ['Quotes','English',] }
                        NoChineseAnswer={k:(v.strip() if v else '') for k,v in NoChineseAnswer.items()}
                        NoChineseAnswer.update({'Doi':DOI})
                        [open(f'{Folder}{os.sep}{j}.txt','a', encoding="utf-8").write(Answer[j]+'\n\n') for j in ['Quotes','English','Chinese'] ]
                        open(f'{Folder}{os.sep}All.txt','a', encoding="utf-8").write(json.dumps(Answer,ensure_ascii=False)+',\n')
                        open(f'{Folder}{os.sep}EnglishWithQuotes.txt','a', encoding="utf-8").write(json.dumps(NoChineseAnswer,ensure_ascii=False)+',\n')
            except ET.ParseError :
                print(Name, 'FAILED.',sep='\t')
                print(traceback.format_exc())
                ErrorList.append(Name)
        if ErrorList:
            RemoveCommands.append(f"for i in {{{','.join(ErrorList)}}};do rm {PART}{os.sep}`readlink {PART}{os.sep}$i`;done")
            AllErrorList.extend(ErrorList)
        os.chdir('..')
    print('\nSplited Into Folders.')
    if AllErrorList:
        print('\nErrorList:')
        print('\n'.join(AllErrorList))
        print('\n')
        print('\n'.join(RemoveCommands))
    os.chdir('..')
    os.chdir('..')
    sys.stdout = old_stdout
if __name__ == "__main__":
    Main('Answer',sys.stdout)
