import tkinter as tk
import tkinter.simpledialog
import io, re, os, sys, json, time, shutil, threading, traceback, functools, importlib, subprocess
RootDirectory = os.path.abspath('.')
os.makedirs('Temp', exist_ok=True)
os.chdir('Temp')
import Utility.License, Utility.GetResponse
import LiteratureSearch.One_key_download, MultiDownload.One_key_download
import TopicFormulation.GetQuestionsFromReview
import KnowledgeExtraction.XMLFormattedPrompt, KnowledgeExtraction.GetAllResponse, KnowledgeExtraction.AnswerIntegration, KnowledgeExtraction.SplitIntoFolders, KnowledgeExtraction.LinkAnswer
import ReviewComposition.GenerateParagraphOfReview, ReviewComposition.GenerateRatingsForReviewParagraphs, ReviewComposition.ExtractSectionsWithTags, ReviewComposition.CompareTwoReviewArticles, ReviewComposition.Advanced_ComparedScore
import LiteratureSearch.Advanced_Research
import psutil
GlobalStopFlag = False
TempOutputFilePath = os.path.join(RootDirectory, 'Temp', 'temp_output.txt')
IsProcessRunning = False
IsLLMCheckRunning = False
HasLLMBeenChecked = False
WindowsTextLength = 36
ConfigParams = {}
ConfigParamLists = {}
EncryptedParams = {}
EncryptedParamLists = {}
InputButtonMap = {}
InputEntryMap = {}
InputCheckButtonMap = {}
MainInputEntryMap = {}
MainInputCheckButtonMap = {}
ClaudeApiFunctions = {}
OpenAIApiFunctions = {}
def LogToFile(*Content, sep='\t'):
    with open(f'{RootDirectory}{os.sep}Temp{os.sep}run.log', 'a', encoding='UTF8') as logFile:
        logFile.write(sep.join([str(i) for i in Content]) + '\n')
def KillAllPythonProcesses():
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)
    children = current_process.children(recursive=True)
    for child in children:
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass
    script_name = os.path.basename(sys.argv[0])
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.pid == current_pid:
                continue
            if proc.name().lower() in ['python.exe', 'pythonw.exe', 'python', 'python3']:
                cmdline = proc.cmdline()
                if any(script_name in cmd for cmd in cmdline):
                    proc.kill()
            if proc.name() == os.path.basename(sys.executable):
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    _, alive = psutil.wait_procs(children, timeout=3)
    for p in alive:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass
def StopCurrentProcess():
    global GlobalStopFlag, IsProcessRunning
    if IsProcessRunning:
        GlobalStopFlag = True
        try:
            with open(TempOutputFilePath, 'w', encoding='UTF8') as f:
                f.write(OutputDisplay.get('1.0', tk.END))
        except Exception as e:
            print(f"Warning: Failed to save output: {e}")
        IsProcessRunning = False
        root.after(0, lambda: ButtonRunReviewGeneration.config(text="Run Automatic Review Generation"))
        root.after(0, lambda: ButtonSearchOptions.config(state=tk.NORMAL))
        root.after(0, lambda: ButtonLLMOptions.config(state=tk.NORMAL))
        root.after(0, lambda: ButtonReviewOptions.config(state=tk.NORMAL))
        ButtonRunReviewGeneration.config(text="Run Automatic Review Generation")
        try:
            with open(os.path.join(RootDirectory, 'Temp', 'last_working_dir.txt'), 'w') as f:
                f.write(os.getcwd())
        except Exception as e:
            print(f"Warning: Failed to save working directory: {e}")
        try:
            python = sys.executable
            script_path = os.path.join(RootDirectory, "GUI.py")
            batch_path = os.path.join(RootDirectory, "Temp", "restart.bat")
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write('@echo off\n')
                f.write('title Auto Review Generation - Restarting\n')
                f.write('color 0A\n')
                f.write('cls\n')
                f.write('echo ========================================\n')
                f.write('echo           Preparing to restart          \n')
                f.write('echo ========================================\n')
                f.write('echo.\n')
                f.write('echo Waiting for processes to close...\n')
                f.write('timeout /t 3 /nobreak\n')
                f.write('echo.\n')
                f.write(f'cd /d "{RootDirectory}"\n')
                f.write('echo Starting new instance...\n')
                f.write('echo.\n')
                f.write(f'start "" "{python}" "{script_path}"\n')
                f.write('echo.\n')
                f.write('echo ========================================\n')
                f.write('echo           Restart completed            \n')
                f.write('echo ========================================\n')
                f.write('timeout /t 2 /nobreak >nul\n')
                f.write('exit\n')
            if os.name == 'nt':
                os.system(f'start "Restarting Program" /wait cmd /c "{batch_path}"')
            else:
                shell_path = os.path.join(RootDirectory, "Temp", "restart.sh")
                with open(shell_path, 'w') as f:
                    f.write('#!/bin/bash\n')
                    f.write('sleep 3\n')
                    f.write(f'cd "{RootDirectory}"\n')
                    f.write(f'{python} "{script_path}"\n')
                os.chmod(shell_path, 0o755)
                subprocess.Popen(['bash', shell_path])
            try:
                KillAllPythonProcesses()
            except Exception as e:
                print(f"Warning: Error during process termination: {e}")
            root.after(500, lambda: root.destroy())
        except Exception as e:
            print(f"Warning: Failed to restart: {e}")
            tk.messagebox.showerror("Error", f"Failed to restart application: {e}")
            root.quit()
            sys.exit(0)
class TextOutputRedirector(io.StringIO):
    def __init__(self, widget):
        self.widget = widget
        self.progress_line = None
        io.StringIO.__init__(self)
    def write(self, str):
        global GlobalStopFlag
        if GlobalStopFlag:
            raise Exception("Process stopped by user")
        cleaned_str = re.sub(r'\x1b\[.*?[@-~]', '', str.replace("\r", ""))
        LogToFile(str)
        if "\r" in str:
            cleaned_str = cleaned_str.replace('\n', '')
            if self.progress_line is not None:
                self.widget.delete(self.progress_line, f"{self.progress_line} lineend")
            else:
                self.widget.insert(tk.END, "\n")
                self.progress_line = self.widget.index("end-1c linestart")
            self.widget.insert(self.progress_line, cleaned_str)
            if "100%" in str:
                self.progress_line = None
        else:
            if cleaned_str.replace('\n', '').strip():
                if cleaned_str.replace('\n', '').strip() == '█':
                    cleaned_str = '\n'
                self.widget.insert(tk.END, cleaned_str + '\n')
        self.widget.see(tk.END)
    def flush(self): pass
def ExecuteCommand(command):
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        subprocess.Popen(command, startupinfo=startupinfo)
    else:
        subprocess.Popen(command)
def SaveConfigParams():
    with open(f'{RootDirectory}{os.sep}Parameters', 'w', encoding='UTF8') as File:
        json.dump([
            ConfigParams,
            ConfigParamLists,
            {k: Utility.License.Encrypt(v, Utility.License.Public) for k, v in EncryptedParams.items()},
            {k: 'Ο'.join([Utility.License.Encrypt(i, Utility.License.Public) for i in v]) if v else Utility.License.Encrypt('', Utility.License.Public) for k, v in EncryptedParamLists.items()}
        ], File)
def CompareReviews():
    if not os.path.exists(f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph'):
        tk.messagebox.showinfo('', 'Please run Review Composition first to generate paragraphs.')
        return
    threading.Thread(target=lambda: CompareReviewsThread()).start()
def CompareReviewsThread():
    global IsProcessRunning
    if IsProcessRunning:
        tk.messagebox.showerror('Process is running', 'Please wait for the current process to finish.')
        return
    IsProcessRunning = True
    old_stdout = sys.stdout
    sys.stdout = TextOutputRedirector(OutputDisplay)
    try:
        print('\n' + '█' * WindowsTextLength)
        print(f"Start CompareTwoReviewArticles\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
        print('█' * WindowsTextLength)
        ReviewComposition.CompareTwoReviewArticles.Main(
            f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph',
            ConfigParams['Threads'], 5, sys.stdout, ClaudeApiFunctions, OpenAIApiFunctions
        )
        print('\n' + '█' * WindowsTextLength)
        print(f"End CompareTwoReviewArticles\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
        print('█' * WindowsTextLength)
    except Exception as e:
        tk.messagebox.showerror(f"Error {str(e)}", traceback.format_exc())
    finally:
        sys.stdout = old_stdout
        OutputDisplay.see(tk.END)
        IsProcessRunning = False
        root.after(0, lambda: ButtonRunReviewGeneration.config(text="Run Automatic Review Generation"))
        root.after(0, lambda: ButtonSearchOptions.config(state=tk.NORMAL))
        root.after(0, lambda: ButtonLLMOptions.config(state=tk.NORMAL))
        root.after(0, lambda: ButtonReviewOptions.config(state=tk.NORMAL))
def InitializeDefaultConfig():
    ConfigParams.update({
        'StartYear': 'StartYear', 'EndYear': 'EndYear',
        'Q1': True, 'Q2&Q3': False, 'Demo': True,
        'WholeProcess': False, 'Threads': 0,
        'Topic': 'Review Topic', 'SkipSearching': False,
        'SkipTopicFormulation': False, 'SkipKnowledgeExtraction': False,
        'SkipReviewComposition': False, 'MultiDownload': False,
        'MaxRun': 1, 'Model': 'claude-3-5-sonnet-20241022', 'MaxToken': 125000,
        'DirectTopicGeneration': False, 'SkipCompareTwoReviewArticles': True
    })
    ConfigParamLists.update({
        'ResearchKeys': [], 'ScreenKeys': [], 'ElsevierApiKey': ''
    })
    EncryptedParamLists.update({
        'SerpApiList': [], 'ClaudeApiKey': [],
        'OpenAIApiUrl': [], 'OpenAIApiKey': []
    })
    SaveConfigParams()
if not os.path.exists(f'{RootDirectory}{os.sep}Parameters'):
    InitializeDefaultConfig()
    ConfigParamTypes = {k: Dict for Dict in ['ConfigParams', 'ConfigParamLists', 'EncryptedParams', 'EncryptedParamLists'] for k in eval(Dict).keys()}
else:
    with open(f'{RootDirectory}{os.sep}Parameters', 'r', encoding='UTF8') as File:
        ConfigParams, ConfigParamLists, EncryptedParams, EncryptedParamLists = json.load(File)
        try:
            EncryptedParams = {k: Utility.License.Decrypt(v, Utility.License.Private) for k, v in EncryptedParams.items()}
            EncryptedParamLists = {k: [i for i in [Utility.License.Decrypt(i, Utility.License.Private) for i in v.split('Ο')] if i] for k, v in EncryptedParamLists.items()}
        except Exception:
            root = tk.Tk()
            root.withdraw()
            tk.messagebox.showerror('Error', 'Wrong License.')
            sys.exit(0)
    ConfigParamTypes = {k: Dict for Dict in ['ConfigParams', 'ConfigParamLists', 'EncryptedParams', 'EncryptedParamLists'] for k in eval(Dict).keys()}
def OpenReviewOptionsWindow():
    top = tk.Toplevel(root)
    top.title("Review Options")
    Row0Frame = tk.Frame(top)
    Row0Frame.pack()
    Row1Frame = tk.Frame(top)
    Row1Frame.pack()
    SkipCompareVar = tk.BooleanVar(value=ConfigParams['SkipCompareTwoReviewArticles'])
    DirectTopicVar = tk.BooleanVar(value=ConfigParams.get('DirectTopicGeneration', False))
    SkipCompareCheckBtn = CustomCheckbutton(Row0Frame, text="Skip Compare Review Articles", variable=SkipCompareVar)
    SkipCompareCheckBtn.pack(side=tk.LEFT)
    DirectTopicCheckBtn = CustomCheckbutton(Row1Frame, text="Direct Topic Generation", variable=DirectTopicVar)
    DirectTopicCheckBtn.pack(side=tk.LEFT)
    InputCheckButtonMap.update({
        SkipCompareCheckBtn: [SkipCompareVar, 'SkipCompareTwoReviewArticles'],
        DirectTopicCheckBtn: [DirectTopicVar, 'DirectTopicGeneration']
    })
    def SaveReviewOptions():
        ConfigParams.update({
            'SkipCompareTwoReviewArticles': SkipCompareVar.get(),
            'DirectTopicGeneration': DirectTopicVar.get()
        })
        SaveConfigParams()
        OutputDisplay.insert(tk.END, 'Review Options Saved.\n')
    def CloseWindow():
        old_stdout = sys.stdout
        sys.stdout = TextOutputRedirector(OutputDisplay)
        print('█')
        print(f"Skip Compare Review Articles: {ConfigParams['SkipCompareTwoReviewArticles']}")
        print(f"Direct Topic Generation: {ConfigParams['DirectTopicGeneration']}")
        print('█')
        sys.stdout = old_stdout
        top.destroy()
    tk.Button(top, text="Save", command=SaveReviewOptions).pack()
    top.protocol("WM_DELETE_WINDOW", CloseWindow)
def RunReviewGenerationThread():
    global IsProcessRunning, GlobalStopFlag
    if not IsProcessRunning:
        try:
            IsProcessRunning = True
            GlobalStopFlag = False
            SaveConfigParams()
            ButtonRunReviewGeneration.config(text="Stop Process")
            ButtonRunReviewGeneration.update()
            ButtonSearchOptions.config(state=tk.DISABLED)
            ButtonLLMOptions.config(state=tk.DISABLED)
            ButtonReviewOptions.config(state=tk.DISABLED)
            if os.path.exists(TempOutputFilePath):
                try:
                    os.remove(TempOutputFilePath)
                except Exception as e:
                    print(f"Warning: Failed to remove temporary output file: {e}")
            processing_thread = threading.Thread(target=lambda: RunAutomaticReviewGeneration())
            processing_thread.daemon = True
            processing_thread.start()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to start process: {str(e)}\n{traceback.format_exc()}")
            RestoreUIState()
    else:
        try:
            with open(TempOutputFilePath, 'w', encoding='UTF8') as f:
                f.write(OutputDisplay.get('1.0', tk.END))
        except Exception as e:
            print(f"Warning: Failed to save output: {e}")
        GlobalStopFlag = True
        ButtonRunReviewGeneration.config(text="Stopping...", state=tk.DISABLED)
        ButtonRunReviewGeneration.update()
        stop_thread = threading.Thread(target=lambda: StopAndRestart())
        stop_thread.daemon = True
        stop_thread.start()
def StopAndRestart():
    """处理停止和重启的过程"""
    try:
        batch_path = os.path.join(RootDirectory, "Temp", "restart.bat")
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write('@echo off\n')
            f.write('title Program Restarting\n')
            f.write('color 0A\n')
            f.write('echo Waiting for processes to close...\n')
            f.write('timeout /t 3 /nobreak\n')
            f.write(f'cd /d "{RootDirectory}"\n')
            f.write('echo Starting new instance...\n')
            f.write(f'start /min "" "{sys.executable}" "{os.path.join(RootDirectory, "GUI.py")}"\n')
        launcher_path = os.path.join(RootDirectory, "Temp", "launcher.bat")
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write('@echo off\n')
            f.write(f'start /b cmd /c "{batch_path}"\n')
        os.system(f'start cmd /c "{launcher_path}"')
        time.sleep(0.5)
        with open(os.path.join(RootDirectory, 'Temp', 'last_working_dir.txt'), 'w') as f:
            f.write(os.getcwd())
        root.after(1000, lambda: FinalCleanup())
    except Exception as e:
        print(f"Error during restart: {e}")
        traceback.print_exc()
        root.after(0, lambda: RestoreUIState())
def FinalCleanup():
    """执行最终的清理工作"""
    try:
        KillAllPythonProcesses()
    except Exception as e:
        print(f"Warning: Error during process termination: {e}")
    finally:
        root.destroy()
        sys.exit(0)
def RestoreUIState():
    global IsProcessRunning, GlobalStopFlag
    IsProcessRunning = False
    GlobalStopFlag = False
    ButtonRunReviewGeneration.config(text="Run Automatic Review Generation", state=tk.NORMAL)
    ButtonSearchOptions.config(state=tk.NORMAL)
    ButtonLLMOptions.config(state=tk.NORMAL)
    ButtonReviewOptions.config(state=tk.NORMAL)
    root.update()
def CompleteStopProcess():
    python = sys.executable
    script_path = os.path.join(RootDirectory, "GUI_Advance.py")
    try:
        with open(os.path.join(RootDirectory, 'Temp', 'last_working_dir.txt'), 'w') as f:
            f.write(os.getcwd())
        SaveConfigParams()
        subprocess.Popen([python, script_path], cwd=RootDirectory)
        root.destroy()
        sys.exit(0)
    except Exception as e:
        tk.messagebox.showerror("Error", f"Failed to restart application: {str(e)}\n{traceback.format_exc()}")
        RestoreUIState()
def InitializeApplication():
    last_working_dir_file = os.path.join(RootDirectory, 'Temp', 'last_working_dir.txt')
    if os.path.exists(last_working_dir_file):
        try:
            with open(last_working_dir_file, 'r') as f:
                os.chdir(f.read().strip())
            os.remove(last_working_dir_file)
        except Exception as e:
            print(f"Warning: Failed to restore last working directory: {e}")
    if os.path.exists(TempOutputFilePath):
        try:
            with open(TempOutputFilePath, 'r', encoding='UTF8') as f:
                OutputDisplay.insert(tk.END, f.read())
            os.remove(TempOutputFilePath)
        except Exception as e:
            print(f"Warning: Failed to load temporary output: {e}")
def RunAutomaticReviewGeneration():
    old_stdout = sys.stdout
    sys.stdout = TextOutputRedirector(OutputDisplay)
    try:
        print('\n' + '█' * WindowsTextLength)
        print(f"Start\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
        [print(msg) for msg, flag in [
            ('Run Demo', ConfigParams['Demo']),
            ('Run Whole Process', ConfigParams['WholeProcess']),
            ('Skip Searching', ConfigParams['SkipSearching']),
            ('Skip Topic Formulation', ConfigParams['SkipTopicFormulation']),
            ('Skip Knowledge Extraction', ConfigParams['SkipKnowledgeExtraction']),
            ('Skip Review Composition', ConfigParams['SkipReviewComposition'])
        ] if flag]
        print('█' * WindowsTextLength)
        if not ConfigParams['SkipSearching']:
            os.chdir(f'{RootDirectory}{os.sep}Temp')
            print('\n' + '█' * WindowsTextLength)
            print(f"Start LiteratureSearch\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
            print('█' * WindowsTextLength)
            LiteratureSearch.Advanced_Research.set_elsevier_api_key(EncryptedParams.get('ElsevierApiKey', ''))
            LiteratureSearch.One_key_download.User_pages(
                EncryptedParamLists['SerpApiList'],
                ConfigParamLists['ResearchKeys'],
                ConfigParamLists['ScreenKeys'],
                int(ConfigParams['StartYear']),
                int(ConfigParams['EndYear']),
                ConfigParams['Q1'],
                ConfigParams['Q2&Q3'],
                ConfigParams['Demo'],
                STDOUT=sys.stdout
            )
            ConfigParams['SkipSearching'] = True
            UpdateUIButtons()
            print('\n' + '█' * WindowsTextLength)
            print(f"End LiteratureSearch\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
            print('█' * WindowsTextLength)
        if ConfigParams['WholeProcess']:
            if not HasLLMBeenChecked:
                global ClaudeApiFunctions, OpenAIApiFunctions
                ClaudeApiFunctions = {idx: functools.partial(Utility.GetResponse.GetResponseFromClaude, api_key=key)
                                    for idx, key in enumerate(EncryptedParamLists['ClaudeApiKey'])}
                OpenAIApiFunctions = {
                    idx: functools.partial(Utility.GetResponse.GetResponseFromOpenAlClient,
                                           url=url, key=key, model=ConfigParams['Model'])
                                    for idx, (url, key) in enumerate(zip(EncryptedParamLists['OpenAIApiUrl'], 
                                                                       EncryptedParamLists['OpenAIApiKey']))}
            if not ConfigParams['SkipTopicFormulation']:
                if os.path.exists(f'{RootDirectory}{os.sep}Temp{os.sep}LiteratureSearchWorkDir'):
                    print('\n' + '█' * WindowsTextLength)
                    print(f"Start TopicFormulation\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
                    print('█' * WindowsTextLength)
                    topic_dir = f'{RootDirectory}{os.sep}Temp{os.sep}TopicFormulationWorkDir'
                    os.makedirs(topic_dir, exist_ok=True)
                    [shutil.copy(f'{RootDirectory}{os.sep}Temp{os.sep}LiteratureSearchWorkDir{os.sep}{f}', 
                               f'{topic_dir}{os.sep}{f}')
                     for f in os.listdir(f'{RootDirectory}{os.sep}Temp{os.sep}LiteratureSearchWorkDir')
                     if f.startswith('10.') and f.endswith('_Review.txt')]
                    TopicFormulation.GetQuestionsFromReview.Main(
                        topic_dir,
                        ConfigParams['Topic'],
                        ConfigParams['Threads'],
                        ClaudeApiFunctions,
                        OpenAIApiFunctions,
                        FromReview=not ConfigParams.get('DirectTopicGeneration', False),
                        STDOUT=sys.stdout
                    )
                    if not os.path.exists(f'{RootDirectory}{os.sep}Temp{os.sep}ParagraphQuestionsForReview.txt'):
                        tk.messagebox.showinfo('', 
                            'In the window that pops up below, modify and save the outline.\nClose the window and the next step will be executed.')
                        process = subprocess.Popen(["notepad.exe", 
                            f'{topic_dir}{os.sep}AllQuestionsFromReview{os.sep}QuestionsFromReviewManual.txt'])
                        process.wait()
                    TopicFormulation.GetQuestionsFromReview.Main2(
                        topic_dir,
                        ConfigParams['Topic'],
                        ConfigParams['Threads'],
                        ClaudeApiFunctions,
                        OpenAIApiFunctions,
                        STDOUT=sys.stdout
                    )
                    ConfigParams['SkipTopicFormulation'] = True
                    UpdateUIButtons()
                    print('\n' + '█' * WindowsTextLength)
                    print(f"End TopicFormulation\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
                    print('█' * WindowsTextLength)
                else:
                    tk.messagebox.showinfo('',
                        'Prepare papers before run TopicFormulation\nPapers can be generated by LiteratureSearch')
            if not ConfigParams['SkipKnowledgeExtraction']:
                if os.path.exists(f'{RootDirectory}{os.sep}Temp{os.sep}QuestionsForReview.txt'):
                    print('\n' + '█' * WindowsTextLength)
                    print(f"Start KnowledgeExtraction\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
                    print('█' * WindowsTextLength)
                    knowledge_dir = f'{RootDirectory}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir'
                    pdf_dir = f'{knowledge_dir}{os.sep}RawFromPDF'
                    os.makedirs(pdf_dir, exist_ok=True)
                    [shutil.copy(f'{RootDirectory}{os.sep}Temp{os.sep}LiteratureSearchWorkDir{os.sep}{f}',
                               f'{pdf_dir}{os.sep}{f}')
                     for f in os.listdir(f'{RootDirectory}{os.sep}Temp{os.sep}LiteratureSearchWorkDir')
                     if f.startswith('10.') and f.endswith('.txt')]
                    KnowledgeExtraction.XMLFormattedPrompt.GetDataList(knowledge_dir, MaxToken=ConfigParams['MaxToken'])
                    print('Prompts Generated.')
                    KnowledgeExtraction.GetAllResponse.Main(
                        knowledge_dir,
                        ConfigParams['Threads'],
                        ClaudeApiFunctions,
                        OpenAIApiFunctions,
                        STDOUT=sys.stdout,
                    )
                    KnowledgeExtraction.AnswerIntegration.Main(
                        knowledge_dir,
                        ConfigParams['Threads'],
                        ClaudeApiFunctions,
                        OpenAIApiFunctions,
                        STDOUT=sys.stdout,
                        MaxToken=ConfigParams['MaxToken']
                    )
                    print('Answers Integrated.')
                    KnowledgeExtraction.LinkAnswer.Main(knowledge_dir, EncryptedParams.get('ElsevierApiKey'))
                    KnowledgeExtraction.SplitIntoFolders.Main(f'{knowledge_dir}{os.sep}Answer', STDOUT=sys.stdout)
                    ConfigParams['SkipKnowledgeExtraction'] = True
                    UpdateUIButtons()
                    print('\n' + '█' * WindowsTextLength)
                    print(f"End KnowledgeExtraction\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
                    print('█' * WindowsTextLength)
                else:
                    tk.messagebox.showinfo('',
                        'Prepare QuestionsForReview.txt before run KnowledgeExtraction\nQuestionsForReview.txt can be generated by TopicFormulation')
            if not ConfigParams['SkipReviewComposition']:
                answer_dir = f'{RootDirectory}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}Answer'
                if os.path.exists(answer_dir) and os.listdir(answer_dir):
                    print('\n' + '█' * WindowsTextLength)
                    print(f"Start ReviewComposition\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
                    print('█' * WindowsTextLength)
                    review_dir = f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph'
                    os.makedirs(review_dir, exist_ok=True)
                    [shutil.copytree(
                        f'{answer_dir}{os.sep}{part}{os.sep}{num}',
                        f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}{int(part.split("PART")[-1]) * 7 + int(num)}',
                        dirs_exist_ok=True)
                     for part in os.listdir(answer_dir) if part.startswith('PART')
                     for num in os.listdir(f'{answer_dir}{os.sep}{part}')
                     if (not num.endswith('.txt')) and os.listdir(f'{answer_dir}{os.sep}{part}{os.sep}{num}')]
                    ReviewComposition.GenerateParagraphOfReview.Main(
                        f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir',
                        ConfigParams['Topic'],
                        ConfigParams['Threads'],
                        ClaudeApiFunctions,
                        OpenAIApiFunctions,
                        STDOUT=sys.stdout,
                    )
                    ReviewComposition.GenerateRatingsForReviewParagraphs.Main(
                        f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir',
                        ConfigParams['Threads'],
                        ClaudeApiFunctions,
                        OpenAIApiFunctions,
                        STDOUT=sys.stdout
                    )
                    best_paragraph_dir = f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}BestParagraph'
                    os.makedirs(best_paragraph_dir, exist_ok=True)
                    [shutil.copy(
                        f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph{os.sep}{para}',
                        f'{best_paragraph_dir}{os.sep}{para}'
                    ) for para in os.listdir(f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph')
                      if re.match('BestParagraph\\d+.txt', para)]
                    ReviewComposition.ExtractSectionsWithTags.Main(best_paragraph_dir, STDOUT=sys.stdout)
                    shutil.copy(f'{best_paragraph_dir}{os.sep}draft.txt', f'{RootDirectory}{os.sep}ReviewDraft.txt')
                    for log_file in ['Waitlog', 'Exceptionlog',
                                   f'{RootDirectory}{os.sep}Temp{os.sep}TopicFormulationWorkDir{os.sep}Exceptionlog',
                                   f'{RootDirectory}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}Exceptionlog',
                                   f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Exceptionlog']:
                        try:
                            os.remove(log_file)
                        except FileNotFoundError:
                            pass
                    ConfigParams['SkipReviewComposition'] = True
                    UpdateUIButtons()
                    print('\n' + '█' * WindowsTextLength)
                    print(f"End ReviewComposition\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
                    print('█' * WindowsTextLength)
                    subprocess.Popen(["notepad.exe", f'{RootDirectory}{os.sep}ReviewDraft.txt'])
                else:
                    tk.messagebox.showinfo('',
                        'Prepare AnswerList before run ReviewComposition\nAnswerList can be generated by KnowledgeExtraction')
            if not ConfigParams['SkipCompareTwoReviewArticles']:
                print('\n' + '█' * WindowsTextLength)
                print(f"Start CompareTwoReviewArticles\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
                print('█' * WindowsTextLength)
                ReviewComposition.CompareTwoReviewArticles.Main(
                    f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph',
                    ConfigParams['Threads'],
                    5,
                    sys.stdout,
                    ClaudeApiFunctions,
                    OpenAIApiFunctions
                )
                compare_path = f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph{os.sep}CompareParagraph'
                ReviewComposition.Advanced_ComparedScore.Main2(compare_path)
                print('\n' + '█' * WindowsTextLength)
                print(f"End CompareTwoReviewArticles\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
                print('█' * WindowsTextLength)
                ConfigParams['SkipCompareTwoReviewArticles'] = True
                UpdateUIButtons()
        print('\n' + '█' * WindowsTextLength)
        print(f"End\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
        print('█' * WindowsTextLength)
    except BaseException as e:
        tk.messagebox.showerror(f"Error {str(e)}", traceback.format_exc())
    finally:
        os.chdir(f'{RootDirectory}{os.sep}Temp')
        sys.stdout = old_stdout
        shutil.copy('run.log', f"logs{os.sep}run{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}.log")
        SaveConfigParams()
        if not Row0Frame.winfo_viewable():
            ToggleFramesVisibility()
        os.chdir(RootDirectory)
        OutputDisplay.see(tk.END)
        global IsProcessRunning
        IsProcessRunning = False
        root.after(0, lambda: ButtonRunReviewGeneration.config(text="Run Automatic Review Generation"))
        root.after(0, lambda: ButtonSearchOptions.config(state=tk.NORMAL))
        root.after(0, lambda: ButtonLLMOptions.config(state=tk.NORMAL))
        root.after(0, lambda: ButtonReviewOptions.config(state=tk.NORMAL))
def GetUserInput(list_name):
    user_input = tk.simpledialog.askstring("Input",
        f"Enter a string for {list_name}\nEnter '!!!~~~!!!' to clean all items in {list_name}\nEnter nothing will change nothing")
    if user_input:
        if list_name == 'ElsevierApiKey':
            EncryptedParams['ElsevierApiKey'] = '' if user_input == '!!!~~~!!!' else user_input
            OutputDisplay.insert(tk.END, f'{list_name} {"Cleared" if user_input == "!!!~~~!!!" else "Saved"}.\n')
        else:
            target_dict = eval(ConfigParamTypes[list_name])
            if user_input == '!!!~~~!!!':
                target_dict[list_name].clear()
                OutputDisplay.insert(tk.END, f'{list_name} Cleared.\n')
            else:
                target_dict[list_name].append(user_input)
                OutputDisplay.insert(tk.END, f'{list_name} Saved.\n')
    if list_name in ['ClaudeApiKey']:
        global ClaudeApiFunctions
        ClaudeApiFunctions = {idx: functools.partial(Utility.GetResponse.GetResponseFromClaude, api_key=key)
                             for idx, key in enumerate(EncryptedParamLists['ClaudeApiKey'])}
    if list_name in ['OpenAIApiUrl', 'OpenAIApiKey']:
        global OpenAIApiFunctions
        OpenAIApiFunctions = {idx: functools.partial(Utility.GetResponse.GetResponseFromOpenAlClient, url=url, key=key)
                             for idx, (url, key) in enumerate(zip(EncryptedParamLists['OpenAIApiUrl'],
                                                                EncryptedParamLists['OpenAIApiKey']))}
def ValidateYear(Entry):
    try:
        year = int(Entry.get())
        assert 1900 < year < time.localtime().tm_year + 2, f'1900<Year<{time.localtime().tm_year + 3}'
        UpdateDisplay()
    except Exception as e:
        tk.messagebox.showerror(f"Error  {str(e)}", traceback.format_exc())
def OpenSearchOptionsWindow():
    topWindow = tk.Toplevel(root)
    topWindow.title("Search Options")
    def CreateSection(title, parent):
        titleFrame = tk.Frame(parent, bg='black')
        titleFrame.pack(fill=tk.X, pady=(10, 5))
        tk.Label(titleFrame, text=title, bg='black', fg='white').pack(anchor='w')
        contentFrame = tk.Frame(parent, bg='black')
        contentFrame.pack(fill=tk.X, pady=5)
        return contentFrame
    mainContainer = tk.Frame(topWindow, bg='black')
    mainContainer.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
    leftColumn = tk.Frame(mainContainer, bg='black')
    leftColumn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
    apiFrame = CreateSection("API Configuration", leftColumn)
    apiButtons = [
        ("Add to Serp API List", lambda: GetUserInput('SerpApiList')),
        ("Set Elsevier API Key", lambda: GetUserInput('ElsevierApiKey'))
    ]
    for btnText, btnCommand in apiButtons:
        btn = tk.Button(apiFrame, text=btnText, command=btnCommand)
        btn.pack(pady=2)
        InputButtonMap[btn] = btnText.split("Add to ")[-1].strip() if "Add to" in btnText else btnText.split("Set ")[-1].strip()
    keywordsFrame = CreateSection("Keywords Settings", leftColumn)
    keywordsButtons = [
        ("Add to Research Keys", lambda: GetUserInput('ResearchKeys')),
        ("Add to Screen Keys", lambda: GetUserInput('ScreenKeys'))
    ]
    for btnText, btnCommand in keywordsButtons:
        btn = tk.Button(keywordsFrame, text=btnText, command=btnCommand)
        btn.pack(pady=2)
        InputButtonMap[btn] = btnText.split("Add to ")[-1].strip()
    rightColumn = tk.Frame(mainContainer, bg='black')
    rightColumn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
    journalFrame = CreateSection("Journal Selection", rightColumn)
    journalBtn = tk.Button(journalFrame, text="Custom Journals", command=OpenJournalEditor)
    journalBtn.pack(pady=2)
    qualityFrame = tk.Frame(journalFrame, bg='black')
    qualityFrame.pack(pady=5)
    q1Var = tk.BooleanVar(value=ConfigParams['Q1'])
    q23Var = tk.BooleanVar(value=ConfigParams['Q2&Q3'])
    q1Btn = CustomCheckbutton(qualityFrame, text="Q1", variable=q1Var)
    q1Btn.pack(side=tk.LEFT, padx=20)
    q23Btn = CustomCheckbutton(qualityFrame, text="Q2&Q3", variable=q23Var)
    q23Btn.pack(side=tk.LEFT, padx=20)
    InputCheckButtonMap.update({
        q1Btn: [q1Var, 'Q1'],
        q23Btn: [q23Var, 'Q2&Q3']
    })
    yearFrame = CreateSection("Time Range", rightColumn)
    def CreateYearEntry(parent, label, defaultValue):
        frame = tk.Frame(parent, bg='black')
        frame.pack(pady=2)
        tk.Label(frame, text=label, bg='black', fg='white').pack(side=tk.LEFT, padx=5)
        entry = tk.Entry(frame, width=10)
        entry.pack(side=tk.LEFT)
        entry.insert(0, defaultValue)
        entry.bind("<Return>", lambda event: ValidateYear(entry))
        return entry
    startYearEntry = CreateYearEntry(yearFrame, "Start Year:", ConfigParams['StartYear'])
    endYearEntry = CreateYearEntry(yearFrame, "End Year:", ConfigParams['EndYear'])
    InputEntryMap.update({
        startYearEntry: 'StartYear',
        endYearEntry: 'EndYear'
    })
    bottomContainer = tk.Frame(topWindow, bg='black')
    bottomContainer.pack(fill=tk.X, padx=15, pady=(0, 10))
    downloadFrame = tk.Frame(bottomContainer, bg='black')
    downloadFrame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    tk.Label(downloadFrame, text="Download Settings", bg='black', fg='white').pack(anchor='w', pady=(0, 5))
    settingsContainer = tk.Frame(downloadFrame, bg='black')
    settingsContainer.pack(fill=tk.X)
    multiDownloadVar = tk.BooleanVar(value=ConfigParams.get('MultiDownload', False))
    multiDownloadBtn = CustomCheckbutton(settingsContainer, text="Enable Multi-download", 
                                       variable=multiDownloadVar)
    multiDownloadBtn.pack(side=tk.LEFT, padx=(0, 20))
    tk.Label(settingsContainer, text="Max Run:", bg='black', fg='white').pack(side=tk.LEFT, padx=(0, 5))
    maxRunEntry = tk.Entry(settingsContainer, width=4)
    maxRunEntry.pack(side=tk.LEFT)
    maxRunEntry.insert(0, ConfigParams.get('MaxRun', '5'))
    InputEntryMap[maxRunEntry] = 'MaxRun'
    InputCheckButtonMap[multiDownloadBtn] = [multiDownloadVar, 'MultiDownload']
    def SaveSettings():
        ConfigParams.update({
            'StartYear': startYearEntry.get(),
            'EndYear': endYearEntry.get(),
            'Q1': q1Var.get(),
            'Q2&Q3': q23Var.get(),
            'MultiDownload': multiDownloadVar.get(),
            'MaxRun': maxRunEntry.get()
        })
        SaveConfigParams()
        OutputDisplay.insert(tk.END, 'Search Options Saved.\n')
        OutputDisplay.insert(tk.END, f"Elsevier API Key: {'Set' if EncryptedParams.get('ElsevierApiKey') else 'Not Set'}\n")
    saveBtn = tk.Button(bottomContainer, text="Save Settings", command=SaveSettings)
    saveBtn.pack(side=tk.RIGHT, padx=(50, 0))
    def OnWindowClosing():
        old_stdout = sys.stdout
        sys.stdout = TextOutputRedirector(OutputDisplay)
        print('█')
        print(f"SerpApi List: {len(EncryptedParamLists['SerpApiList'])} APIs")
        print(f"Research Keys: {ConfigParamLists['ResearchKeys']}")
        print(f"Screen Keys: {ConfigParamLists['ScreenKeys']}")
        print(f"Start Year: {ConfigParams['StartYear']}")
        print(f"End Year: {ConfigParams['EndYear']}")
        print(f"CAS Q1: {ConfigParams['Q1']}")
        print(f"CAS Q2&Q3: {ConfigParams['Q2&Q3']}")
        print(f"Multi-download: {ConfigParams['MultiDownload']}")
        print(f"Max Run: {ConfigParams['MaxRun']}")
        print('█')
        sys.stdout = old_stdout
        topWindow.destroy()
    topWindow.protocol("WM_DELETE_WINDOW", OnWindowClosing)
    topWindow.update_idletasks()
    width = topWindow.winfo_width()
    height = topWindow.winfo_height()
    x = (topWindow.winfo_screenwidth() // 2) - (width // 2)
    y = (topWindow.winfo_screenheight() // 2) - (height // 2)
    topWindow.geometry(f'+{x}+{y}')
    topWindow.minsize(width, height)
def OpenJournalEditor():
    journal_file = f'{RootDirectory}{os.sep}Temp{os.sep}custom_journals.txt'
    if not os.path.exists(journal_file):
        with open(journal_file, 'w', encoding='utf-8') as f:
            f.write("# Enter one journal name per line\n# Lines starting with # are comments\n\n")
    try:
        process = subprocess.Popen(["notepad.exe", journal_file])
        process.wait()
        with open(journal_file, 'r', encoding='utf-8') as f:
            journals = [line.strip() for line in f.readlines() 
                       if line.strip() and not line.startswith('#')]
        import LiteratureSearch.Global_Journal as Global_Journal
        importlib.reload(Global_Journal)
        Global_Journal.User_defined.clear()
        Global_Journal.User_defined.extend(journals)
        if journals:
            import LiteratureSearch.One_key_download as One_key_download
            One_key_download.High_IF_publications['User_defined'] = journals
            One_key_download.Low_IF_publications['User_defined'] = journals
        OutputDisplay.insert(tk.END, f"Updated custom journal list ({len(journals)} journals)\n")
        OutputDisplay.see(tk.END)
        SaveConfigParams()
    except Exception as e:
        tk.messagebox.showerror("Error", f"Failed to update custom journals: {str(e)}\n{traceback.format_exc()}")
def TestLLMResponse():
    global IsLLMCheckRunning
    if not IsLLMCheckRunning:
        IsLLMCheckRunning = True
        threading.Thread(target=CheckLLMResponse).start()
    else:
        tk.messagebox.showerror('Check LLM Response is running', 'Only run one process at a time.')
def CheckLLMResponse():
    old_stdout = sys.stdout
    sys.stdout = TextOutputRedirector(OutputDisplay)
    print('\nCheck LLM Response:')
    print('Check ClaudeAPI Response:')
    for idx, key in enumerate(EncryptedParamLists['ClaudeApiKey']):
        try:
            response = Utility.GetResponse.GetResponseFromClaude('Who are you?', key)
            print(f'{idx}\t{response}')
            ClaudeApiFunctions[idx] = functools.partial(Utility.GetResponse.GetResponseFromClaude, api_key=key)
        except Exception as e:
            ClaudeApiFunctions[idx] = False
            print(f'{idx}\tFailed', e)
    print('Check OpenAIAPI Response:')
    for idx, (url, key) in enumerate(zip(EncryptedParamLists['OpenAIApiUrl'], EncryptedParamLists['OpenAIApiKey'])):
        try:
            response = Utility.GetResponse.GetResponseFromOpenAlClient('Who are you?', url, key,
                                                                            model=ConfigParams['Model'])
            print(f'{idx}\t{response}')
            OpenAIApiFunctions[idx] = functools.partial(Utility.GetResponse.GetResponseFromOpenAlClient,
                                                        url=url, key=key, model=ConfigParams['Model'])
        except Exception as e:
            OpenAIApiFunctions[idx] = False
            print(f'{idx}\tFailed', e)
    print('Check LLM finished')
    if ClaudeApiFunctions:
        print(f'ClaudeApiFunctions\t{({k: bool(v) for k, v in ClaudeApiFunctions.items()})}')
    if OpenAIApiFunctions:
        print(f'OpenAIApiFunctions\t{({k: bool(v) for k, v in OpenAIApiFunctions.items()})}')
    sys.stdout = old_stdout
    global IsLLMCheckRunning, HasLLMBeenChecked
    HasLLMBeenChecked = True
    IsLLMCheckRunning = False
def OpenLLMOptionsWindow():
    top = tk.Toplevel(root)
    top.title("LLM Options")
    def CreateApiSection(title, buttons):
        title_frame = tk.Frame(top)
        title_frame.pack(pady=(10, 5))
        tk.Label(title_frame, text=title).pack()
        api_frame = tk.Frame(top)
        api_frame.pack(pady=5)
        for btn_text, btn_command in buttons:
            btn = tk.Button(api_frame, text=btn_text, command=btn_command, width=30)
            btn.pack(pady=2)
            InputButtonMap[btn] = btn_text.split("Add to ")[-1].strip()
        return api_frame
    CreateApiSection("Claude API Settings", [
        ("Add to Claude Api Key List", lambda: GetUserInput('ClaudeApiKey'))
    ])
    tk.Frame(top, height=2, bg='white').pack(fill=tk.X, pady=10)
    CreateApiSection("OpenAI API Settings", [
        ("Add to OpenAI-compatible API Url List", lambda: GetUserInput('OpenAIApiUrl')),
        ("Add to OpenAI-compatible API Key List", lambda: GetUserInput('OpenAIApiKey'))
    ])
    tk.Frame(top, height=2, bg='white').pack(fill=tk.X, pady=10)
    model_title_frame = tk.Frame(top)
    model_title_frame.pack(pady=(5, 5))
    tk.Label(model_title_frame, text="Model Configuration").pack()
    model_frame = tk.Frame(top)
    model_frame.pack(pady=5)
    def CreateConfigEntry(parent, label, default_value, config_key):
        frame = tk.Frame(parent)
        frame.pack(pady=5)
        tk.Label(frame, text=label, width=12, anchor='e').pack(side=tk.LEFT, padx=5)
        entry = tk.Entry(frame, width=20)
        entry.pack(side=tk.LEFT)
        entry.insert(0, default_value)
        InputEntryMap[entry] = config_key
        return entry
    model_entry = CreateConfigEntry(model_frame, "Model Name:", ConfigParams['Model'], 'Model')
    token_entry = CreateConfigEntry(model_frame, "Max Tokens:", str(ConfigParams.get('MaxToken', 25000)), 'MaxToken')
    tk.Frame(top, height=2, bg='white').pack(fill=tk.X, pady=10)
    test_title_frame = tk.Frame(top)
    test_title_frame.pack(pady=(5, 5))
    tk.Label(test_title_frame, text="Connection Test").pack()
    check_frame = tk.Frame(top)
    check_frame.pack(pady=10)
    tk.Button(check_frame, text="Check LLM Response", command=TestLLMResponse, width=30).pack()
    save_frame = tk.Frame(top)
    save_frame.pack(pady=15)
    def SaveSettings():
        ConfigParams.update({
            'Model': model_entry.get(),
            'MaxToken': int(token_entry.get())
        })
        SaveConfigParams()
        OutputDisplay.insert(tk.END, 'LLM Options Saved.\n')
    tk.Button(save_frame, text="Save Settings", width=20, command=SaveSettings).pack()
    def OnClose():
        old_stdout = sys.stdout
        sys.stdout = TextOutputRedirector(OutputDisplay)
        print('█')
        print(f"ClaudeApiKey List: {len(EncryptedParamLists['ClaudeApiKey'])} Keys")
        print(f"OpenAIApiUrl List: {len(EncryptedParamLists['OpenAIApiUrl'])} Urls")
        print(f"OpenAIApiKey List: {len(EncryptedParamLists['OpenAIApiKey'])} Keys")
        ConfigParams["Threads"] = len(list(zip(EncryptedParamLists['OpenAIApiUrl'],
                                             EncryptedParamLists['OpenAIApiKey']))) * 3 + len(
            EncryptedParamLists['ClaudeApiKey'])
        print(f'Threads: {ConfigParams["Threads"]}')
        print(f"Max Tokens: {ConfigParams['MaxToken']}")
        print(f"Model: {ConfigParams['Model']}")
        print('█')
        sys.stdout = old_stdout
        top.destroy()
    top.protocol("WM_DELETE_WINDOW", OnClose)
class CustomCheckbutton(tk.Frame):
    def __init__(self, parent, text="", variable=None, command=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._variable = variable
        self.command = command
        self.canvas = tk.Canvas(self, width=20, height=20, bg='black', highlightthickness=0)
        self.check_rect = self.canvas.create_rectangle(1, 1, 19, 19, outline='white', fill='black', width=4)
        self.canvas.bind("<Button-1>", self.toggle)
        self.canvas.pack(side=tk.LEFT)
        self.label = tk.Label(self, text=text, bg='black', fg='white')
        self.label.pack(side=tk.LEFT)
        self.label.bind("<Button-1>", self.toggle)
        self.update_check()
    def toggle(self, event=None):
        self._variable.set(not self._variable.get())
        self.update_check()
        if self.command:
            self.command()
    def update_check(self):
        self.canvas.itemconfig(self.check_rect, fill='white' if self._variable.get() else 'black')
    def config(self, **kwargs):
        if "variable" in kwargs:
            self._variable = kwargs.pop("variable")
        super().config(**kwargs)
        self.update_check()
    def configure(self, **kwargs):
        self.config(**kwargs)
def UpdateUIButtons():
    for btn, (var, param_name) in MainInputCheckButtonMap.items():
        var.set(eval(ConfigParamTypes[param_name])[param_name])
        btn.config(variable=var)
def UpdateDisplay():
    UpdateUIButtons()
    display_text = '\n'.join([
        f"TOPIC: {ConfigParams['Topic']}",
        f"Demo: {ConfigParams['Demo']}",
        f"WholeProcess: {ConfigParams['WholeProcess']}",
        f"SkipSearching: {ConfigParams['SkipSearching']}",
        f"Multi-Download: {ConfigParams['MultiDownload']}",
        f"SkipTopicFormulation: {ConfigParams['SkipTopicFormulation']}",
        f"SkipKnowledgeExtraction: {ConfigParams['SkipKnowledgeExtraction']}",
        f"SkipReviewComposition: {ConfigParams['SkipReviewComposition']}",
        f"Model: {ConfigParams['Model']}",
        f"Max Tokens: {ConfigParams.get('MaxToken', 25000)}",
        f"SkipCompareTwoReviewArticles: {ConfigParams['SkipCompareTwoReviewArticles']}",
        f"Direct Topic Generation: {ConfigParams.get('DirectTopicGeneration', False)}"
    ])
    OutputDisplay.insert(tk.END, f"\n{display_text}\n")
    OutputDisplay.see(tk.END)
def SaveAndUpdateDisplay():
    for entry, param_name in MainInputEntryMap.items():
        eval(ConfigParamTypes[InputEntryMap[entry]])[InputEntryMap[entry]] = entry.get()
    for btn, (var, param_name) in MainInputCheckButtonMap.items():
        eval(ConfigParamTypes[InputCheckButtonMap[btn][1]])[InputCheckButtonMap[btn][1]] = var.get()
    SaveConfigParams()
    UpdateDisplay()
def ToggleFramesVisibility():
    is_visible = Row0Frame.winfo_viewable()
    for frame in [Row0Frame, Row1Frame, Row2Frame, Row3Frame, Row4Frame, OutputDisplay, OutputScrollbar]:
        frame.pack_forget()
    if is_visible:
        Row4Frame.pack()
        OutputDisplay.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        OutputScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    else:
        for frame in [Row0Frame, Row1Frame, Row2Frame, Row3Frame, Row4Frame]:
            frame.pack()
        OutputDisplay.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        OutputScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
root = tk.Tk()
root.title("Automatic Review Generation V0.0")
root.option_add("*Font", "{Times New Roman} 25")
root.option_add('*background', 'black')
root.option_add('*foreground', 'white')
root.option_add('*Entry*insertBackground', 'white')
root.option_add('*Text*insertBackground', 'white')
root.configure(bg='black')
Row0Frame = tk.Frame(root)
Row1Frame = tk.Frame(root)
Row2Frame = tk.Frame(root)
Row3Frame = tk.Frame(root)
Row4Frame = tk.Frame(root)
[frames_to_pack := [Row0Frame, Row1Frame, Row2Frame, Row3Frame, Row4Frame]]
[frame.pack() for frame in frames_to_pack]
tk.Label(Row0Frame, text="TOPIC:").pack(side=tk.LEFT)
TopicEntry = tk.Entry(Row0Frame)
TopicEntry.pack(side=tk.LEFT, padx=(0, 32))
TopicEntry.insert(0, ConfigParams['Topic'])
TopicEntry.bind("<Return>", lambda event: SaveAndUpdateDisplay())
InputEntryMap[TopicEntry] = 'Topic'
MainInputEntryMap[TopicEntry] = 'Topic'
def CreateMainCheckbutton(parent, text, config_key, padding=0):
    var = tk.BooleanVar(value=ConfigParams[config_key])
    btn = CustomCheckbutton(parent, text=text, variable=var, command=SaveAndUpdateDisplay)
    btn.pack(side=tk.LEFT, padx=(0, padding))
    InputCheckButtonMap[btn] = [var, config_key]
    MainInputCheckButtonMap[btn] = [var, config_key]
    return btn
DemoCheckBtn = CreateMainCheckbutton(Row0Frame, "Demo", 'Demo', 17)
WholeProcessCheckBtn = CreateMainCheckbutton(Row0Frame, "Whole Process", 'WholeProcess')
SkipSearchCheckBtn = CreateMainCheckbutton(Row1Frame, "Skip Literature Search", 'SkipSearching', 114)
SkipTopicCheckBtn = CreateMainCheckbutton(Row1Frame, "Skip Topic Formulation", 'SkipTopicFormulation', 27)
SkipKnowledgeCheckBtn = CreateMainCheckbutton(Row2Frame, "Skip Knowledge Extraction", 'SkipKnowledgeExtraction', 49)
SkipReviewCheckBtn = CreateMainCheckbutton(Row2Frame, "Skip Review Composition", 'SkipReviewComposition')
ButtonSearchOptions = tk.Button(Row3Frame, text="Search Options", command=OpenSearchOptionsWindow)
ButtonLLMOptions = tk.Button(Row3Frame, text="LLM Options", command=OpenLLMOptionsWindow)
ButtonReviewOptions = tk.Button(Row3Frame, text="Review Options", command=OpenReviewOptionsWindow)
[btn.pack(side=tk.LEFT) for btn in [ButtonSearchOptions, ButtonLLMOptions, ButtonReviewOptions]]
ToggleButton = tk.Button(Row4Frame, text="Show/Hide Options", command=ToggleFramesVisibility)
ButtonRunReviewGeneration = tk.Button(Row4Frame, text="Run Automatic Review Generation",
                                    command=RunReviewGenerationThread)
[btn.pack(side=tk.LEFT) for btn in [ToggleButton, ButtonRunReviewGeneration]]
OutputDisplay = tk.Text(root, height=13, width=49)
OutputScrollbar = tk.Scrollbar(root, command=OutputDisplay.yview)
OutputDisplay.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
OutputScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
OutputDisplay.config(yscrollcommand=OutputScrollbar.set)
UpdateDisplay()
if os.path.exists(TempOutputFilePath):
    try:
        with open(TempOutputFilePath, 'r', encoding='UTF8') as f:
            OutputDisplay.insert(tk.END, f.read())
        os.remove(TempOutputFilePath)
    except Exception as e:
        print(f"Warning: Failed to load temporary output: {e}")
root.attributes('-topmost', True)
root.update()
root.attributes('-topmost', False)
window_width = root.winfo_width()
window_height = root.winfo_height()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = int((screen_width / 2) - (window_width / 2))
y = int((screen_height / 2) - (window_height / 2))
root.geometry(f'{window_width}x{window_height}+{x}+{y}')
root.mainloop()
os.chdir(RootDirectory)
try:
    shutil.copy(f'Temp{os.sep}run.log',
                f"Temp{os.sep}logs{os.sep}run{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}.log")
except:
    pass
ExecuteCommand(f"TASKKILL /F /IM {os.path.basename(sys.executable) if 'python' not in os.path.basename(sys.executable) else 'GUI.exe'}")
