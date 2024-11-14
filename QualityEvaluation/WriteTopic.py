import json
import os
TopicAndQuestion=json.load(open('TopicAndQuestion.json','r'))
for i in [i for i in os.listdir() if i.startswith('10.')]:
  open(f'{i}{os.sep}QuestionsForReview','w',encoding='utf-8').write(TopicAndQuestion[i]['QuestionEnglish'])
  open(f'{i}{os.sep}ParagraphQuestionsForReview','w',encoding='utf-8').write(TopicAndQuestion[i]['topic'])
