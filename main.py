import tkinter as tk
from tkinter import ttk, messagebox
import io, re, os, sys, json, time, shutil, threading, traceback, functools, importlib, subprocess
import psutil
import datetime
import hashlib
import webbrowser
import requests
import multiprocessing
from multiprocessing import Process, Queue
RootDirectory = os.path.abspath('.')
os.makedirs('Temp', exist_ok=True)
os.makedirs('Temp/logs', exist_ok=True)
os.chdir('Temp')
try:
    import Utility.License, Utility.GetResponse
    import LiteratureSearch.One_key_download, MultiDownload.One_key_download
    import TopicFormulation.GetQuestionsFromReview
    import KnowledgeExtraction.XMLFormattedPrompt, KnowledgeExtraction.GetAllResponse, \
        KnowledgeExtraction.AnswerIntegration, KnowledgeExtraction.SplitIntoFolders, KnowledgeExtraction.LinkAnswer
    import ReviewComposition.GenerateParagraphOfReview, ReviewComposition.GenerateRatingsForReviewParagraphs, \
        ReviewComposition.ExtractSectionsWithTags, ReviewComposition.CompareTwoReviewArticles, \
        ReviewComposition.Advanced_ComparedScore
    import LiteratureSearch.Advanced_Research
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please make sure you're running this script from the correct directory.")
    sys.exit(1)
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
def ExecuteCommand(command):
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        subprocess.Popen(command, startupinfo=startupinfo)
    else:
        subprocess.Popen(command)
def InitializeDefaultConfig():
    install_date = datetime.datetime.now().strftime('%Y-%m-%d')
    ConfigParams.update({
        'StartYear': '2020', 'EndYear': '2026',
        'Q1': True, 'Q2&Q3': False, 'Demo': True,
        'Topic': '', 'SkipSearching': False,
        'SkipTopicFormulation': False, 'SkipKnowledgeExtraction': False,
        'SkipReviewComposition': False,
        'DirectTopicGeneration': False, 'SkipCompareTwoReviewArticles': True,
        'MaxPapers': 100,  
        'Language': 'zh', 'Theme': 'dark'
    })
    ConfigParamLists.update({
        'ResearchKeys': [], 'ScreenKeys': []
    })
    EncryptedParams.update({
        'InstallDate': install_date,
        'StoredUsername': '',
        'StoredPassword': ''
    })
    EncryptedParamLists.update({
        'SerpApiList': [], 'ClaudeApiKey': [],
        'OpenAIApiUrl': [], 'OpenAIApiKey': [],
        'ElsevierApiList': []
    })
    SaveConfigParams()
def SaveConfigParams():
    with open(f'{RootDirectory}{os.sep}Parameters', 'w', encoding='UTF8') as File:
        json.dump([
            ConfigParams,
            ConfigParamLists,
            {k: Utility.License.Encrypt(v, Utility.License.Public) for k, v in EncryptedParams.items()},
            {k: 'Ο'.join(
                [Utility.License.Encrypt(i, Utility.License.Public) for i in v]) if v else Utility.License.Encrypt('',
                                                                                                                   Utility.License.Public)
             for k, v in EncryptedParamLists.items()}
        ], File)
if not os.path.exists(f'{RootDirectory}{os.sep}Parameters'):
    InitializeDefaultConfig()
else:
    try:
        with open(f'{RootDirectory}{os.sep}Parameters', 'r', encoding='UTF8') as File:
            ConfigParams, ConfigParamLists, EncryptedParams, EncryptedParamLists = json.load(File)
            try:
                EncryptedParams = {k: Utility.License.Decrypt(v, Utility.License.Private) for k, v in
                                   EncryptedParams.items()}
                EncryptedParamLists = {
                    k: [i for i in [Utility.License.Decrypt(i, Utility.License.Private) for i in v.split('Ο')] if i] for
                    k, v in EncryptedParamLists.items()}
            except Exception:
                tk_root = tk.Tk()
                tk_root.withdraw()
                messagebox.showerror('Error', 'Wrong License.')
                sys.exit(0)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        InitializeDefaultConfig()
ConfigParamTypes = {k: Dict for Dict in ['ConfigParams', 'ConfigParamLists', 'EncryptedParams', 'EncryptedParamLists']
                    for k in eval(Dict).keys()}
class TextOutputRedirector(io.StringIO):
    def __init__(self, widget, gui_ref=None):
        self.widget = widget
        self.gui_ref = gui_ref
        self.progress_line = None
        io.StringIO.__init__(self)
    def write(self, str):
        cleaned_str = re.sub(r'\x1b\[.*?[@-~]', '', str.replace("\r", ""))
        LogToFile(str)
        if "\r" in str and "|" in str and "%" in str:
            try:
                percent_match = re.search(r'(\d+)%', str)
                if percent_match and self.gui_ref:
                    percent = int(percent_match.group(1))
                    self.gui_ref.update_progress_value(percent)
                    self.widget.update_idletasks()
            except Exception:
                pass
            cleaned_str = cleaned_str.replace('\n', '')
            if self.progress_line is not None:
                self.widget.delete(self.progress_line, f"{self.progress_line} lineend")
            else:
                self.widget.insert(tk.END, "\n")
                self.progress_line = self.widget.index("end-1c linestart")
            self.widget.insert(self.progress_line, cleaned_str)
            if "100%" in str:
                self.progress_line = None
                if self.gui_ref:
                    self.gui_ref.update_progress_value(100)
                    self.widget.update_idletasks()
        else:
            if cleaned_str.replace('\n', '').strip():
                if cleaned_str.replace('\n', '').strip() == '█':
                    cleaned_str = '\n'
                try:
                    self.widget.insert(tk.END, cleaned_str + '\n')
                    self.widget.see(tk.END)
                except tk.TclError:
                    pass
    def flush(self):
        pass
def load_language_resources():
    resources = {'zh': {}, 'en': {}}
    try:
        with open(os.path.join(RootDirectory,'Temp', 'language_resources.jsonl'), 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line.strip())
                    key = data['key']
                    resources['zh'][key] = data['zh']
                    resources['en'][key] = data['en']
    except FileNotFoundError:
        print("Warning: language_resources.jsonl not found, using default texts")
    return resources
def md5_encrypt(text):
    md5 = hashlib.md5()
    md5.update(text.encode('utf-8'))
    return md5.hexdigest()
def login_request(payload):
    base_url = "https://www.aistrucx.com/api"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(base_url + "/user/auth/login", 
                               data=json.dumps(payload), 
                               headers=headers, 
                               timeout=10)
        return response.json()
    except requests.exceptions.RequestException:
        return {"code": 504, "msg": "Request failed"}
def verify_user(username, password):
    payload = {"username": username, "password": md5_encrypt(password)}
    res_json = login_request(payload)
    return res_json.get("code") == 200
def verify_stored_user():
    stored_username = EncryptedParams.get('StoredUsername', '')
    stored_password = EncryptedParams.get('StoredPassword', '')
    if not stored_username or not stored_password:
        return False
    return verify_user(stored_username, stored_password)
def get_trial_days_left():
    install_date_str = EncryptedParams.get('InstallDate')
    if not install_date_str:
        return 30
    try:
        install_date = datetime.datetime.strptime(install_date_str, '%Y-%m-%d')
        today = datetime.datetime.now()
        delta = datetime.timedelta(days=30) - (today - install_date)
        return max(0, delta.days)
    except Exception:
        return 0
def user_authentication():
    if verify_stored_user():
        return True
    auth_window = tk.Toplevel()
    auth_window.title("用户验证 User Authentication")
    width, height = 600, 500
    x = (auth_window.winfo_screenwidth() // 2) - (width // 2)
    y = (auth_window.winfo_screenheight() // 2) - (height // 2)
    auth_window.geometry(f'{width}x{height}+{x}+{y}')
    auth_window.resizable(False, False)
    auth_window.attributes('-topmost', True)
    auth_window.configure(bg="#000000")
    chinese_font = ('楷体', 17)
    english_font = ('Times New Roman', 17)
    style = ttk.Style()
    style.configure('Auth.TLabel', background="#000000", foreground="#ffffff")
    style.configure('Auth.TFrame', background="#000000")
    style.configure('Auth.TButton', background="#000000", foreground="#ffffff")
    style.configure('Auth.TEntry', background="#ffffff", foreground="#000000")
    result = {'authenticated': False}
    main_frame = ttk.Frame(auth_window, style='Auth.TFrame')
    main_frame.pack(padx=20, pady=20, fill='both', expand=True)
    title_frame = ttk.Frame(main_frame, style='Auth.TFrame')
    title_frame.pack(fill='x', pady=(0, 20))
    title_cn = tk.Label(title_frame, text="用户身份验证", 
                       font=chinese_font, bg="#000000", fg="#ffffff")
    title_cn.pack()
    title_en = tk.Label(title_frame, text="User Authentication", 
                       font=english_font, bg="#000000", fg="#ffffff")
    title_en.pack()
    username_frame = ttk.Frame(main_frame, style='Auth.TFrame')
    username_frame.pack(fill='x', pady=10)
    username_label_frame = ttk.Frame(username_frame, style='Auth.TFrame')
    username_label_frame.pack(side='left')
    username_cn = tk.Label(username_label_frame, text="用户名", 
                          font=chinese_font, bg="#000000", fg="#ffffff")
    username_cn.pack(side='left')
    username_en = tk.Label(username_label_frame, text=" Username:", 
                          font=english_font, bg="#000000", fg="#ffffff")
    username_en.pack(side='left')
    username_entry = ttk.Entry(username_frame, width=45, style='Auth.TEntry', font=('Times New Roman', 12))
    username_entry.pack(side='right', padx=(0, 0))
    stored_username = EncryptedParams.get('StoredUsername', '')
    if stored_username:
        username_entry.insert(0, stored_username)
    password_frame = ttk.Frame(main_frame, style='Auth.TFrame')
    password_frame.pack(fill='x', pady=10)
    password_label_frame = ttk.Frame(password_frame, style='Auth.TFrame')
    password_label_frame.pack(side='left')
    password_cn = tk.Label(password_label_frame, text="密码", 
                          font=chinese_font, bg="#000000", fg="#ffffff")
    password_cn.pack(side='left')
    password_en = tk.Label(password_label_frame, text=" Password:", 
                          font=english_font, bg="#000000", fg="#ffffff")
    password_en.pack(side='left')
    password_entry = ttk.Entry(password_frame, width=45, show="*", style='Auth.TEntry', font=('Times New Roman', 12))
    password_entry.pack(side='right', padx=(0, 0))
    button_frame = ttk.Frame(main_frame, style='Auth.TFrame')
    button_frame.pack(fill='x', pady=20)
    def show_error_message(chinese_msg, english_msg):
        auth_x = auth_window.winfo_x()
        auth_y = auth_window.winfo_y()
        auth_width = auth_window.winfo_width()
        auth_height = auth_window.winfo_height()
        error_window = tk.Toplevel(auth_window)
        error_window.title("验证失败 Authentication Failed")
        error_width = 400
        error_height = 200
        error_x = auth_x + (auth_width - error_width) // 2
        error_y = auth_y + (auth_height - error_height) // 2
        error_window.geometry(f'{error_width}x{error_height}+{error_x}+{error_y}')
        error_window.resizable(False, False)
        error_window.attributes('-topmost', True)
        error_window.configure(bg="#000000")
        error_frame = tk.Frame(error_window, bg="#000000")
        error_frame.pack(expand=True, fill='both', padx=20, pady=20)
        error_cn = tk.Label(error_frame, text=chinese_msg,
                           font=chinese_font, bg="#000000", fg="#ffffff",
                           wraplength=350, justify='center')
        error_cn.pack(pady=(10, 5))
        error_en = tk.Label(error_frame, text=english_msg,
                           font=english_font, bg="#000000", fg="#ffffff",
                           wraplength=350, justify='center')
        error_en.pack(pady=(5, 15))
        ok_button = tk.Button(error_frame, text="确定 OK", command=error_window.destroy,
                             font=chinese_font, bg="#ffffff", fg="#000000",
                             relief='flat', padx=20, pady=15, height=2)
        ok_button.pack()
    def on_verify():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        if not username or not password:
            show_error_message("请输入完整的用户名和密码", "Please enter complete username and password")
            return
        if verify_user(username, password):
            EncryptedParams['StoredUsername'] = username
            EncryptedParams['StoredPassword'] = password
            SaveConfigParams()
            result['authenticated'] = True
            auth_window.destroy()
        else:
            show_error_message("用户名或密码不正确", "Incorrect username or password")
    def on_try():
        result['authenticated'] = False
        auth_window.destroy()
    trial_days = get_trial_days_left()
    verify_button = tk.Button(button_frame, text="验证登录\nVerify Login",
                             command=on_verify, font=chinese_font,
                             bg="#ffffff", fg="#000000", relief='flat',
                             padx=20, pady=15, height=1)
    verify_button.pack(side='left', padx=10, expand=True, fill='x')
    try_button = tk.Button(button_frame, text=f"试用模式 ({trial_days}天)\nTrial Mode ({trial_days} days)",
                          command=on_try, font=chinese_font,
                          bg="#ffffff", fg="#000000", relief='flat',
                          padx=20, pady=15, height=1)
    try_button.pack(side='right', padx=10, expand=True, fill='x')
    info_frame = ttk.Frame(main_frame, style='Auth.TFrame')
    info_frame.pack(fill='x', pady=15)
    info_cn = tk.Label(info_frame, text="请输入用户名和密码进行验证，或选择试用模式",
                      font=chinese_font, bg="#000000", fg="#ffffff",
                       justify='center')
    info_cn.pack()
    info_en = tk.Label(info_frame, text="Please enter username and password or choose trial mode",
                      font=english_font, bg="#000000", fg="#ffffff",
                       justify='center')
    info_en.pack()
    register_frame = ttk.Frame(main_frame, style='Auth.TFrame')
    register_frame.pack(fill='x', pady=10)
    def open_website(event):
        webbrowser.open("https://www.aistrucx.com/login?type=signup&tn=tju")
    register_cn = tk.Label(register_frame, text="点击进入熵纳科技官网注册",
                          font=chinese_font, bg="#000000", fg="#ffffff", cursor="hand2")
    register_cn.pack()
    register_cn.bind("<Button-1>", open_website)
    register_en = tk.Label(register_frame, text="Click to enter Entropy Technology website for registration",
                          font=english_font, bg="#000000", fg="#ffffff", cursor="hand2")
    register_en.pack()
    register_en.bind("<Button-1>", open_website)
    username_entry.focus()
    def on_enter(event):
        if event.widget == username_entry:
            password_entry.focus()
        elif event.widget == password_entry:
            on_verify()
    username_entry.bind('<Return>', on_enter)
    password_entry.bind('<Return>', on_enter)
    auth_window.grab_set()
    auth_window.wait_window()
    return result['authenticated']
def check_trial_expiration():
    install_date_str = EncryptedParams.get('InstallDate')
    if not install_date_str:
        install_date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        EncryptedParams['InstallDate'] = install_date_str
        SaveConfigParams()
    try:
        install_date = datetime.datetime.strptime(install_date_str, '%Y-%m-%d')
        today = datetime.datetime.now()
        delta = datetime.timedelta(days=30) - (today - install_date)
        days_left = max(0, delta.days)
        temp_root = tk.Tk()
        temp_root.withdraw()
        if days_left > 0:
            trial_window = tk.Toplevel(temp_root)
            trial_window.title("试用期提示 Trial Period Notice")
            trial_window.geometry('450x250')
            trial_window.resizable(False, False)
            trial_window.attributes('-topmost', True)
            trial_window.configure(bg="#000000")
            x = (trial_window.winfo_screenwidth() // 2) - 225
            y = (trial_window.winfo_screenheight() // 2) - 125
            trial_window.geometry(f'450x250+{x}+{y}')
            chinese_font = ('楷体', 17)
            english_font = ('Times New Roman', 17)
            main_frame = tk.Frame(trial_window, bg="#000000")
            main_frame.pack(expand=True, fill='both', padx=20, pady=20)
            msg_cn = tk.Label(main_frame, text=f"此软件为测试版，剩余使用天数：{days_left} 天",
                             font=chinese_font, bg="#000000", fg="#ffffff",
                             wraplength=400, justify='center')
            msg_cn.pack(pady=(10, 5))
            msg_en = tk.Label(main_frame, text=f"This software is trial version, remaining days: {days_left}",
                             font=english_font, bg="#000000", fg="#ffffff",
                             wraplength=400, justify='center')
            msg_en.pack(pady=(5, 20))
            ok_button = tk.Button(main_frame, text="确定 OK", command=trial_window.destroy,
                                 font=chinese_font, bg="#ffffff", fg="#000000",
                                 relief='flat', padx=30, pady=10)
            ok_button.pack()
            trial_window.grab_set()
            trial_window.wait_window()
        else:
            expired_window = tk.Toplevel(temp_root)
            expired_window.title("试用期已过 Trial Expired")
            expired_window.geometry('500x300')
            expired_window.resizable(False, False)
            expired_window.attributes('-topmost', True)
            expired_window.configure(bg="#000000")
            x = (expired_window.winfo_screenwidth() // 2) - 250
            y = (expired_window.winfo_screenheight() // 2) - 150
            expired_window.geometry(f'500x300+{x}+{y}')
            chinese_font = ('楷体', 17)
            english_font = ('Times New Roman', 17)
            main_frame = tk.Frame(expired_window, bg="#000000")
            main_frame.pack(expand=True, fill='both', padx=20, pady=20)
            msg_cn = tk.Label(main_frame, text="测试版试用期已结束！",
                             font=chinese_font, bg="#000000", fg="#ffffff",
                             wraplength=450, justify='center')
            msg_cn.pack(pady=(10, 5))
            msg_en = tk.Label(main_frame, text="Trial period has ended!",
                             font=english_font, bg="#000000", fg="#ffffff",
                             wraplength=450, justify='center')
            msg_en.pack(pady=(5, 10))
            info_cn = tk.Label(main_frame, text="请在登录界面点击链接进行注册",
                              font=chinese_font, bg="#000000", fg="#ffffff",
                              wraplength=450, justify='center')
            info_cn.pack(pady=(5, 5))
            info_en = tk.Label(main_frame, text="Please register via the link on login page",
                              font=english_font, bg="#000000", fg="#ffffff",
                              wraplength=450, justify='center')
            info_en.pack(pady=(5, 20))
            def exit_app():
                expired_window.destroy()
                temp_root.destroy()
                sys.exit(0)
            exit_button = tk.Button(main_frame, text="退出 Exit", command=exit_app,
                                   font=chinese_font, bg="#ffffff", fg="#000000",
                                   relief='flat', padx=30, pady=10)
            exit_button.pack()
            expired_window.grab_set()
            expired_window.wait_window()
        temp_root.destroy()
        return days_left
    except Exception as e:
        print(f"Date check error: {e}")
        return 30
from GUI import ModernGUI
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    authenticated = user_authentication()
    days_left = 30
    if not authenticated:
        days_left = check_trial_expiration()
    root.deiconify()
    if authenticated:
        title = "Deep Review V1.0 - Advanced (Licensed)"
    else:
        title = f"Deep Review V1.0 - Advanced (Trial {days_left} days left)"
    root.title(title)
    app = ModernGUI(root, authenticated, days_left)
    root.update_idletasks()
    width = 900
    height = 700
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    root.minsize(800, 600)
    root.update_idletasks()
    root.attributes('-topmost', True)
    root.update()
    root.attributes('-topmost', False)
    root.mainloop()
    if not os.path.basename(sys.executable).lower().startswith('python'):
        ExecuteCommand(f"TASKKILL /F /IM {os.path.basename(sys.executable)}")
