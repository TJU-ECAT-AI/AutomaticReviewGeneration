import os
import re
import sys
def Main(Folder,STDOUT):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    ParagraphQuestionsForReview = [i.strip() for i in
                                   open('../../ParagraphQuestionsForReview.txt', 'r', encoding='UTF8').readlines() if
                                   i.strip()]
    current_directory = "."
    txt_files = [int(file.strip('.txt').replace('BestParagraph', '')) for file in os.listdir(current_directory)
                 if
                 file.endswith('.txt') and file.startswith('BestParagraph') and 'draft' not in file and '_' not in file]
    txt_files.sort()
    txt_files = [f'BestParagraph{i}.txt' for i in txt_files]
    All = ''
    for txt_file in txt_files:
        Index = int(txt_file.split('BestParagraph')[-1].split('.txt')[0])
        with open(os.path.join(current_directory, txt_file), "r", encoding="utf-8") as file:
            content = file.read()
            All += "\n".join([f'{Index}. ' + ParagraphQuestionsForReview[Index - 1]] +
                             re.findall(r"<Content>(.*?)</Content>", content, re.DOTALL)) + "\n\n"
    with open('draft.txt', "w", encoding="utf-8") as file:
        file.write(All)
    os.chdir('../..')
    sys.stdout = old_stdout
