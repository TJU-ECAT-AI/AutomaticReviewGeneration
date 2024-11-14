from elsapy.elsclient import ElsClient
from elsapy.elsdoc import FullDoc
import os
import re
import shutil
def Main(Folder,apikey=None):
    if apikey is None:
        apikey = 'none'
    ElsevierClient = ElsClient(apikey)
    os.chdir(Folder)
    os.makedirs('Answer',exist_ok=True)
    os.chdir('Answer')
    source_dir = ".."
    target_dir = ""
    file_pattern = re.compile(r"AnswerWithRelevanceCheck\.PART\d+\.txt$")
    search_string = "※※※The provided answers are not relevant to the questions.※※※"
    files_to_link = []
    for subdir in os.listdir(source_dir):
        if subdir.startswith("10.") and os.path.isdir(os.path.join(source_dir, subdir)):
            for file in os.listdir(os.path.join(source_dir, subdir)):
                if file_pattern.match(file):
                    file_path = os.path.join(source_dir, subdir, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if search_string not in content:
                            files_to_link.append(file_path)
    created_links_corrected = []
    for file_path in files_to_link:
        part_match = re.search(r"PART(\d+)\.txt$", os.path.basename(file_path))
        if part_match:
            part_folder = f"PART{part_match.group(1)}"
            target_folder = os.path.join(target_dir, part_folder)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            prefix = os.path.basename(os.path.dirname(file_path))
            if prefix.startswith('10._pii_S'):
                doc = FullDoc(sd_pii=prefix.replace('10._pii_',''))
                doc.read(ElsevierClient)
                prefix=doc.int_id.replace('/','_')
            symlink_name = f"{prefix}.{os.path.basename(file_path)}"
            target_path = os.path.join(target_folder, symlink_name)
            adjusted_file_path = os.path.join(".", file_path)
            shutil.copy(adjusted_file_path, target_path)
            created_links_corrected.append(target_path)
    os.chdir('..')
    os.chdir('..')
