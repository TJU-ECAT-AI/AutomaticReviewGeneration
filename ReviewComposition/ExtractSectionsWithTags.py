import os
import json
import sys
def Main(Folder, STDOUT):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    ParagraphQuestionsForReview = [i.strip() for i in
                                   open('../../TitlesForReview.txt', 'r', encoding='UTF8').readlines() if
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
        try:
            with open(os.path.join(current_directory, txt_file), "r", encoding="utf-8") as file:
                best_content = file.read()
                try:
                    json_content = '{' + best_content.split('{',1)[-1].rsplit('}',1)[0] + '}'
                    try:
                        json_data = json.loads(json_content)
                    except json.JSONDecodeError:
                        json_data = json.loads(json_content[:-1])
                    if 'best_paragraph_ID' in json_data:
                        best_paragraph_id = json_data['best_paragraph_ID']
                        if int(best_paragraph_id)<0 or int(best_paragraph_id)>9:
                            best_paragraph_id=0
                        paragraph_file = f'..{os.sep}Paragraph{os.sep}Paragraph{Index}_{best_paragraph_id}.txt'
                        try:
                            with open(os.path.join(current_directory, paragraph_file), "r", encoding="utf-8") as para_file:
                                paragraph_content = para_file.read()
                                try:
                                    para_json_content = '{' + paragraph_content.split('{',1)[-1].rsplit('}',1)[0] + '}'
                                    try:
                                        para_json_data = json.loads(para_json_content)
                                    except json.JSONDecodeError:
                                        para_json_data = json.loads(para_json_content[:-1])
                                    if 'Content' in para_json_data and 'References' in para_json_data:
                                        extracted_content = para_json_data['Content']
                                        extracted_content_DOI = para_json_data['References']
                                        All += "\n".join([f'{Index}. ' + ParagraphQuestionsForReview[Index - 1], 
                                                         extracted_content, 
                                                         '\nDOI:', 
                                                         '\n'.join(extracted_content_DOI)]) + "\n\n"
                                    else:
                                        print(f"Warning: No 'Content' or 'References' found in {paragraph_file}")
                                except json.JSONDecodeError as e:
                                    print(f"Error parsing JSON in {paragraph_file}: {e}")
                        except FileNotFoundError:
                            print(f"Error: Paragraph file {paragraph_file} not found")
                        except Exception as e:
                            print(f"Error processing {paragraph_file}: {e}")
                    else:
                        print(f"Warning: No 'best_paragraph_ID' found in {txt_file}")
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON in {txt_file}: {e}")
        except FileNotFoundError:
            print(f"Error: File {txt_file} not found")
        except Exception as e:
            print(f"Error processing {txt_file}: {e}")
    try:
        with open('draft.txt', "w", encoding="utf-8") as file:
            file.write(All)
    except Exception as e:
        print(f"Error writing draft.txt: {e}")
    os.chdir('../..')
    sys.stdout = old_stdout
