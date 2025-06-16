import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font
import os, sys, json, time, shutil, threading, traceback, functools, subprocess, re
import webbrowser
from __main__ import (
    RootDirectory, GlobalStopFlag, TempOutputFilePath, IsProcessRunning,
    IsLLMCheckRunning, HasLLMBeenChecked, WindowsTextLength,
    ConfigParams, ConfigParamLists, EncryptedParams, EncryptedParamLists,
    ClaudeApiFunctions, OpenAIApiFunctions, TextOutputRedirector,
    LogToFile, KillAllPythonProcesses, ExecuteCommand, SaveConfigParams,
    load_language_resources
)
import psutil
import Utility.License, Utility.GetResponse
import LiteratureSearch.One_key_download, MultiDownload.One_key_download
import TopicFormulation.GetQuestionsFromReview
import KnowledgeExtraction.XMLFormattedPrompt, KnowledgeExtraction.GetAllResponse, \
    KnowledgeExtraction.AnswerIntegration, KnowledgeExtraction.SplitIntoFolders, KnowledgeExtraction.LinkAnswer
import ReviewComposition.GenerateParagraphOfReview, ReviewComposition.GenerateRatingsForReviewParagraphs, \
    ReviewComposition.ExtractSectionsWithTags, ReviewComposition.CompareTwoReviewArticles, \
    ReviewComposition.Advanced_ComparedScore
import LiteratureSearch.Advanced_Research
class TooltipManager:
    def __init__(self):
        self.tooltip_window = None
        self.tooltips = {}
    def create_tooltip(self, widget, text_key, gui_ref=None):
        def on_enter(event):
            self.show_tooltip(event, text_key, gui_ref)
        def on_leave(event):
            self.hide_tooltip()
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        self.tooltips[widget] = {'key': text_key, 'gui_ref': gui_ref}
    def show_tooltip(self, event, text_key, gui_ref=None):
        if self.tooltip_window:
            self.hide_tooltip()
        x = event.widget.winfo_rootx() + 20
        y = event.widget.winfo_rooty() + 20
        self.tooltip_window = tk.Toplevel()
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        if gui_ref:
            text = gui_ref.translate(text_key)
        else:
            text = text_key
        label = tk.Label(self.tooltip_window, text=text, 
                        background="#ffffdd", foreground="#000000",
                        relief="solid", borderwidth=1,
                        font=("Times New Roman", 10))
        label.pack()
    def hide_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    def update_all_tooltips(self, gui_ref):
        pass
class ModernGUI:
    def __init__(self, root, authenticated=False, days_left=30):
        self.root = root
        self.authenticated = authenticated
        self.days_left = days_left
        self.lang_resources = load_language_resources()
        self.current_language = ConfigParams.get('Language', 'zh')
        self.current_theme = ConfigParams.get('Theme', 'dark')
        self.tooltip_manager = TooltipManager()
        self.log_expanded = False
        self.selected_llm_row = None
        self.selected_research_keyword_row = None
        self.selected_screen_keyword_row = None
        self.llm_actual_keys = {}
        self.setup_fonts_and_styles()
        self.apply_theme()
        self.create_main_interface()
        self.load_settings()
        self.update_title()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.main_process_thread = None
        self.main_process_pid = os.getpid()
        self.process_start_time = None
        self.stop_event = threading.Event()
        self.active_threads = []
    def translate(self, key, **kwargs):
        try:
            text = self.lang_resources.get(self.current_language, {}).get(key, key)
            if text == key:
                text = self.lang_resources.get('zh', {}).get(key, key)
            if kwargs:
                text = text.format(**kwargs)
            return text
        except Exception as e:
            print(f"Translation error for key '{key}': {e}")
            return key
    def setup_fonts_and_styles(self):
        import os
        import sys
        import tkinter.font as tkfont
        def get_resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        def get_font_name_simple(font_path):
            try:
                import struct
                with open(font_path, 'rb') as f:
                    f.seek(4)
                    num_tables = struct.unpack('>H', f.read(2))[0]
                    f.seek(12)
                    for _ in range(num_tables):
                        tag = f.read(4)
                        f.read(4)
                        offset = struct.unpack('>L', f.read(4))[0]
                        f.read(4)
                        if tag == b'name':
                            current_pos = f.tell()
                            f.seek(offset + 2)
                            count = struct.unpack('>H', f.read(2))[0]
                            string_offset = struct.unpack('>H', f.read(2))[0]
                            for _ in range(count):
                                platform_id = struct.unpack('>H', f.read(2))[0]
                                f.read(2)
                                f.read(2)
                                name_id = struct.unpack('>H', f.read(2))[0]
                                length = struct.unpack('>H', f.read(2))[0]
                                name_offset = struct.unpack('>H', f.read(2))[0]
                                if name_id == 1 and platform_id == 3:
                                    save_pos = f.tell()
                                    f.seek(offset + string_offset + name_offset)
                                    name_data = f.read(length)
                                    try:
                                        font_name = name_data.decode('utf-16-be').strip('\x00')
                                        if font_name:
                                            return font_name
                                    except:
                                        pass
                                    f.seek(save_pos)
                            f.seek(current_pos)
                            break
            except Exception as e:
                print(f"Error reading font name: {e}")
            return os.path.splitext(os.path.basename(font_path))[0]
        def is_font_available(font_name):
            try:
                test_font = tkfont.Font(family=font_name, size=12)
                actual_family = test_font.actual()['family']
                return font_name.lower() in actual_family.lower() or actual_family.lower() in font_name.lower()
            except Exception:
                return False
        def register_font_temporarily(font_path):
            try:
                if os.name == 'nt':
                    import ctypes
                    from ctypes import wintypes
                    FR_PRIVATE = 0x10
                    FR_NOT_ENUM = 0x20
                    gdi32 = ctypes.windll.gdi32
                    result = gdi32.AddFontResourceExW(
                        ctypes.c_wchar_p(font_path),
                        FR_PRIVATE | FR_NOT_ENUM,
                        None
                    )
                    if result > 0:
                        print(f"Font temporarily registered: {font_path}")
                        return True
                    else:
                        print(f"Failed to register font: {font_path}")
                        return False
                else:
                    return False
            except Exception as e:
                print(f"Error registering font: {e}")
                return False
        font_file = "font.ttf"
        font_path = get_resource_path(font_file)
        if os.path.exists(font_path):
            font_name = get_font_name_simple(font_path)
            if is_font_available(font_name):
                self.main_font = tkfont.Font(family=font_name, size=17)
                self.small_font = tkfont.Font(family=font_name, size=14)
                self.loaded_font_name = font_name
                self.font_file_path = font_path
            else:
                if register_font_temporarily(font_path):
                    if is_font_available(font_name):
                        self.main_font = tkfont.Font(family=font_name, size=17)
                        self.small_font = tkfont.Font(family=font_name, size=14)
                        self.loaded_font_name = font_name
                        self.font_file_path = font_path
                    else:
                        self.use_fallback_font()
                else:
                    self.use_fallback_font()
        else:
            self.use_fallback_font()
        self.style = ttk.Style()
        self.style.theme_use('default')
    def use_fallback_font(self):
        import tkinter.font as tkfont
        fallback_fonts = [
            "KaiTi",
            "Times New Roman"
        ]
        selected_font = None
        for font_name in fallback_fonts:
            try:
                test_font = tkfont.Font(family=font_name, size=12)
                actual_family = test_font.actual()['family']
                if font_name.lower() in actual_family.lower() or actual_family.lower() in font_name.lower():
                    selected_font = font_name
                    print(f"Using fallback font: {font_name}")
                    break
            except Exception:
                continue
        if not selected_font:
            selected_font = "楷体"
            print(f"Using final fallback font: {selected_font}")
        try:
            self.main_font = tkfont.Font(family=selected_font, size=17)
            self.small_font = tkfont.Font(family=selected_font, size=14)
        except Exception:
            self.main_font = (selected_font, 17)
            self.small_font = (selected_font, 14)
        self.loaded_font_name = selected_font
        self.font_file_path = None
    def create_font_from_file(self, size):
        import tkinter.font as tkfont
        if hasattr(self, 'loaded_font_name') and self.loaded_font_name:
            try:
                return tkfont.Font(family=self.loaded_font_name, size=size)
            except Exception as e:
                print(f"Error creating font: {e}")
                return tkfont.Font(family="楷体", size=size)
        else:
            return tkfont.Font(family="楷体", size=size)
    def update_labelframes_background(self, parent):
        try:
            for widget in parent.winfo_children():
                if isinstance(widget, ttk.LabelFrame):
                    try:
                        widget.configure(style='TLabelFrame')
                    except:
                        pass
                    try:
                        widget.configure(background=self.colors['frame_bg'])
                    except:
                        pass
                    self.update_labelframes_background(widget)
                elif hasattr(widget, 'winfo_children'):
                    self.update_labelframes_background(widget)
        except Exception as e:
            print(f"Error updating labelframe background: {e}")
    def apply_theme(self):
        if self.current_theme == 'dark':
            self.colors = {
                'bg': '#000000',
                'fg': '#ffffff',
                'select_bg': '#808080',
                'select_fg': '#ffffff',
                'entry_bg': '#000000',
                'entry_fg': '#ffffff',
                'button_bg': '#000000',
                'button_fg': '#ffffff',
                'frame_bg': '#000000',
                'progress_bg': '#000000',
                'progress_fill': '#ffffff',
            }
        else:
            self.colors = {
                'bg': '#ffffff',
                'fg': '#000000',
                'select_bg': '#e0e0e0',
                'select_fg': '#000000',
                'entry_bg': '#ffffff',
                'entry_fg': '#000000',
                'button_bg': '#f0f0f0',
                'button_fg': '#000000',
                'frame_bg': '#ffffff',
                'progress_bg': '#ffffff',
                'progress_fill': '#000000',
            }
        self.root.configure(bg=self.colors['bg'])
        self.style.configure('TFrame', background=self.colors['frame_bg'], borderwidth=0, relief='flat')
        self.style.configure('TLabel', background=self.colors['frame_bg'], foreground=self.colors['fg'], font=self.main_font)
        self.style.configure('TButton', background=self.colors['button_bg'], foreground=self.colors['button_fg'], font=self.main_font, borderwidth=1)
        self.style.configure('TEntry', fieldbackground=self.colors['entry_bg'], foreground=self.colors['entry_fg'], font=self.main_font, borderwidth=1)
        self.style.configure('TCheckbutton', background=self.colors['frame_bg'], foreground=self.colors['fg'], font=self.main_font)
        self.style.configure('TNotebook', background=self.colors['frame_bg'], borderwidth=0)
        self.style.configure('TNotebook.Tab', background=self.colors['frame_bg'], foreground=self.colors['fg'], font=self.main_font, borderwidth=1)
        self.style.map('TNotebook.Tab', background=[('selected', self.colors['select_bg'])])
        self.style.configure('TLabelFrame', 
                            background=self.colors['frame_bg'], 
                            foreground=self.colors['fg'], 
                            font=self.main_font, 
                            borderwidth=1,
                            relief='solid')
        self.style.configure('TLabelFrame.Label', 
                            background=self.colors['frame_bg'], 
                            foreground=self.colors['fg'], 
                            font=self.main_font)
        self.style.map('TLabelFrame', 
                      background=[('!disabled', self.colors['frame_bg']),
                                 ('disabled', self.colors['frame_bg']),
                                 ('active', self.colors['frame_bg']),
                                 ('!active', self.colors['frame_bg'])])
        self.style.configure('TProgressbar', 
                            background=self.colors['progress_fill'], 
                            troughcolor=self.colors['progress_bg'],
                            borderwidth=1,
                            relief='solid')
        self.style.configure('Vertical.TProgressbar', 
                           background=self.colors['progress_fill'], 
                           borderwidth=1,
                           troughcolor=self.colors['progress_bg'],
                           relief='solid')
        self.style.configure('Treeview', background=self.colors['entry_bg'], foreground=self.colors['fg'], 
                           fieldbackground=self.colors['entry_bg'], font=self.small_font)
        self.style.configure('Treeview.Heading', background=self.colors['button_bg'], foreground=self.colors['button_fg'], font=self.main_font)
        self.style.map('Treeview', background=[('selected', self.colors['select_bg'])],
                      foreground=[('selected', self.colors['select_fg'])])
        if hasattr(self, 'main_container'):
            self.main_container.configure(bg=self.colors['bg'])
        if hasattr(self, 'serp_listbox'):
            self.serp_listbox.configure(bg=self.colors['entry_bg'], fg=self.colors['entry_fg'], font=self.small_font)
        if hasattr(self, 'log_text'):
            self.log_text.configure(bg=self.colors['entry_bg'], fg=self.colors['entry_fg'], font=self.small_font)
        if hasattr(self, 'step_status_indicators'):
            for step_key, indicator in self.step_status_indicators.items():
                v_frame = indicator['vertical']['frame']
                v_icon=indicator['vertical']['icon']
                v_label = indicator['vertical']['label']
                v_frame.configure(bg=self.colors['frame_bg'])
                v_icon.configure(bg=self.colors['frame_bg'], fg=self.colors['fg'])
                v_label.configure(bg=self.colors['frame_bg'], fg=self.colors['fg'])
                h_frame = indicator['horizontal']['frame']
                h_label = indicator['horizontal']['label']
                h_icon = indicator['horizontal']['icon']
                h_frame.configure(bg=self.colors['frame_bg'])
                h_icon.configure(bg=self.colors['frame_bg'], fg=self.colors['fg'])
                h_label.configure(bg=self.colors['frame_bg'], fg=self.colors['fg'])
            if hasattr(self, 'vertical_status_frame'):
                self.vertical_status_frame.configure(bg=self.colors['frame_bg'])
            if hasattr(self, 'progress_v_frame'):
                self.progress_v_frame.configure(bg=self.colors['frame_bg'])
            if hasattr(self, 'horizontal_status_frame'):
                self.horizontal_status_frame.configure(bg=self.colors['frame_bg'])
        if hasattr(self, 'progress_v_canvas'):
            self.progress_v_canvas.configure(
                bg=self.colors['progress_bg'], 
                highlightthickness=1,
                highlightbackground=self.colors['progress_fill']
            )
            if hasattr(self, 'current_progress_value'):
                self.update_vertical_progress(self.current_progress_value)
        if hasattr(self, 'basic_frame'):
            self.update_labelframes_background(self.basic_frame)
        if hasattr(self, 'llm_frame'):
            self.update_labelframes_background(self.llm_frame)
        if hasattr(self, 'search_api_frame'):
            self.update_labelframes_background(self.search_api_frame)
        if hasattr(self, 'keywords_frame'):
            self.update_labelframes_background(self.keywords_frame)
        if hasattr(self, 'options_frame') and isinstance(self.options_frame, tk.LabelFrame):
            self.options_frame.configure(bg=self.colors['frame_bg'], 
                                        fg=self.colors['fg'],
                                        highlightbackground=self.colors['fg'],
                                        highlightcolor=self.colors['fg'])
        if hasattr(self, 'settings_frame') and isinstance(self.settings_frame, tk.LabelFrame):
            self.settings_frame.configure(bg=self.colors['frame_bg'], 
                                         fg=self.colors['fg'],
                                         highlightbackground=self.colors['fg'],
                                         highlightcolor=self.colors['fg'])
    def update_labelframes_background(self, parent):
        try:
            for widget in parent.winfo_children():
                if isinstance(widget, ttk.LabelFrame):
                    widget.configure(style='TLabelFrame')
                    try:
                        widget.configure(background=self.colors['frame_bg'])
                    except:
                        pass
                    self.update_labelframes_background(widget)
                elif hasattr(widget, 'winfo_children'):
                    self.update_labelframes_background(widget)
        except Exception as e:
            print(f"Error updating labelframe background: {e}")
    def create_main_interface(self):
        self.main_container = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.main_paned = tk.PanedWindow(self.main_container, orient=tk.HORIZONTAL, 
                                         bg=self.colors['bg'], sashwidth=5)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.left_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_panel, minsize=500)
        self.right_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_panel, minsize=160)
        self.notebook = ttk.Notebook(self.left_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.create_basic_tab()
        self.create_llm_tab()
        self.create_search_api_tab()
        self.create_keywords_tab()
        self.create_right_panel()
        self.create_bottom_buttons()
        self.root.after(100, lambda: self.update_vertical_progress(0))
    def create_basic_tab(self):
        self.basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_frame, text=self.translate('tab_basic'))
        control_frame = ttk.Frame(self.basic_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        theme_text = self.translate('theme_light') if self.current_theme == 'dark' else self.translate('theme_dark')
        self.theme_button = ttk.Button(control_frame, text=theme_text + " (?)", command=self.toggle_theme)
        self.theme_button.pack(side=tk.LEFT, padx=(0, 5))
        self.tooltip_manager.create_tooltip(self.theme_button, 'theme_help', self)
        lang_text = self.translate('language_en') if self.current_language == 'zh' else self.translate('language_zh')
        self.lang_button = ttk.Button(control_frame, text=lang_text + " (?)", command=self.toggle_language)
        self.lang_button.pack(side=tk.LEFT)
        self.tooltip_manager.create_tooltip(self.lang_button, 'language_help', self)
        topic_frame = ttk.Frame(self.basic_frame)
        topic_frame.pack(fill=tk.X, padx=10, pady=5)
        topic_label = ttk.Label(topic_frame, text=self.translate('topic') + " (?)")
        topic_label.pack(side=tk.LEFT)
        self.tooltip_manager.create_tooltip(topic_label, 'topic_help', self)
        self.topic_var = tk.StringVar(value=ConfigParams.get('Topic', ''))
        self.topic_entry = ttk.Entry(topic_frame, textvariable=self.topic_var)
        self.topic_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        self.topic_var.trace('w', self.on_setting_changed)
        options_frame = tk.LabelFrame(self.basic_frame, text="Options (?)", 
                                      bg=self.colors['frame_bg'], 
                                      fg=self.colors['fg'],
                                      font=self.main_font,
                                      bd=2,
                                      relief='solid',
                                      )                   
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        self.tooltip_manager.create_tooltip(options_frame, 'options_help', self)
        self.options_frame = options_frame
        self.demo_var = tk.BooleanVar(value=ConfigParams.get('Demo', True))
        demo_cb = ttk.Checkbutton(options_frame, text=self.translate('demo_mode') + " (?)", 
                                 variable=self.demo_var, command=self.on_setting_changed)
        demo_cb.pack(anchor=tk.W, padx=5, pady=2)
        self.tooltip_manager.create_tooltip(demo_cb, 'demo_mode_help', self)
        self.skip_search_var = tk.BooleanVar(value=ConfigParams.get('SkipSearching', False))
        skip_search_cb = ttk.Checkbutton(options_frame, text=self.translate('skip_search') + " (?)", 
                                        variable=self.skip_search_var, command=self.on_setting_changed)
        skip_search_cb.pack(anchor=tk.W, padx=5, pady=2)
        self.tooltip_manager.create_tooltip(skip_search_cb, 'skip_search_help', self)
        self.skip_topic_var = tk.BooleanVar(value=ConfigParams.get('SkipTopicFormulation', False))
        skip_topic_cb = ttk.Checkbutton(options_frame, text=self.translate('skip_topic') + " (?)", 
                                       variable=self.skip_topic_var, command=self.on_setting_changed)
        skip_topic_cb.pack(anchor=tk.W, padx=5, pady=2)
        self.tooltip_manager.create_tooltip(skip_topic_cb, 'skip_topic_help', self)
        self.skip_knowledge_var = tk.BooleanVar(value=ConfigParams.get('SkipKnowledgeExtraction', False))
        skip_knowledge_cb = ttk.Checkbutton(options_frame, text=self.translate('skip_knowledge') + " (?)", 
                                           variable=self.skip_knowledge_var, command=self.on_setting_changed)
        skip_knowledge_cb.pack(anchor=tk.W, padx=5, pady=2)
        self.tooltip_manager.create_tooltip(skip_knowledge_cb, 'skip_knowledge_help', self)
        self.skip_review_var = tk.BooleanVar(value=ConfigParams.get('SkipReviewComposition', False))
        skip_review_cb = ttk.Checkbutton(options_frame, text=self.translate('skip_review') + " (?)", 
                                        variable=self.skip_review_var, command=self.on_setting_changed)
        skip_review_cb.pack(anchor=tk.W, padx=5, pady=2)
        self.tooltip_manager.create_tooltip(skip_review_cb, 'skip_review_help', self)
        self.skip_compare_var = tk.BooleanVar(value=ConfigParams.get('SkipCompareTwoReviewArticles', False))
        self.direct_topic_var = tk.BooleanVar(value=ConfigParams.get('DirectTopicGeneration', False))
        direct_topic_cb = ttk.Checkbutton(options_frame, text=self.translate('direct_topic') + " (?)", 
                                         variable=self.direct_topic_var, command=self.on_setting_changed)
        direct_topic_cb.pack(anchor=tk.W, padx=5, pady=2)
        self.tooltip_manager.create_tooltip(direct_topic_cb, 'direct_topic_help', self)
        settings_frame = tk.LabelFrame(self.basic_frame, text="Search Settings (?)",
                                       bg=self.colors['frame_bg'], 
                                       fg=self.colors['fg'],
                                       font=self.main_font,
                                       bd=2,
                                       relief='solid',
                                       )                   
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        self.tooltip_manager.create_tooltip(settings_frame, 'search_settings_help', self)
        self.settings_frame = settings_frame
        journal_frame = ttk.Frame(settings_frame)
        journal_frame.pack(fill=tk.X, padx=5, pady=2)
        journal_label = ttk.Label(journal_frame, text=self.translate('journal_selection') + " (?)")
        journal_label.pack(side=tk.LEFT)
        self.tooltip_manager.create_tooltip(journal_label, 'journal_selection_help', self)
        self.q1_var = tk.BooleanVar(value=ConfigParams.get('Q1', True))
        q1_cb = ttk.Checkbutton(journal_frame, text=self.translate('q1_journals') + " (?)", 
                       variable=self.q1_var, command=self.on_setting_changed)
        q1_cb.pack(side=tk.LEFT, padx=10)
        self.tooltip_manager.create_tooltip(q1_cb, 'q1_journals_help', self)
        self.q2q3_var = tk.BooleanVar(value=ConfigParams.get('Q2&Q3', False))
        q2q3_cb = ttk.Checkbutton(journal_frame, text=self.translate('q2q3_journals') + " (?)", 
                       variable=self.q2q3_var, command=self.on_setting_changed)
        q2q3_cb.pack(side=tk.LEFT, padx=10)
        self.tooltip_manager.create_tooltip(q2q3_cb, 'q2q3_journals_help', self)
        self.custom_journals_button=ttk.Button(journal_frame, text=self.translate('custom_journals') + " (?)", 
                  command=self.open_journal_editor)
        self.custom_journals_button.pack(side=tk.LEFT, padx=10)
        self.tooltip_manager.create_tooltip(self.custom_journals_button, 'custom_journals_help', self)
        year_frame = ttk.Frame(settings_frame)
        year_frame.pack(fill=tk.X, padx=5, pady=2)
        start_year_label = ttk.Label(year_frame, text=self.translate('start_year') + " (?)")
        start_year_label.pack(side=tk.LEFT)
        self.tooltip_manager.create_tooltip(start_year_label, 'start_year_help', self)
        self.start_year_var = tk.StringVar(value=ConfigParams.get('StartYear', '2020'))
        start_year_entry = ttk.Entry(year_frame, textvariable=self.start_year_var, width=8)
        start_year_entry.pack(side=tk.LEFT, padx=5)
        self.start_year_var.trace('w', self.on_setting_changed)
        end_year_label = ttk.Label(year_frame, text=self.translate('end_year') + " (?)")
        end_year_label.pack(side=tk.LEFT, padx=(20, 0))
        self.tooltip_manager.create_tooltip(end_year_label, 'end_year_help', self)
        self.end_year_var = tk.StringVar(value=ConfigParams.get('EndYear', '2024'))
        end_year_entry = ttk.Entry(year_frame, textvariable=self.end_year_var, width=8)
        end_year_entry.pack(side=tk.LEFT, padx=5)
        self.end_year_var.trace('w', self.on_setting_changed)
        papers_frame = ttk.Frame(settings_frame)
        papers_frame.pack(fill=tk.X, padx=5, pady=2)
        papers_label = ttk.Label(papers_frame, text=self.translate('max_papers') + " (?)")
        papers_label.pack(side=tk.LEFT)
        self.tooltip_manager.create_tooltip(papers_label, 'max_papers_help', self)
        self.max_papers_var = tk.StringVar(value=str(ConfigParams.get('MaxPapers', 100)))
        papers_entry = ttk.Entry(papers_frame, textvariable=self.max_papers_var, width=8)
        papers_entry.pack(side=tk.LEFT, padx=5)
        self.max_papers_var.trace('w', self.on_setting_changed)
    def update_labelframes_background(self, parent):
        try:
            for widget in parent.winfo_children():
                if isinstance(widget, (ttk.LabelFrame, tk.LabelFrame)):
                    if isinstance(widget, tk.LabelFrame):
                        widget.configure(bg=self.colors['frame_bg'], 
                                       fg=self.colors['fg'],
                                       highlightbackground=self.colors['fg'],
                                       highlightcolor=self.colors['fg'])
                    else:
                        try:
                            widget.configure(style='TLabelFrame')
                        except:
                            pass
                        try:
                            widget.configure(background=self.colors['frame_bg'])
                        except:
                            pass
                    self.update_labelframes_background(widget)
                elif hasattr(widget, 'winfo_children'):
                    self.update_labelframes_background(widget)
        except Exception as e:
            print(f"Error updating labelframe background: {e}")
    def create_llm_tab(self):
        self.llm_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.llm_frame, text=self.translate('tab_llm'))
        input_frame = ttk.Frame(self.llm_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        model_label = ttk.Label(input_frame, text=self.translate('model_name') + " (?)")
        model_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.tooltip_manager.create_tooltip(model_label, 'model_name_help', self)
        self.llm_model_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.llm_model_var, width=20).grid(row=0, column=1, padx=5)
        url_label = ttk.Label(input_frame, text=self.translate('base_url') + " (?)")
        url_label.grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.tooltip_manager.create_tooltip(url_label, 'base_url_help', self)
        self.llm_url_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.llm_url_var, width=30).grid(row=0, column=3, padx=5)
        key_label = ttk.Label(input_frame, text=self.translate('api_key') + " (?)")
        key_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        self.tooltip_manager.create_tooltip(key_label, 'api_key_help', self)
        self.llm_key_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.llm_key_var, width=40, show="*").grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        tokens_frame = ttk.Frame(input_frame)
        tokens_frame.grid(row=1, column=3, columnspan=2, sticky=tk.W, padx=5, pady=5)
        tokens_label = ttk.Label(tokens_frame, text=self.translate('max_tokens') + " (?)")
        tokens_label.pack(side=tk.LEFT)
        self.tooltip_manager.create_tooltip(tokens_label, 'max_tokens_help', self)
        self.llm_tokens_var = tk.StringVar()
        ttk.Entry(tokens_frame, textvariable=self.llm_tokens_var, width=10).pack(side=tk.LEFT, padx=(3, 0))
        concurrency_label = ttk.Label(input_frame, text=self.translate('concurrency') + " (?)")
        concurrency_label.grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        self.tooltip_manager.create_tooltip(concurrency_label, 'concurrency_help', self)
        self.llm_concurrency_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.llm_concurrency_var, width=10).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        buttons_frame = ttk.Frame(self.llm_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        self.llm_add_button = ttk.Button(buttons_frame, text=self.translate('add') + " (?)", command=self.add_llm_config)
        self.llm_add_button.pack(side=tk.LEFT, padx=(0, 5))
        self.tooltip_manager.create_tooltip(self.llm_add_button, 'add_llm_help', self)
        delete_button = ttk.Button(buttons_frame, text=self.translate('delete') + " (?)", command=self.delete_llm_config)
        delete_button.pack(side=tk.LEFT, padx=5)
        self.tooltip_manager.create_tooltip(delete_button, 'delete_llm_help', self)
        test_selected_button = ttk.Button(buttons_frame, text=self.translate('test_selected') + " (?)", command=self.test_selected_llm)
        test_selected_button.pack(side=tk.LEFT, padx=5)
        self.tooltip_manager.create_tooltip(test_selected_button, 'test_selected_help', self)
        test_all_button = ttk.Button(buttons_frame, text=self.translate('test_all') + " (?)", command=self.test_all_llm)
        test_all_button.pack(side=tk.LEFT, padx=5)
        self.tooltip_manager.create_tooltip(test_all_button, 'test_all_help', self)
        table_frame = ttk.Frame(self.llm_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        columns = ('model', 'url', 'key', 'tokens', 'concurrency', 'status')
        self.llm_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=8)
        self.llm_tree.heading('model', text=self.translate('model_name'), command=lambda: self.sort_tree(self.llm_tree, 'model'))
        self.llm_tree.heading('url', text=self.translate('base_url'), command=lambda: self.sort_tree(self.llm_tree, 'url'))
        self.llm_tree.heading('key', text=self.translate('api_key'), command=lambda: self.sort_tree(self.llm_tree, 'key'))
        self.llm_tree.heading('tokens', text=self.translate('max_tokens'), command=lambda: self.sort_tree(self.llm_tree, 'tokens'))
        self.llm_tree.heading('concurrency', text=self.translate('concurrency'), command=lambda: self.sort_tree(self.llm_tree, 'concurrency'))
        self.llm_tree.heading('status', text=self.translate('status'), command=lambda: self.sort_tree(self.llm_tree, 'status'))
        self.llm_tree.column('model', width=120, minwidth=20)
        self.llm_tree.column('url', width=200, minwidth=100)
        self.llm_tree.column('key', width=120, minwidth=50)
        self.llm_tree.column('tokens', width=80, minwidth=30)
        self.llm_tree.column('concurrency', width=80, minwidth=30)
        self.llm_tree.column('status', width=100, minwidth=30)
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.llm_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.llm_tree.xview)
        self.llm_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.llm_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.llm_tree.bind('<ButtonRelease-1>', self.on_llm_select)
        self.llm_tree.bind('<Button-1>', self.on_llm_click)
        self.load_llm_configs()
    def create_search_api_tab(self):
        self.search_api_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_api_frame, text=self.translate('tab_search_api'))
        serp_frame = tk.LabelFrame(self.search_api_frame, text=self.translate('serp_api') + " (?)",
                                   bg=self.colors['frame_bg'], 
                                   fg=self.colors['fg'],
                                   font=self.main_font,
                                   bd=2,
                                   relief='solid')
        serp_frame.pack(fill=tk.X, padx=10, pady=5)
        self.tooltip_manager.create_tooltip(serp_frame, 'serp_api_help', self)
        serp_input_frame = ttk.Frame(serp_frame)
        serp_input_frame.pack(fill=tk.X, padx=5, pady=5)
        serp_label = ttk.Label(serp_input_frame, text=self.translate('serp_api') + " (?)")
        serp_label.pack(side=tk.LEFT)
        self.tooltip_manager.create_tooltip(serp_label, 'serp_api_help', self)
        self.serp_var = tk.StringVar()
        ttk.Entry(serp_input_frame, textvariable=self.serp_var, width=40, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.serp_add_button = ttk.Button(serp_input_frame, text=self.translate('add') + " (?)", command=self.add_serp_api)
        self.serp_add_button.pack(side=tk.LEFT, padx=5)
        self.tooltip_manager.create_tooltip(self.serp_add_button, 'add_serp_help', self)
        serp_delete_button = ttk.Button(serp_input_frame, text=self.translate('delete') + " (?)", command=self.delete_serp_api)
        serp_delete_button.pack(side=tk.LEFT, padx=5)
        self.tooltip_manager.create_tooltip(serp_delete_button, 'delete_serp_help', self)
        serp_table_frame = ttk.Frame(serp_frame)
        serp_table_frame.pack(fill=tk.X, padx=5, pady=5)
        columns = ('api_key',)
        self.serp_tree = ttk.Treeview(serp_table_frame, columns=columns, show='headings', height=8)
        self.serp_tree.heading('api_key', text=self.translate('serp_api'), command=lambda: self.sort_tree(self.serp_tree, 'api_key'))
        self.serp_tree.column('api_key', width=400, minwidth=200)
        serp_scrollbar = ttk.Scrollbar(serp_table_frame, orient=tk.VERTICAL, command=self.serp_tree.yview)
        self.serp_tree.configure(yscrollcommand=serp_scrollbar.set)
        self.serp_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        serp_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.serp_tree.bind('<Double-Button-1>', self.remove_serp_api)
        self.serp_tree.bind('<ButtonRelease-1>', self.on_serp_select)
        self.serp_tree.bind('<Button-1>', self.on_serp_click)
        self.tooltip_manager.create_tooltip(self.serp_tree, 'serp_list_help', self)
        elsevier_frame = tk.LabelFrame(self.search_api_frame, text=self.translate('elsevier_api') + " (?)",
                                       bg=self.colors['frame_bg'], 
                                       fg=self.colors['fg'],
                                       font=self.main_font,
                                       bd=2,
                                       relief='solid')
        elsevier_frame.pack(fill=tk.X, padx=10, pady=5)
        self.tooltip_manager.create_tooltip(elsevier_frame, 'elsevier_api_help', self)
        elsevier_input_frame = ttk.Frame(elsevier_frame)
        elsevier_input_frame.pack(fill=tk.X, padx=5, pady=5)
        elsevier_label = ttk.Label(elsevier_input_frame, text=self.translate('elsevier_api') + " (?)")
        elsevier_label.pack(side=tk.LEFT)
        self.tooltip_manager.create_tooltip(elsevier_label, 'elsevier_api_help', self)
        self.elsevier_var = tk.StringVar()
        ttk.Entry(elsevier_input_frame, textvariable=self.elsevier_var, width=40, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.elsevier_add_button = ttk.Button(elsevier_input_frame, text=self.translate('add') + " (?)", command=self.add_elsevier_api)
        self.elsevier_add_button.pack(side=tk.LEFT, padx=5)
        self.tooltip_manager.create_tooltip(self.elsevier_add_button, 'add_elsevier_help', self)
        elsevier_delete_button = ttk.Button(elsevier_input_frame, text=self.translate('delete') + " (?)", command=self.delete_elsevier_api)
        elsevier_delete_button.pack(side=tk.LEFT, padx=5)
        self.tooltip_manager.create_tooltip(elsevier_delete_button, 'delete_elsevier_help', self)
        elsevier_table_frame = ttk.Frame(elsevier_frame)
        elsevier_table_frame.pack(fill=tk.X, padx=5, pady=5)
        columns = ('api_key',)
        self.elsevier_tree = ttk.Treeview(elsevier_table_frame, columns=columns, show='headings', height=8)
        self.elsevier_tree.heading('api_key', text=self.translate('elsevier_api'), command=lambda: self.sort_tree(self.elsevier_tree, 'api_key'))
        self.elsevier_tree.column('api_key', width=400, minwidth=200)
        elsevier_scrollbar = ttk.Scrollbar(elsevier_table_frame, orient=tk.VERTICAL, command=self.elsevier_tree.yview)
        self.elsevier_tree.configure(yscrollcommand=elsevier_scrollbar.set)
        self.elsevier_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        elsevier_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.elsevier_tree.bind('<Double-Button-1>', self.remove_elsevier_api)
        self.elsevier_tree.bind('<ButtonRelease-1>', self.on_elsevier_select)
        self.elsevier_tree.bind('<Button-1>', self.on_elsevier_click)
        self.tooltip_manager.create_tooltip(self.elsevier_tree, 'elsevier_list_help', self)
        self.selected_serp_row = None
        self.selected_elsevier_row = None
        self.load_search_apis()
    def on_serp_select(self, event):
        selection = self.serp_tree.selection()
        if selection:
            self.selected_serp_row = selection[0]
            index = self.serp_tree.index(self.selected_serp_row)
            if 'SerpApiList' in EncryptedParamLists and index < len(EncryptedParamLists['SerpApiList']):
                actual_key = EncryptedParamLists['SerpApiList'][index]
                display_key = '*'*5+actual_key[-4:] if len(actual_key) >= 4 else '*'*8
                self.serp_var.set(display_key)
                self.serp_add_button.config(text=self.translate('update') + " (?)")
        else:
            self.selected_serp_row = None
            self.serp_var.set('')
            self.serp_add_button.config(text=self.translate('add') + " (?)")
    def on_serp_click(self, event):
        region = self.serp_tree.identify_region(event.x, event.y)
        if region == "nothing":
            self.serp_tree.selection_remove(self.serp_tree.selection())
            self.selected_serp_row = None
            self.serp_var.set('')
            self.serp_add_button.config(text=self.translate('add') + " (?)")
    def on_elsevier_select(self, event):
        selection = self.elsevier_tree.selection()
        if selection:
            self.selected_elsevier_row = selection[0]
            index = self.elsevier_tree.index(self.selected_elsevier_row)
            if 'ElsevierApiList' in EncryptedParamLists and index < len(EncryptedParamLists['ElsevierApiList']):
                actual_key = EncryptedParamLists['ElsevierApiList'][index]
                display_key = '*'*5+actual_key[-4:] if len(actual_key) >= 4 else '*'*8
                self.elsevier_var.set(display_key)
                self.elsevier_add_button.config(text=self.translate('update') + " (?)")
        else:
            self.selected_elsevier_row = None
            self.elsevier_var.set('')
            self.elsevier_add_button.config(text=self.translate('add') + " (?)")
    def on_elsevier_click(self, event):
        region = self.elsevier_tree.identify_region(event.x, event.y)
        if region == "nothing":
            self.elsevier_tree.selection_remove(self.elsevier_tree.selection())
            self.selected_elsevier_row = None
            self.elsevier_var.set('')
            self.elsevier_add_button.config(text=self.translate('add') + " (?)")
    def delete_serp_api(self):
        if not self.selected_serp_row:
            messagebox.showwarning(self.translate('no_selection'), self.translate('no_api_selected'))
            return
        if messagebox.askyesno(self.translate('confirm_delete'), self.translate('delete_confirmation')):
            index = self.serp_tree.index(self.selected_serp_row)
            if 'SerpApiList' in EncryptedParamLists and index < len(EncryptedParamLists['SerpApiList']):
                deleted_key = EncryptedParamLists['SerpApiList'][index]
                display_key = '*'*5+deleted_key[-4:] if len(deleted_key) >= 4 else '*'*8
                EncryptedParamLists['SerpApiList'].pop(index)
                self.serp_tree.delete(self.selected_serp_row)
                SaveConfigParams()
                self.log(f"{self.translate('api_deleted')}: {display_key}")
            self.selected_serp_row = None
            self.serp_var.set('')
            self.serp_add_button.config(text=self.translate('add') + " (?)")
    def delete_elsevier_api(self):
        if not self.selected_elsevier_row:
            messagebox.showwarning(self.translate('no_selection'), self.translate('no_api_selected'))
            return
        if messagebox.askyesno(self.translate('confirm_delete'), self.translate('delete_confirmation')):
            index = self.elsevier_tree.index(self.selected_elsevier_row)
            if 'ElsevierApiList' in EncryptedParamLists and index < len(EncryptedParamLists['ElsevierApiList']):
                deleted_key = EncryptedParamLists['ElsevierApiList'][index]
                display_key = '*'*5+deleted_key[-4:] if len(deleted_key) >= 4 else '*'*8
                EncryptedParamLists['ElsevierApiList'].pop(index)
                self.elsevier_tree.delete(self.selected_elsevier_row)
                SaveConfigParams()
                self.log(f"{self.translate('api_deleted')}: {display_key}")
            self.selected_elsevier_row = None
            self.elsevier_var.set('')
            self.elsevier_add_button.config(text=self.translate('add') + " (?)")
    def on_research_keyword_select(self, event):
        selection = self.research_tree.selection()
        if selection:
            self.selected_research_keyword_row = selection[0]
            item = self.research_tree.item(self.selected_research_keyword_row)
            self.research_keyword_var.set(item['values'][0])
            self.research_add_button.config(text=self.translate('update') + " (?)")
        else:
            self.selected_research_keyword_row = None
            self.research_keyword_var.set('')
            self.research_add_button.config(text=self.translate('add') + " (?)")
    def on_research_keyword_click(self, event):
        region = self.research_tree.identify_region(event.x, event.y)
        if region == "nothing":
            self.research_tree.selection_remove(self.research_tree.selection())
            self.selected_research_keyword_row = None
            self.research_keyword_var.set('')
            self.research_add_button.config(text=self.translate('add') + " (?)")
    def on_screen_keyword_select(self, event):
        selection = self.screen_tree.selection()
        if selection:
            self.selected_screen_keyword_row = selection[0]
            item = self.screen_tree.item(self.selected_screen_keyword_row)
            self.screen_keyword_var.set(item['values'][0])
            self.screen_add_button.config(text=self.translate('update') + " (?)")
        else:
            self.selected_screen_keyword_row = None
            self.screen_keyword_var.set('')
            self.screen_add_button.config(text=self.translate('add') + " (?)")
    def on_screen_keyword_click(self, event):
        region = self.screen_tree.identify_region(event.x, event.y)
        if region == "nothing":
            self.screen_tree.selection_remove(self.screen_tree.selection())
            self.selected_screen_keyword_row = None
            self.screen_keyword_var.set('')
            self.screen_add_button.config(text=self.translate('add') + " (?)")
    def double_click_delete_research_keyword(self, event):
        selection = self.research_tree.selection()
        if selection:
            item = selection[0]
            keyword = self.research_tree.item(item)['values'][0]
            if messagebox.askyesno(self.translate('confirm_delete'), 
                                  f"{self.translate('delete_confirmation')}\n\n{keyword}"):
                index = self.research_tree.index(item)
                self.research_tree.delete(item)
                if 'ResearchKeys' in ConfigParamLists and index < len(ConfigParamLists['ResearchKeys']):
                    ConfigParamLists['ResearchKeys'].pop(index)
                SaveConfigParams()
                self.selected_research_keyword_row = None
                self.research_keyword_var.set('')
                self.research_add_button.config(text=self.translate('add') + " (?)")
                self.log(self.translate('keyword_deleted'))
    def double_click_delete_screen_keyword(self, event):
        selection = self.screen_tree.selection()
        if selection:
            item = selection[0]
            keyword = self.screen_tree.item(item)['values'][0]
            if messagebox.askyesno(self.translate('confirm_delete'), 
                                  f"{self.translate('delete_confirmation')}\n\n{keyword}"):
                index = self.screen_tree.index(item)
                self.screen_tree.delete(item)
                if 'ScreenKeys' in ConfigParamLists and index < len(ConfigParamLists['ScreenKeys']):
                    ConfigParamLists['ScreenKeys'].pop(index)
                SaveConfigParams()
                self.selected_screen_keyword_row = None
                self.screen_keyword_var.set('')
                self.screen_add_button.config(text=self.translate('add') + " (?)")
                self.log(self.translate('keyword_deleted'))
    def create_keywords_tab(self):
        self.keywords_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.keywords_frame, text=self.translate('tab_keywords'))
        research_frame = tk.LabelFrame(self.keywords_frame, text=self.translate('research_keywords') + " (?)",
                                       bg=self.colors['frame_bg'], 
                                       fg=self.colors['fg'],
                                       font=self.main_font,
                                       bd=2,
                                       relief='solid')
        research_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tooltip_manager.create_tooltip(research_frame, 'research_keywords_help', self)
        research_input_frame = ttk.Frame(research_frame)
        research_input_frame.pack(fill=tk.X, padx=5, pady=5)
        research_label = ttk.Label(research_input_frame, text=self.translate('keyword') + " (?)")
        research_label.pack(side=tk.LEFT)
        self.tooltip_manager.create_tooltip(research_label, 'research_keywords_help', self)
        self.research_keyword_var = tk.StringVar()
        ttk.Entry(research_input_frame, textvariable=self.research_keyword_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.research_add_button = ttk.Button(research_input_frame, text=self.translate('add') + " (?)", command=self.add_research_keyword)
        self.research_add_button.pack(side=tk.LEFT, padx=5)
        self.tooltip_manager.create_tooltip(self.research_add_button, 'add_research_keyword_help', self)
        research_delete_button = ttk.Button(research_input_frame, text=self.translate('delete') + " (?)", command=self.delete_research_keyword)
        research_delete_button.pack(side=tk.LEFT, padx=5)
        self.tooltip_manager.create_tooltip(research_delete_button, 'delete_research_keyword_help', self)
        research_table_frame = ttk.Frame(research_frame)
        research_table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        columns = ('keyword',)
        self.research_tree = ttk.Treeview(research_table_frame, columns=columns, show='headings', height=6)
        self.research_tree.heading('keyword', text=self.translate('research_keywords'), command=lambda: self.sort_tree(self.research_tree, 'keyword'))
        self.research_tree.column('keyword', width=300, minwidth=200)
        research_scrollbar = ttk.Scrollbar(research_table_frame, orient=tk.VERTICAL, command=self.research_tree.yview)
        self.research_tree.configure(yscrollcommand=research_scrollbar.set)
        self.research_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        research_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.research_tree.bind('<Double-Button-1>', self.double_click_delete_research_keyword)
        self.research_tree.bind('<ButtonRelease-1>', self.on_research_keyword_select)
        self.research_tree.bind('<Button-1>', self.on_research_keyword_click)
        self.tooltip_manager.create_tooltip(self.research_tree, 'research_tree_help', self)
        screen_frame = tk.LabelFrame(self.keywords_frame, text=self.translate('screen_keywords') + " (?)",
                                     bg=self.colors['frame_bg'], 
                                     fg=self.colors['fg'],
                                     font=self.main_font,
                                     bd=2,
                                     relief='solid')
        screen_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tooltip_manager.create_tooltip(screen_frame, 'screen_keywords_help', self)
        screen_input_frame = ttk.Frame(screen_frame)
        screen_input_frame.pack(fill=tk.X, padx=5, pady=5)
        screen_label = ttk.Label(screen_input_frame, text=self.translate('keyword') + " (?)")
        screen_label.pack(side=tk.LEFT)
        self.tooltip_manager.create_tooltip(screen_label, 'screen_keywords_help', self)
        self.screen_keyword_var = tk.StringVar()
        ttk.Entry(screen_input_frame, textvariable=self.screen_keyword_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.screen_add_button = ttk.Button(screen_input_frame, text=self.translate('add') + " (?)", command=self.add_screen_keyword)
        self.screen_add_button.pack(side=tk.LEFT, padx=5)
        self.tooltip_manager.create_tooltip(self.screen_add_button, 'add_screen_keyword_help', self)
        screen_delete_button = ttk.Button(screen_input_frame, text=self.translate('delete') + " (?)", command=self.delete_screen_keyword)
        screen_delete_button.pack(side=tk.LEFT, padx=5)
        self.tooltip_manager.create_tooltip(screen_delete_button, 'delete_screen_keyword_help', self)
        screen_table_frame = ttk.Frame(screen_frame)
        screen_table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        columns = ('keyword',)
        self.screen_tree = ttk.Treeview(screen_table_frame, columns=columns, show='headings', height=6)
        self.screen_tree.heading('keyword', text=self.translate('screen_keywords'), command=lambda: self.sort_tree(self.screen_tree, 'keyword'))
        self.screen_tree.column('keyword', width=300, minwidth=200)
        screen_scrollbar = ttk.Scrollbar(screen_table_frame, orient=tk.VERTICAL, command=self.screen_tree.yview)
        self.screen_tree.configure(yscrollcommand=screen_scrollbar.set)
        self.screen_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        screen_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.screen_tree.bind('<Double-Button-1>', self.double_click_delete_screen_keyword)
        self.screen_tree.bind('<ButtonRelease-1>', self.on_screen_keyword_select)
        self.screen_tree.bind('<Button-1>', self.on_screen_keyword_click)
        self.tooltip_manager.create_tooltip(self.screen_tree, 'screen_tree_help', self)
        self.load_keywords()
    def load_search_apis(self):
        self.serp_tree.delete(*self.serp_tree.get_children())
        for api in EncryptedParamLists.get('SerpApiList', []):
            display_key = '*'*5+api[-4:] if len(api) >= 4 else '*'*8
            self.serp_tree.insert('', tk.END, values=(display_key,))
        self.elsevier_tree.delete(*self.elsevier_tree.get_children())
        for api in EncryptedParamLists.get('ElsevierApiList', []):
            display_key = '*'*5+api[-4:] if len(api) >= 4 else '*'*8
            self.elsevier_tree.insert('', tk.END, values=(display_key,))
    def add_serp_api(self):
        api_key = self.serp_var.get().strip()
        if not api_key:
            return
        if self.selected_serp_row:
            index = self.serp_tree.index(self.selected_serp_row)
            if 'SerpApiList' in EncryptedParamLists and index < len(EncryptedParamLists['SerpApiList']):
                if api_key.startswith('*****') and len(api_key) >= 9:
                    self.log(self.translate('no_changes_made'))
                else:
                    EncryptedParamLists['SerpApiList'][index] = api_key
                    display_key = '*'*5+api_key[-4:] if len(api_key) >= 4 else '*'*8
                    self.serp_tree.item(self.selected_serp_row, values=(display_key,))
                    SaveConfigParams()
                    self.log(self.translate('api_updated'))
            self.selected_serp_row = None
            self.serp_var.set('')
            self.serp_add_button.config(text=self.translate('add') + " (?)")
        else:
            if not api_key.startswith('*****'):
                if api_key not in EncryptedParamLists.get('SerpApiList', []):
                    EncryptedParamLists.setdefault('SerpApiList', []).append(api_key)
                    display_key = '*'*5+api_key[-4:] if len(api_key) >= 4 else '*'*8
                    self.serp_tree.insert('', tk.END, values=(display_key,))
                    SaveConfigParams()
                    self.log(self.translate('api_added'))
            self.serp_var.set('')
    def remove_serp_api(self, event):
        selection = self.serp_tree.selection()
        if selection:
            item = selection[0]
            index = self.serp_tree.index(item)
            if messagebox.askyesno(self.translate('confirm_delete'), self.translate('delete_confirmation')):
                if 'SerpApiList' in EncryptedParamLists and index < len(EncryptedParamLists['SerpApiList']):
                    deleted_key = EncryptedParamLists['SerpApiList'][index]
                    display_key = '*'*5+deleted_key[-4:] if len(deleted_key) >= 4 else '*'*8
                    EncryptedParamLists['SerpApiList'].pop(index)
                    self.serp_tree.delete(item)
                    SaveConfigParams()
                    self.log(f"{self.translate('api_deleted')}: {display_key}")
                self.selected_serp_row = None
                self.serp_var.set('')
                self.serp_add_button.config(text=self.translate('add') + " (?)")
    def add_elsevier_api(self):
        api_key = self.elsevier_var.get().strip()
        if not api_key:
            return
        if 'ElsevierApiList' not in EncryptedParamLists:
            EncryptedParamLists['ElsevierApiList'] = []
        if self.selected_elsevier_row:
            index = self.elsevier_tree.index(self.selected_elsevier_row)
            if index < len(EncryptedParamLists['ElsevierApiList']):
                if api_key.startswith('*****') and len(api_key) >= 9:
                    self.log(self.translate('no_changes_made'))
                else:
                    EncryptedParamLists['ElsevierApiList'][index] = api_key
                    display_key = '*'*5+api_key[-4:] if len(api_key) >= 4 else '*'*8
                    self.elsevier_tree.item(self.selected_elsevier_row, values=(display_key,))
                    SaveConfigParams()
                    self.log(self.translate('api_updated'))
            self.selected_elsevier_row = None
            self.elsevier_var.set('')
            self.elsevier_add_button.config(text=self.translate('add') + " (?)")
        else:
            if not api_key.startswith('*****'):
                if api_key not in EncryptedParamLists['ElsevierApiList']:
                    EncryptedParamLists['ElsevierApiList'].append(api_key)
                    display_key = '*'*5+api_key[-4:] if len(api_key) >= 4 else '*'*8
                    self.elsevier_tree.insert('', tk.END, values=(display_key,))
                    SaveConfigParams()
                    self.log(self.translate('api_added'))
            self.elsevier_var.set('')
    def remove_elsevier_api(self, event):
        selection = self.elsevier_tree.selection()
        if selection:
            item = selection[0]
            index = self.elsevier_tree.index(item)
            if messagebox.askyesno(self.translate('confirm_delete'), self.translate('delete_confirmation')):
                if 'ElsevierApiList' in EncryptedParamLists and index < len(EncryptedParamLists['ElsevierApiList']):
                    deleted_key = EncryptedParamLists['ElsevierApiList'][index]
                    display_key = '*'*5+deleted_key[-4:] if len(deleted_key) >= 4 else '*'*8
                    EncryptedParamLists['ElsevierApiList'].pop(index)
                    self.elsevier_tree.delete(item)
                    SaveConfigParams()
                    self.log(f"{self.translate('api_deleted')}: {display_key}")
                self.selected_elsevier_row = None
                self.elsevier_var.set('')
                self.elsevier_add_button.config(text=self.translate('add') + " (?)")
    def create_right_panel(self):
        status_frame = ttk.Frame(self.right_panel)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        self.status_label = ttk.Label(status_frame, text=self.translate('status_ready') + " (?)", font=self.main_font)
        self.status_label.pack()
        self.tooltip_manager.create_tooltip(self.status_label, 'status_help', self)
        log_toggle_frame = ttk.Frame(self.right_panel)
        log_toggle_frame.pack(fill=tk.X, padx=5, pady=5)
        self.log_toggle_button = ttk.Button(log_toggle_frame, text=self.translate('expand_log') + " (?)", 
                                           command=self.toggle_log)
        self.log_toggle_button.pack()
        self.tooltip_manager.create_tooltip(self.log_toggle_button, 'log_toggle_help', self)
        self.progress_frame = ttk.Frame(self.right_panel)
        self.progress_h = ttk.Progressbar(self.progress_frame, mode='determinate', length=200, orient='horizontal')
        self.progress_h.pack(fill=tk.X, padx=5, pady=5)
        self.progress_label = ttk.Label(self.progress_frame, text="", font=self.small_font)
        self.progress_label.pack()
        self.horizontal_status_frame = tk.Frame(self.progress_frame, bg=self.colors['frame_bg'])
        self.progress_v_frame = tk.Frame(self.right_panel, bg=self.colors['frame_bg'])
        self.progress_v_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.progress_v_canvas = tk.Canvas(self.progress_v_frame, width=60,
                                           bg=self.colors['progress_bg'], 
                                           highlightthickness=1,
                                           highlightbackground=self.colors['progress_fill'])
        self.progress_v_canvas.pack(fill=tk.BOTH,expand=True, pady=10)
        self.vertical_status_frame = tk.Frame(self.progress_v_frame, bg=self.colors['frame_bg'])
        self.vertical_status_frame.place(relx=0.5, rely=0.5, anchor='center')
        self.create_step_status_indicators()
        self.progress = 'vertical'
        self.current_progress_value = 0
        self.log_frame = ttk.Frame(self.right_panel)
        self.log_text = tk.Text(self.log_frame, width=50, height=25, font=self.small_font,
                               bg=self.colors['entry_bg'], fg=self.colors['entry_fg'])
        log_scrollbar = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tooltip_manager.create_tooltip(self.log_text, 'log_text_help', self)
    def update_vertical_progress(self, value):
        self.current_progress_value = value
        canvas_height = self.progress_v_canvas.winfo_height()
        if canvas_height <= 1:
            canvas_height = 198
        canvas_width = self.progress_v_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 40
        self.progress_v_canvas.delete("all")
        progress_height = int((value / 100.0) * canvas_height)
        if progress_height > 0:
            self.progress_v_canvas.create_rectangle(
                2, canvas_height - progress_height,
                canvas_width - 2, canvas_height - 2,
                fill=self.colors['progress_fill'], 
                outline=self.colors['progress_fill']
            )
    def toggle_log(self):
        if self.log_expanded:
            self.log_frame.pack_forget()
            self.progress_frame.pack_forget()
            self.log_toggle_button.config(text=self.translate('expand_log') + " (?)")
            self.log_expanded = False
            self.progress_v_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.progress = 'vertical'
            self.horizontal_status_frame.pack_forget()
            self.root.after(100, lambda: self.update_vertical_progress(self.current_progress_value))
            current_width = self.root.winfo_width()
            new_width = max(800, current_width-400)
            self.root.geometry(f"{new_width}x{self.root.winfo_height()}")
        else:
            self.progress_v_frame.pack_forget()
            self.log_toggle_button.config(text=self.translate('collapse_log') + " (?)")
            self.log_expanded = True
            self.progress_frame.pack(fill=tk.X, padx=5, pady=5)
            self.horizontal_status_frame.pack(pady=5)
            self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.progress = self.progress_h
            self.update_progress_value(self.current_progress_value)
            current_width = self.root.winfo_width()
            min_width = 800 + len(self.steps) * 80 + 100
            new_width = max(min_width, current_width + 350)
            self.root.geometry(f"{new_width}x{self.root.winfo_height()}")
    def update_progress_value(self, value):
        self.current_progress_value = value
        if self.progress == 'vertical':
            self.update_vertical_progress(value)
        elif hasattr(self, 'progress_h') and self.progress == self.progress_h:
            try:
                self.progress_h['value'] = value
                self.root.update_idletasks()
            except Exception as e:
                print(f"Error updating horizontal progress: {e}")
        else:
            self.update_vertical_progress(value)
    def create_bottom_buttons(self):
        button_frame = ttk.Frame(self.left_panel)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        self.run_button = ttk.Button(button_frame, text=self.translate('run_review') + " (?)", 
                                    command=self.run_review_generation)
        self.run_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.tooltip_manager.create_tooltip(self.run_button, 'run_review_help', self)
        self.about_button = ttk.Button(button_frame, text=self.translate('about') + " (?)", 
                                      command=self.show_about)
        self.about_button.pack(side=tk.RIGHT)
        self.tooltip_manager.create_tooltip(self.about_button, 'about_help', self)
    def toggle_theme(self):
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        ConfigParams['Theme'] = self.current_theme
        SaveConfigParams()
        self.apply_theme()
        self.update_interface_text()
        theme_text = self.translate('theme_light') if self.current_theme == 'dark' else self.translate('theme_dark')
        self.theme_button.config(text=theme_text + " (?)")
        self.root.update_idletasks()
    def toggle_language(self):
        old_language = self.current_language
        self.current_language = 'en' if self.current_language == 'zh' else 'zh'
        ConfigParams['Language'] = self.current_language
        SaveConfigParams()
        self.update_all_interface_text()
        self.update_title()
        self.update_step_status_text()
        self.tooltip_manager.update_all_tooltips(self)
    def update_step_status_text(self):
        if not hasattr(self, 'step_status_indicators'):
            return
        for step_key, indicator in self.step_status_indicators.items():
            indicator['vertical']['label'].config(text=self.translate(step_key))
            indicator['horizontal']['label'].config(text=self.translate(step_key))
    def update_interface_text(self):
        self.update_all_interface_text()
    def update_all_interface_text(self):
        try:
            if hasattr(self, 'notebook'):
                self.notebook.tab(0, text=self.translate('tab_basic'))
                self.notebook.tab(1, text=self.translate('tab_llm'))
                self.notebook.tab(2, text=self.translate('tab_search_api'))
                self.notebook.tab(3, text=self.translate('tab_keywords'))
            if hasattr(self, 'lang_button'):
                lang_text = self.translate('language_en') if self.current_language == 'zh' else self.translate('language_zh')
                self.lang_button.config(text=lang_text + " (?)")
            if hasattr(self, 'theme_button'):
                theme_text = self.translate('theme_light') if self.current_theme == 'dark' else self.translate('theme_dark')
                self.theme_button.config(text=theme_text + " (?)")
            if hasattr(self, 'run_button'):
                self.run_button.config(text=self.translate('run_review') + " (?)")
            if hasattr(self, 'about_button'):
                self.about_button.config(text=self.translate('about') + " (?)")
            if hasattr(self, 'status_label'):
                self.status_label.config(text=self.translate('status_ready') + " (?)")
            if hasattr(self, 'custom_journals_button'):
                self.custom_journals_button.config(text=self.translate('custom_journals') + " (?)")
            if hasattr(self, 'log_toggle_button'):
                if self.log_expanded:
                    self.log_toggle_button.config(text=self.translate('collapse_log') + " (?)")
                else:
                    self.log_toggle_button.config(text=self.translate('expand_log') + " (?)")
            self.update_basic_tab_text()
            self.update_llm_tab_text()
            self.update_search_api_tab_text()
            self.update_keywords_tab_text()
            self.update_labels_in_frame(self.basic_frame)
            self.update_labels_in_frame(self.llm_frame)
            self.update_labels_in_frame(self.search_api_frame)
            self.update_labels_in_frame(self.keywords_frame)
        except Exception as e:
            print(f"Error updating interface text: {e}")
            traceback.print_exc()            
    def update_basic_tab_text(self):
        try:
            for widget in self.basic_frame.winfo_children():
                if isinstance(widget, ttk.LabelFrame):
                    current_text = widget.cget('text')
                    if 'Options' in current_text:
                        widget.config(text="Options (?)")
                    elif 'Search Settings' in current_text:
                        widget.config(text="Search Settings (?)")
            self.update_checkboxes_text()
        except Exception as e:
            print(f"Error updating basic tab text: {e}")
    def update_checkboxes_text(self):
        try:
            def update_widget_text(widget):
                if isinstance(widget, ttk.Checkbutton):
                    current_text = widget.cget('text')
                    if 'demo' in current_text.lower() or '演示' in current_text:
                        widget.config(text=self.translate('demo_mode') + " (?)")
                    elif ('skip' in current_text.lower() or '跳过' in current_text) and ('search' in current_text.lower() or '搜索' in current_text):
                        widget.config(text=self.translate('skip_search') + " (?)")
                    elif ('skip' in current_text.lower() or '跳过' in current_text) and ('topic' in current_text.lower() or '主题' in current_text):
                        widget.config(text=self.translate('skip_topic') + " (?)")
                    elif ('skip' in current_text.lower() or '跳过' in current_text) and ('knowledge' in current_text.lower() or '知识' in current_text):
                        widget.config(text=self.translate('skip_knowledge') + " (?)")
                    elif ('skip' in current_text.lower() or '跳过' in current_text) and ('review' in current_text.lower() or '综述' in current_text):
                        widget.config(text=self.translate('skip_review') + " (?)")
                    elif ('skip' in current_text.lower() or '跳过' in current_text) and ('compare' in current_text.lower() or '比较' in current_text):
                        widget.config(text=self.translate('skip_compare') + " (?)")
                    elif 'direct' in current_text.lower() or '直接' in current_text:
                        widget.config(text=self.translate('direct_topic') + " (?)")
                    elif 'q1' in current_text.lower():
                        widget.config(text=self.translate('q1_journals') + " (?)")
                    elif 'q2' in current_text.lower() or 'q3' in current_text.lower():
                        widget.config(text=self.translate('q2q3_journals') + " (?)")
                for child in widget.winfo_children():
                    update_widget_text(child)
            update_widget_text(self.basic_frame)
        except Exception as e:
            print(f"Error updating checkboxes text: {e}")
    def update_llm_tab_text(self):
        try:
            if hasattr(self, 'llm_tree'):
                self.llm_tree.heading('model', text=self.translate('model_name'))
                self.llm_tree.heading('url', text=self.translate('base_url'))
                self.llm_tree.heading('key', text=self.translate('api_key'))
                self.llm_tree.heading('tokens', text=self.translate('max_tokens'))
                self.llm_tree.heading('concurrency', text=self.translate('concurrency'))
                self.llm_tree.heading('status', text=self.translate('status'))
            self.update_llm_labels()
            if hasattr(self, 'llm_add_button'):
                if self.selected_llm_row:
                    self.llm_add_button.config(text=self.translate('update') + " (?)")
                else:
                    self.llm_add_button.config(text=self.translate('add') + " (?)")
            self.update_buttons_in_frame(self.llm_frame)
        except Exception as e:
            print(f"Error updating LLM tab text: {e}")
    def update_llm_labels(self):
        try:
            def update_llm_label_text(widget):
                if isinstance(widget, ttk.Label):
                    current_text = widget.cget('text')
                    if ('Model Name' in current_text or '模型名称' in current_text):
                        widget.config(text=self.translate('model_name') + " (?)")
                    elif ('Base URL' in current_text or '基础地址' in current_text):
                        widget.config(text=self.translate('base_url') + " (?)")
                    elif ('API Key' in current_text or 'API密钥' in current_text ):
                        widget.config(text=self.translate('api_key') + " (?)")
                    elif ('Max Tokens' in current_text or '最大Token' in current_text):
                        widget.config(text=self.translate('max_tokens') + " (?)")
                    elif 'LLM' in current_text and ('Models' in current_text or '模型' in current_text):
                        widget.config(text=self.translate('llm_models'))
                    elif 'Configuration' in current_text or '配置' in current_text:
                        widget.config(text=self.translate('llm_config'))
                for child in widget.winfo_children():
                    update_llm_label_text(child)
            update_llm_label_text(self.llm_frame)
        except Exception as e:
            print(f"Error updating LLM labels: {e}")
    def update_search_api_tab_text(self):
        try:
            for widget in self.search_api_frame.winfo_children():
                if isinstance(widget, tk.LabelFrame):
                    current_text = widget.cget('text')
                    if 'serp' in current_text.lower():
                        widget.config(text=self.translate('serp_api') + " (?)")
                    elif 'elsevier' in current_text.lower():
                        widget.config(text=self.translate('elsevier_api') + " (?)")
            if hasattr(self, 'serp_add_button'):
                if self.selected_serp_row:
                    self.serp_add_button.config(text=self.translate('update') + " (?)")
                else:
                    self.serp_add_button.config(text=self.translate('add') + " (?)")
            if hasattr(self, 'elsevier_add_button'):
                if self.selected_elsevier_row:
                    self.elsevier_add_button.config(text=self.translate('update') + " (?)")
                else:
                    self.elsevier_add_button.config(text=self.translate('add') + " (?)")
            self.update_buttons_in_frame(self.search_api_frame)
        except Exception as e:
            print(f"Error updating search API tab text: {e}")
    def update_keywords_tab_text(self):
        try:
            for widget in self.keywords_frame.winfo_children():
                if isinstance(widget, ttk.LabelFrame):
                    current_text = widget.cget('text')
                    if 'research' in current_text.lower() or '研究' in current_text:
                        widget.config(text=self.translate('research_keywords') + " (?)")
                    elif 'screen' in current_text.lower() or '筛选' in current_text:
                        widget.config(text=self.translate('screen_keywords') + " (?)")
            if hasattr(self, 'research_tree'):
                self.research_tree.heading('keyword', text=self.translate('research_keywords'))
            if hasattr(self, 'screen_tree'):
                self.screen_tree.heading('keyword', text=self.translate('screen_keywords'))
            if hasattr(self, 'research_add_button'):
                if self.selected_research_keyword_row:
                    self.research_add_button.config(text=self.translate('update') + " (?)")
                else:
                    self.research_add_button.config(text=self.translate('add') + " (?)")
            if hasattr(self, 'screen_add_button'):
                if self.selected_screen_keyword_row:
                    self.screen_add_button.config(text=self.translate('update') + " (?)")
                else:
                    self.screen_add_button.config(text=self.translate('add') + " (?)")
            self.update_buttons_in_frame(self.keywords_frame)
        except Exception as e:
            print(f"Error updating keywords tab text: {e}")
    def update_buttons_in_frame(self, frame):
        try:
            def update_button_text(widget):
                if isinstance(widget, ttk.Button):
                    current_text = widget.cget('text')
                    if 'Add' in current_text or '添加' in current_text:
                        widget.config(text=self.translate('add') + " (?)")
                    elif 'Delete' in current_text or '删除' in current_text:
                        widget.config(text=self.translate('delete') + " (?)")
                    elif 'Update' in current_text or '更新' in current_text:
                        widget.config(text=self.translate('update') + " (?)")
                    elif ('test' in current_text.lower() and 'selected' in current_text.lower()) or ('测试选中' in current_text):
                        widget.config(text=self.translate('test_selected') + " (?)")
                    elif ('test' in current_text.lower() and 'all' in current_text.lower()) or ('测试全部' in current_text):
                        widget.config(text=self.translate('test_all') + " (?)")
                for child in widget.winfo_children():
                    update_button_text(child)
            update_button_text(frame)
        except Exception as e:
            print(f"Error updating buttons in frame: {e}")
    def update_labels_in_frame(self, frame):
        try:
            def update_label_text(widget):
                if isinstance(widget, ttk.Label):
                    current_text = widget.cget('text')
                    if 'Topic' in current_text or '主题' in current_text:
                        widget.config(text=self.translate('topic') + " (?)")
                    elif 'Start Year' in current_text or '开始年份' in current_text:
                        widget.config(text=self.translate('start_year') + " (?)")
                    elif 'End Year' in current_text or '结束年份' in current_text:
                        widget.config(text=self.translate('end_year') + " (?)")
                    elif ('Max Papers' in current_text or '最大文献数' in current_text or 
                          'Max Pages' in current_text or '最大页数' in current_text):
                        widget.config(text=self.translate('max_papers') + " (?)")
                    elif 'Journal' in current_text or '期刊' in current_text:
                        widget.config(text=self.translate('journal_selection') + " (?)")
                    elif 'Model Name' in current_text or '模型名称' in current_text:
                        widget.config(text=self.translate('model_name') + " (?)")
                    elif 'Base URL' in current_text or '基础URL' in current_text:
                        widget.config(text=self.translate('base_url') + " (?)")
                    elif 'API Key' in current_text or 'API密钥' in current_text:
                        widget.config(text=self.translate('api_key') + " (?)")
                    elif 'Max Tokens' in current_text or '最大令牌' in current_text:
                        widget.config(text=self.translate('max_tokens') + " (?)")
                    elif 'Keyword' in current_text or '关键词' in current_text:
                        widget.config(text=self.translate('keyword') + " (?)")
                for child in widget.winfo_children():
                    update_label_text(child)
            update_label_text(frame)
        except Exception as e:
            print(f"Error updating labels in frame: {e}")
    def update_title(self):
        if self.authenticated:
            title = self.translate('app_title_licensed')
        else:
            title = self.translate('app_title_trial', days=self.days_left)
        self.root.title(title)
    def on_setting_changed(self, *args):
        ConfigParams['Topic'] = self.topic_var.get()
        ConfigParams['Demo'] = self.demo_var.get()
        ConfigParams['SkipSearching'] = self.skip_search_var.get()
        ConfigParams['SkipTopicFormulation'] = self.skip_topic_var.get()
        ConfigParams['SkipKnowledgeExtraction'] = self.skip_knowledge_var.get()
        ConfigParams['SkipReviewComposition'] = self.skip_review_var.get()
        ConfigParams['SkipCompareTwoReviewArticles'] = self.skip_compare_var.get()
        ConfigParams['DirectTopicGeneration'] = self.direct_topic_var.get()
        ConfigParams['Q1'] = self.q1_var.get()
        ConfigParams['Q2&Q3'] = self.q2q3_var.get()
        ConfigParams['StartYear'] = self.start_year_var.get()
        ConfigParams['EndYear'] = self.end_year_var.get()
        try:
            max_papers = int(self.max_papers_var.get())
            if max_papers > 200:
                messagebox.showwarning(
                    self.translate('input_warning'),
                    self.translate('max_papers_warning')
                )
                self.max_papers_var.set('200')
                max_papers = 200
            elif max_papers < 1:
                self.max_papers_var.set('1')
                max_papers = 1
            ConfigParams['MaxPapers'] = max_papers
        except ValueError:
            self.max_papers_var.set('100')
            ConfigParams['MaxPapers'] = 100
        if hasattr(self, 'step_status_indicators') and hasattr(self, 'log_text'):
            self.root.after(100, lambda: self.update_all_step_status(log_changes=True))
        SaveConfigParams()
    def load_settings(self):
        pass
    def load_llm_configs(self):
        for item in self.llm_tree.get_children():
            self.llm_tree.delete(item)
        self.llm_actual_keys = {}
        if 'ClaudeApiKey' in EncryptedParamLists:
            claude_urls = EncryptedParamLists.get('ClaudeApiUrl', ['https://api.anthropic.com'] * len(EncryptedParamLists['ClaudeApiKey']))
            claude_models = EncryptedParamLists.get('ClaudeApiModel', ['claude-3-sonnet'] * len(EncryptedParamLists['ClaudeApiKey']))
            claude_tokens = EncryptedParamLists.get('ClaudeApiTokens', ['100000'] * len(EncryptedParamLists['ClaudeApiKey']))
            claude_concurrency = EncryptedParamLists.get('ClaudeApiConcurrency', ['1'] * len(EncryptedParamLists['ClaudeApiKey']))
            for i, key in enumerate(EncryptedParamLists['ClaudeApiKey']):
                url = claude_urls[i] if i < len(claude_urls) else 'https://api.anthropic.com'
                model = claude_models[i] if i < len(claude_models) else 'claude-3-sonnet'
                tokens = claude_tokens[i] if i < len(claude_tokens) else '100000'
                concurrency = claude_concurrency[i] if i < len(claude_concurrency) else '1'
                item_id = self.llm_tree.insert('', tk.END, values=(
                    model, 
                    url, 
                    '*'*5+key[-4:],
                    tokens,
                    concurrency,
                    'Unknown'
                ))
                self.llm_actual_keys[item_id] = {
                    'model': model,
                    'url': url,
                    'key': key,
                    'tokens': tokens,
                    'concurrency': concurrency
                }
        if 'OpenAIApiKey' in EncryptedParamLists:
            openai_urls = EncryptedParamLists.get('OpenAIApiUrl', ['https://api.openai.com'] * len(EncryptedParamLists['OpenAIApiKey']))
            openai_models = EncryptedParamLists.get('OpenAIApiModel', [ConfigParams.get('Model', 'gpt-4')] * len(EncryptedParamLists['OpenAIApiKey']))
            openai_tokens = EncryptedParamLists.get('OpenAIApiTokens', [str(ConfigParams.get('MaxToken', 25000))] * len(EncryptedParamLists['OpenAIApiKey']))
            openai_concurrency = EncryptedParamLists.get('OpenAIApiConcurrency', ['1'] * len(EncryptedParamLists['OpenAIApiKey']))
            for i, key in enumerate(EncryptedParamLists['OpenAIApiKey']):
                url = openai_urls[i] if i < len(openai_urls) else 'https://api.openai.com'
                model = openai_models[i] if i < len(openai_models) else ConfigParams.get('Model', 'gpt-4')
                tokens = openai_tokens[i] if i < len(openai_tokens) else str(ConfigParams.get('MaxToken', 25000))
                concurrency = openai_concurrency[i] if i < len(openai_concurrency) else '1'
                item_id = self.llm_tree.insert('', tk.END, values=(
                    model, 
                    url, 
                    '*'*5+key[-4:],
                    tokens,
                    concurrency,
                    'Unknown'
                ))
                self.llm_actual_keys[item_id] = {
                    'model': model,
                    'url': url,
                    'key': key,
                    'tokens': tokens,
                    'concurrency': concurrency
                }
    def on_llm_select(self, event):
        selection = self.llm_tree.selection()
        if selection:
            self.selected_llm_row = selection[0]
            if self.selected_llm_row in getattr(self, 'llm_actual_keys', {}):
                data = self.llm_actual_keys[self.selected_llm_row]
                self.llm_model_var.set(data['model'])
                self.llm_url_var.set(data['url'])
                self.llm_key_var.set(data['key'])
                self.llm_tokens_var.set(data['tokens'])
                self.llm_concurrency_var.set(data['concurrency'])
            else:
                item = self.llm_tree.item(self.selected_llm_row)
                values = item['values']
                self.llm_model_var.set(values[0])
                self.llm_url_var.set(values[1])
                self.llm_key_var.set('')
                self.llm_tokens_var.set(values[3])
                self.llm_concurrency_var.set(values[4])
            self.llm_add_button.config(text=self.translate('update') + " (?)")
    def on_llm_click(self, event):
        region = self.llm_tree.identify_region(event.x, event.y)
        if region == "nothing":
            self.llm_tree.selection_remove(self.llm_tree.selection())
            self.selected_llm_row = None
            self.clear_llm_inputs()
            self.llm_add_button.config(text=self.translate('add') + " (?)")
    def clear_llm_inputs(self):
        self.llm_model_var.set('')
        self.llm_url_var.set('')
        self.llm_key_var.set('')
        self.llm_tokens_var.set('')
        self.llm_concurrency_var.set('')
    def add_llm_config(self):
        model = self.llm_model_var.get().strip()
        url = self.llm_url_var.get().strip()
        key = self.llm_key_var.get().strip()
        tokens = self.llm_tokens_var.get().strip()
        concurrency = self.llm_concurrency_var.get().strip()
        if not all([model, url, key, tokens, concurrency]):
            messagebox.showerror(self.translate('input_required'), self.translate('input_required'))
            return
        try:
            int(tokens)
            int(concurrency)
            if int(concurrency) < 1:
                raise ValueError("Concurrency must be >= 1")
        except ValueError:
            messagebox.showerror(self.translate('invalid_input'), self.translate('invalid_input'))
            return
        if not hasattr(self, 'llm_actual_keys'):
            self.llm_actual_keys = {}
        if self.selected_llm_row:
            self.llm_tree.item(self.selected_llm_row, values=(model, url, '*' * 20, tokens, concurrency, 'Unknown'))
            self.llm_actual_keys[self.selected_llm_row] = {
                'model': model, 'url': url, 'key': key, 'tokens': tokens, 'concurrency': concurrency
            }
            self.log(self.translate('api_updated'))
        else:
            item_id = self.llm_tree.insert('', tk.END, values=(model, url, '*' * 20, tokens, concurrency, 'Unknown'))
            self.llm_actual_keys[item_id] = {
                'model': model, 'url': url, 'key': key, 'tokens': tokens, 'concurrency': concurrency
            }
            self.log(self.translate('api_added'))
        self.update_llm_config()
        self.clear_llm_inputs()
        self.selected_llm_row = None
        self.llm_add_button.config(text=self.translate('add') + " (?)")
    def delete_llm_config(self):
        if not self.selected_llm_row:
            self.log(self.translate('no_llm_selected'))
            return
        if hasattr(self, 'llm_actual_keys') and self.selected_llm_row in self.llm_actual_keys:
            model_name = self.llm_actual_keys[self.selected_llm_row]['model']
            self.log(self.translate('deleting_llm_config').format(model=model_name))
        if messagebox.askyesno(self.translate('confirm_delete'), self.translate('confirm_delete_llm')):
            self.llm_tree.delete(self.selected_llm_row)
            if hasattr(self, 'llm_actual_keys') and self.selected_llm_row in self.llm_actual_keys:
                del self.llm_actual_keys[self.selected_llm_row]
            self.update_llm_config()
            self.clear_llm_inputs()
            self.selected_llm_row = None
            self.llm_add_button.config(text=self.translate('add') + " (?)")
            self.log(self.translate('llm_config_deleted'))
    def test_selected_llm(self):
        if not self.selected_llm_row:
            self.log(self.translate('no_llm_selected'))
            return
        if not hasattr(self, 'llm_actual_keys') or self.selected_llm_row not in self.llm_actual_keys:
            self.log(self.translate('no_llm_data'))
            return
        data = self.llm_actual_keys[self.selected_llm_row]
        values = self.llm_tree.item(self.selected_llm_row)['values']
        self.llm_tree.item(self.selected_llm_row, values=(*values[:5], self.translate('api_testing')))
        self.log(self.translate('testing_llm_start').format(model=data['model'], url=data['url']))
        def test_thread():
            try:
                model = data['model'].lower()
                self.root.after(0, lambda: self.log(self.translate('sending_test_request').format(model=data['model'])))
                if 'claude' in model:
                    response = Utility.GetResponse.GetResponseFromClaude('Hello', data['key'])
                    self.root.after(0, lambda: self.log(self.translate('claude_response_received').format(
                        model=data['model'], 
                        response_length=len(str(response))
                    )))
                else:
                    response = Utility.GetResponse.GetResponseFromOpenAlClient(
                        'Hello', data['url'], data['key'], model=data['model']
                    )
                    self.root.after(0, lambda: self.log(self.translate('openai_response_received').format(
                        model=data['model'], 
                        response_length=len(str(response))
                    )))
                result = self.translate('api_test_success')
                self.root.after(0, lambda: self.log(self.translate('llm_test_success').format(
                    model=data['model'],
                    concurrency=data['concurrency']
                )))
            except Exception as e:
                error_msg = str(e)[:100]
                result = f"{self.translate('api_test_failed')}: {error_msg}"
                self.root.after(0, lambda: self.log(self.translate('llm_test_failed').format(
                    model=data['model'],
                    error=error_msg
                )))
            self.root.after(0, lambda: self.llm_tree.item(
                self.selected_llm_row, values=(*values[:5], result)
            ))
            self.root.after(0, lambda: self.log(self.translate('testing_llm_complete').format(model=data['model'])))
        threading.Thread(target=test_thread, daemon=True).start()
    def test_all_llm(self):
        if not hasattr(self, 'llm_actual_keys'):
            self.log(self.translate('no_llm_configs'))
            return
        total_configs = len(self.llm_actual_keys)
        self.log(self.translate('testing_all_llm_start').format(count=total_configs))
        for item in self.llm_tree.get_children():
            values = self.llm_tree.item(item)['values']
            self.llm_tree.item(item, values=(*values[:5], self.translate('api_testing')))
        def test_all_thread():
            success_count = 0
            failed_count = 0
            for i, (item_id, data) in enumerate(self.llm_actual_keys.items(), 1):
                self.root.after(0, lambda idx=i, total=total_configs, model=data['model']: 
                               self.log(self.translate('testing_llm_progress').format(
                                   current=idx, 
                                   total=total, 
                                   model=model
                               )))
                try:
                    model = data['model'].lower()
                    self.root.after(0, lambda m=data['model']: 
                                   self.log(self.translate('sending_test_request').format(model=m)))
                    if 'claude' in model:
                        response = Utility.GetResponse.GetResponseFromClaude('Hello', data['key'])
                        self.root.after(0, lambda m=data['model'], r=response: 
                                       self.log(self.translate('claude_response_received').format(
                                           model=m, 
                                           response_length=len(str(r))
                                       )))
                    else:
                        response = Utility.GetResponse.GetResponseFromOpenAlClient(
                            'Hello', data['url'], data['key'], model=data['model']
                        )
                        self.root.after(0, lambda m=data['model'], r=response: 
                                       self.log(self.translate('openai_response_received').format(
                                           model=m, 
                                           response_length=len(str(r))
                                       )))
                    result = self.translate('api_test_success')
                    success_count += 1
                    self.root.after(0, lambda m=data['model'], c=data['concurrency']: 
                                   self.log(self.translate('llm_test_success').format(
                                       model=m,
                                       concurrency=c
                                   )))
                except Exception as e:
                    error_msg = str(e)[:100]
                    result = f"{self.translate('api_test_failed')}: {error_msg}"
                    failed_count += 1
                    self.root.after(0, lambda m=data['model'], err=error_msg: 
                                   self.log(self.translate('llm_test_failed').format(
                                       model=m,
                                       error=err
                                   )))
                values = self.llm_tree.item(item_id)['values']
                self.root.after(0, lambda i=item_id, r=result, v=values: 
                               self.llm_tree.item(i, values=(*v[:5], r)))
                if i < total_configs:
                    time.sleep(2)
                    self.root.after(0, lambda: self.log(self.translate('waiting_between_tests')))
            self.root.after(0, lambda: self.log(self.translate('testing_all_llm_complete').format(
                total=total_configs,
                success=success_count,
                failed=failed_count
            )))
        threading.Thread(target=test_all_thread, daemon=True).start()
    def update_llm_config(self):
        claude_keys = []
        claude_urls = []
        claude_models = []
        claude_tokens = []
        claude_concurrency = []
        openai_keys = []
        openai_urls = []
        openai_models = []
        openai_tokens = []
        openai_concurrency = []
        if hasattr(self, 'llm_actual_keys'):
            for item_id, data in self.llm_actual_keys.items():
                model = data['model'].lower()
                if 'claude' in model:
                    claude_keys.append(data['key'])
                    claude_urls.append(data['url'])
                    claude_models.append(data['model'])
                    claude_tokens.append(data['tokens'])
                    claude_concurrency.append(data['concurrency'])
                else:
                    openai_keys.append(data['key'])
                    openai_urls.append(data['url'])
                    openai_models.append(data['model'])
                    openai_tokens.append(data['tokens'])
                    openai_concurrency.append(data['concurrency'])
        EncryptedParamLists['ClaudeApiKey'] = claude_keys
        EncryptedParamLists['ClaudeApiUrl'] = claude_urls
        EncryptedParamLists['ClaudeApiModel'] = claude_models
        EncryptedParamLists['ClaudeApiTokens'] = claude_tokens
        EncryptedParamLists['ClaudeApiConcurrency'] = claude_concurrency
        EncryptedParamLists['OpenAIApiKey'] = openai_keys
        EncryptedParamLists['OpenAIApiUrl'] = openai_urls
        EncryptedParamLists['OpenAIApiModel'] = openai_models
        EncryptedParamLists['OpenAIApiTokens'] = openai_tokens
        EncryptedParamLists['OpenAIApiConcurrency'] = openai_concurrency
        SaveConfigParams()
    def get_total_concurrency(self):
        try:
            total_concurrency = 0
            claude_concurrency = EncryptedParamLists.get('ClaudeApiConcurrency', [])
            for concurrency_str in claude_concurrency:
                try:
                    concurrency = int(concurrency_str)
                    total_concurrency += concurrency
                except (ValueError, TypeError):
                    total_concurrency += 1
            openai_concurrency = EncryptedParamLists.get('OpenAIApiConcurrency', [])
            for concurrency_str in openai_concurrency:
                try:
                    concurrency = int(concurrency_str)
                    total_concurrency += concurrency
                except (ValueError, TypeError):
                    total_concurrency += 1
            return max(total_concurrency, 1)
        except Exception as e:
            print(f"Error calculating total concurrency: {e}")
            return 1
    def load_keywords(self):
        self.research_tree.delete(*self.research_tree.get_children())
        for keyword in ConfigParamLists.get('ResearchKeys', []):
            self.research_tree.insert('', tk.END, values=(keyword,))
        self.screen_tree.delete(*self.screen_tree.get_children())
        for keyword in ConfigParamLists.get('ScreenKeys', []):
            self.screen_tree.insert('', tk.END, values=(keyword,))
    def on_research_keyword_select(self, event):
        selection = self.research_tree.selection()
        if selection:
            self.selected_research_keyword_row = selection[0]
            item = self.research_tree.item(self.selected_research_keyword_row)
            self.research_keyword_var.set(item['values'][0])
            self.research_add_button.config(text=self.translate('update') + " (?)")
        else:
            self.selected_research_keyword_row = None
            self.research_keyword_var.set('')
            self.research_add_button.config(text=self.translate('add') + " (?)")
    def on_screen_keyword_select(self, event):
        selection = self.screen_tree.selection()
        if selection:
            self.selected_screen_keyword_row = selection[0]
            item = self.screen_tree.item(self.selected_screen_keyword_row)
            self.screen_keyword_var.set(item['values'][0])
            self.screen_add_button.config(text=self.translate('update') + " (?)")
        else:
            self.selected_screen_keyword_row = None
            self.screen_keyword_var.set('')
            self.screen_add_button.config(text=self.translate('add') + " (?)")
    def add_research_keyword(self):
        keyword = self.research_keyword_var.get().strip()
        if not keyword:
            return
        existing_keywords = [self.research_tree.item(item)['values'][0] for item in self.research_tree.get_children()]
        if self.selected_research_keyword_row:
            self.research_tree.item(self.selected_research_keyword_row, values=(keyword,))
            index = self.research_tree.index(self.selected_research_keyword_row)
            ConfigParamLists.setdefault('ResearchKeys', [])
            if index < len(ConfigParamLists['ResearchKeys']):
                ConfigParamLists['ResearchKeys'][index] = keyword
            self.log(self.translate('keyword_updated'))
        else:
            if keyword in existing_keywords:
                messagebox.showwarning(self.translate('keyword_exists'), self.translate('keyword_exists'))
                return
            self.research_tree.insert('', tk.END, values=(keyword,))
            ConfigParamLists.setdefault('ResearchKeys', []).append(keyword)
            self.log(self.translate('keyword_added'))
        SaveConfigParams()
        self.research_keyword_var.set('')
        self.selected_research_keyword_row = None
        self.research_add_button.config(text=self.translate('add') + " (?)")
    def delete_research_keyword(self):
        if not self.selected_research_keyword_row:
            messagebox.showwarning(self.translate('no_selection'), self.translate('no_keyword_selected'))
            return
        if messagebox.askyesno(self.translate('confirm_delete'), self.translate('delete_confirmation')):
            item = self.research_tree.item(self.selected_research_keyword_row)
            keyword = item['values'][0]
            index = self.research_tree.index(self.selected_research_keyword_row)
            self.research_tree.delete(self.selected_research_keyword_row)
            if 'ResearchKeys' in ConfigParamLists and index < len(ConfigParamLists['ResearchKeys']):
                ConfigParamLists['ResearchKeys'].pop(index)
            SaveConfigParams()
            self.selected_research_keyword_row = None
            self.research_keyword_var.set('')
            self.research_add_button.config(text=self.translate('add') + " (?)")
            self.log(self.translate('keyword_deleted'))
    def add_screen_keyword(self):
        keyword = self.screen_keyword_var.get().strip()
        if not keyword:
            return
        existing_keywords = [self.screen_tree.item(item)['values'][0] for item in self.screen_tree.get_children()]
        if self.selected_screen_keyword_row:
            self.screen_tree.item(self.selected_screen_keyword_row, values=(keyword,))
            index = self.screen_tree.index(self.selected_screen_keyword_row)
            ConfigParamLists.setdefault('ScreenKeys', [])
            if index < len(ConfigParamLists['ScreenKeys']):
                ConfigParamLists['ScreenKeys'][index] = keyword
            self.log(self.translate('keyword_updated'))
        else:
            if keyword in existing_keywords:
                messagebox.showwarning(self.translate('keyword_exists'), self.translate('keyword_exists'))
                return
            self.screen_tree.insert('', tk.END, values=(keyword,))
            ConfigParamLists.setdefault('ScreenKeys', []).append(keyword)
            self.log(self.translate('keyword_added'))
        SaveConfigParams()
        self.screen_keyword_var.set('')
        self.selected_screen_keyword_row = None
        self.screen_add_button.config(text=self.translate('add') + " (?)")
    def delete_screen_keyword(self):
        if not self.selected_screen_keyword_row:
            messagebox.showwarning(self.translate('no_selection'), self.translate('no_keyword_selected'))
            return
        if messagebox.askyesno(self.translate('confirm_delete'), self.translate('delete_confirmation')):
            item = self.screen_tree.item(self.selected_screen_keyword_row)
            keyword = item['values'][0]
            index = self.screen_tree.index(self.selected_screen_keyword_row)
            self.screen_tree.delete(self.selected_screen_keyword_row)
            if 'ScreenKeys' in ConfigParamLists and index < len(ConfigParamLists['ScreenKeys']):
                ConfigParamLists['ScreenKeys'].pop(index)
            SaveConfigParams()
            self.selected_screen_keyword_row = None
            self.screen_keyword_var.set('')
            self.screen_add_button.config(text=self.translate('add') + " (?)")
            self.log(self.translate('keyword_deleted'))
    def load_keywords(self):
        self.research_tree.delete(*self.research_tree.get_children())
        for keyword in ConfigParamLists.get('ResearchKeys', []):
            self.research_tree.insert('', tk.END, values=(keyword,))
        self.screen_tree.delete(*self.screen_tree.get_children())
        for keyword in ConfigParamLists.get('ScreenKeys', []):
            self.screen_tree.insert('', tk.END, values=(keyword,))
    def sort_tree(self, tree, column):
        data = [(tree.item(item)['values'], item) for item in tree.get_children()]
        columns = tree['columns']
        col_index = list(columns).index(column)
        def get_sort_key(x):
            try:
                return str(x[0][col_index]).lower()
            except (IndexError, TypeError):
                return ""
        data.sort(key=get_sort_key)
        for index, (values, item) in enumerate(data):
            tree.move(item, '', index)
    def test_elsevier_api_key(self, api_key):
        if not api_key:
            return False
        try:
            import requests
            test_url = "https://api.elsevier.com/content/search/scopus"
            headers = {
                'X-ELS-APIKey': api_key,
                'Accept': 'application/json'
            }
            params = {
                'query': 'TITLE("test")',
                'count': 1,
                'start': 0
            }
            response = requests.get(test_url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                return False
            elif response.status_code == 403:
                return False
            elif response.status_code == 429:
                return True
            else:
                return False
        except requests.exceptions.RequestException as e:
            return False
        except Exception as e:
            return False
    def get_elsevier_api_key(self):
        elsevier_keys = EncryptedParamLists.get('ElsevierApiList', [])
        if not elsevier_keys:
            raise Exception('Elsevier API key not set')
        for i, api_key in enumerate(elsevier_keys):
            self.log(f"🔍 测试 Elsevier API Key #{i+1}...")
            if self.test_elsevier_api_key(api_key):
                display_key = '*'*5 + api_key[-4:] if len(api_key) >= 4 else '*'*8
                self.log(f"✅ Elsevier API Key #{i+1} ({display_key}) 可用")
                return api_key
            else:
                display_key = '*'*5 + api_key[-4:] if len(api_key) >= 4 else '*'*8
                self.log(f"❌ Elsevier API Key #{i+1} ({display_key}) 不可用")
        self.log(f"❌ 所有 {len(elsevier_keys)} 个 Elsevier API Key 都不可用")
        raise Exception('Elsevier API key not set')
    def check_elsevier_api_availability(self):
        try:
            self.get_elsevier_api_key()
            return True
        except Exception:
            return False
    def check_configuration_completeness(self):
        errors = []
        if not ConfigParams.get('SkipSearching', False):
            if not EncryptedParamLists.get('SerpApiList'):
                errors.append(self.translate('please_add_serp_api'))
            if not EncryptedParamLists.get('ElsevierApiList'):
                errors.append(self.translate('please_add_elsevier_api'))
            else:
                try:
                    if not any(key.strip() for key in EncryptedParamLists['ElsevierApiList']):
                        errors.append(self.translate('please_add_elsevier_api'))
                except Exception:
                    errors.append(self.translate('please_add_elsevier_api'))
            if not ConfigParamLists.get('ResearchKeys'):
                errors.append(self.translate('please_add_research_keywords'))
            if not ConfigParamLists.get('ScreenKeys'):
                errors.append(self.translate('please_add_screen_keywords'))
        needs_llm = (
            not ConfigParams.get('SkipTopicFormulation', False) or
            not ConfigParams.get('SkipKnowledgeExtraction', False) or
            not ConfigParams.get('SkipReviewComposition', False) or
            not ConfigParams.get('SkipCompareTwoReviewArticles', False)
        )
        if needs_llm:
            has_claude_config = (
                EncryptedParamLists.get('ClaudeApiKey') and
                EncryptedParamLists.get('ClaudeApiUrl') and 
                EncryptedParamLists.get('ClaudeApiModel') and
                EncryptedParamLists.get('ClaudeApiTokens') and
                EncryptedParamLists.get('ClaudeApiConcurrency')
            )
            has_openai_config = (
                EncryptedParamLists.get('OpenAIApiKey') and
                EncryptedParamLists.get('OpenAIApiUrl') and
                EncryptedParamLists.get('OpenAIApiModel') and
                EncryptedParamLists.get('OpenAIApiTokens') and
                EncryptedParamLists.get('OpenAIApiConcurrency')
            )
            if not has_claude_config and not has_openai_config:
                errors.append(self.translate('please_add_llm_api'))
        return errors
    def show_configuration_errors(self, errors):
        error_window = tk.Toplevel(self.root)
        error_window.title(self.translate('configuration_check_failed'))
        error_window.geometry('500x400')
        error_window.configure(bg=self.colors['bg'])
        error_window.transient(self.root)
        error_window.grab_set()
        x = (error_window.winfo_screenwidth() // 2) - 250
        y = (error_window.winfo_screenheight() // 2) - 200
        error_window.geometry(f'500x400+{x}+{y}')
        main_frame = tk.Frame(error_window, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        title_label = tk.Label(main_frame, 
                              text=self.translate('missing_required_config'),
                              font=self.main_font, 
                              bg=self.colors['bg'], 
                              fg=self.colors['fg'])
        title_label.pack(pady=(0, 10))
        error_text = tk.Text(main_frame, wrap=tk.WORD, height=15, width=60,
                            bg=self.colors['entry_bg'], fg=self.colors['entry_fg'],
                            font=self.small_font)
        error_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        error_content = f"{self.translate('setup_required_before_start')}\n\n"
        error_content += f"{self.translate('check_settings_tabs')}\n\n"
        error_content += "❌ " + "\n❌ ".join(errors)
        error_text.insert(tk.END, error_content)
        error_text.config(state=tk.DISABLED)
        close_button = tk.Button(main_frame, 
                                text=self.translate('close') if hasattr(self, 'translate') else "确定 OK",
                                command=error_window.destroy,
                                bg=self.colors['button_bg'], 
                                fg=self.colors['button_fg'],
                                font=self.main_font)
        close_button.pack(pady=10)
    def finalize_stop_process(self):
        global IsProcessRunning, GlobalStopFlag
        IsProcessRunning = False
        GlobalStopFlag = False
        self.run_button.config(text=self.translate('run_review'))
        self.status_label.config(text=self.translate('status_interrupted'))
        for step_key, indicator in self.step_status_indicators.items():
            if indicator['status'] == 'running':
                self.update_step_status(step_key, 'error')
        self.log(self.translate('process_stopped'))
    def process_completed_successfully(self):
        global IsProcessRunning
        IsProcessRunning = False
        self.run_button.config(text=self.translate('run_review'))
        self.status_label.config(text=self.translate('status_completed'))
        for step_key, indicator in self.step_status_indicators.items():
            if indicator['status'] == 'running':
                self.update_step_status(step_key, 'completed')
    def calculate_max_token(self):
        try:
            all_tokens = []
            if hasattr(self, 'llm_actual_keys'):
                for config in self.llm_actual_keys.values():
                    try:
                        tokens = int(config.get('tokens', 25000))
                        all_tokens.append(tokens)
                    except (ValueError, TypeError):
                        all_tokens.append(25000)
            if not all_tokens:
                claude_tokens = EncryptedParamLists.get('ClaudeApiTokens', [])
                for token_str in claude_tokens:
                    try:
                        tokens = int(token_str)
                        all_tokens.append(tokens)
                    except (ValueError, TypeError):
                        all_tokens.append(200000)
                openai_tokens = EncryptedParamLists.get('OpenAIApiTokens', [])
                for token_str in openai_tokens:
                    try:
                        tokens = int(token_str)
                        all_tokens.append(tokens)
                    except (ValueError, TypeError):
                        all_tokens.append(25000)
            if all_tokens:
                min_tokens = min(all_tokens)
                ConfigParams['MaxToken'] = min_tokens
                SaveConfigParams()
            else:
                ConfigParams['MaxToken'] = 25000
                SaveConfigParams()
        except Exception as e:
            ConfigParams['MaxToken'] = 25000
            SaveConfigParams()
    def create_step_status_indicators(self):
        self.steps = [
            ('literature_search', 'SkipSearching'),
            ('topic_formulation', 'SkipTopicFormulation'), 
            ('knowledge_extraction', 'SkipKnowledgeExtraction'),
            ('review_composition', 'SkipReviewComposition'),
        ]
        self.step_status_indicators = {}
        for i, (step_key, config_key) in enumerate(self.steps):
            v_frame = tk.Frame(self.vertical_status_frame, bg=self.colors['frame_bg'])
            v_frame.pack(pady=3)
            v_icon = tk.Label(v_frame, text="⏳", font=self.small_font, 
                             bg=self.colors['frame_bg'], fg=self.colors['fg'], 
                             width=3, height=1)
            v_icon.pack()
            v_label = tk.Label(v_frame, text=self.translate(step_key), font=self.small_font,
                              bg=self.colors['frame_bg'], fg=self.colors['fg'])
            v_label.pack()
            h_frame = tk.Frame(self.horizontal_status_frame, bg=self.colors['frame_bg'])
            h_frame.pack(side=tk.LEFT, padx=5)
            h_icon = tk.Label(h_frame, text="⏳", font=self.small_font, bg=self.colors['frame_bg'], fg=self.colors['fg'])
            h_icon.pack()
            h_label = tk.Label(h_frame, text=self.translate(step_key), font=self.small_font, bg=self.colors['frame_bg'], fg=self.colors['fg'])
            h_label.pack()
            self.step_status_indicators[step_key] = {
                'config_key': config_key,
                'vertical': {'icon': v_icon, 'label': v_label, 'frame': v_frame},
                'horizontal': {'icon': h_icon, 'label': h_label, 'frame': h_frame},
                'status': 'waiting'
            }
            self.tooltip_manager.create_tooltip(v_frame, f'{step_key}_status_help', self)
            self.tooltip_manager.create_tooltip(h_frame, f'{step_key}_status_help', self)
        self.update_all_step_status(log_changes=False)
    def update_step_status(self, step_key, status='waiting', log_change=True):
        if step_key not in self.step_status_indicators:
            return
        status_icons = {
            'waiting': '⏳',
            'running': '⚡',
            'completed': '✅',
            'error': '❌',
            'skipped': '⏭️'
        }
        status_colors = {
            'waiting':self.colors['fg'],
            'running': self.colors['fg'],
            'completed':self.colors['fg'],
            'error': self.colors['fg'],
            'skipped':self.colors['fg'],
        }
        icon = status_icons.get(status, '⏳')
        color = status_colors.get(status, 'gray')
        indicator = self.step_status_indicators[step_key]
        indicator['status'] = status
        indicator['vertical']['icon'].config(text=icon, fg=color)
        indicator['horizontal']['icon'].config(text=icon, fg=color)
        if log_change and hasattr(self, 'log_text') and self.log_text:
            step_name = self.translate(step_key)
            status_name = self.translate(f'status_{status}')
            self.log(f"📋 {step_name}: {status_name}")
    def update_all_step_status(self, log_changes=False):
        if not hasattr(self, 'step_status_indicators'):
            return
        for step_key, indicator in self.step_status_indicators.items():
            config_key = indicator['config_key']
            is_skipped = ConfigParams.get(config_key, False)
            if is_skipped:
                var_mapping = {
                    'SkipSearching': 'skip_search_var',
                    'SkipTopicFormulation': 'skip_topic_var', 
                    'SkipKnowledgeExtraction': 'skip_knowledge_var',
                    'SkipReviewComposition': 'skip_review_var',
                    'SkipCompareTwoReviewArticles': 'skip_compare_var'
                }
                var_name = var_mapping.get(config_key)
                if var_name and hasattr(self, var_name):
                    var = getattr(self, var_name)
                    if var.get():
                        self.update_step_status(step_key, 'completed', log_changes)
                    else:
                        self.update_step_status(step_key, 'completed', log_changes)
                else:
                    self.update_step_status(step_key, 'completed', log_changes)
            else:
                self.update_step_status(step_key, 'waiting', log_changes)
    def auto_check_skip_option(self, option_name):
        try:
            option_mapping = {
                'skip_search': ('literature_search', 'skip_search_var'),
                'skip_topic': ('topic_formulation', 'skip_topic_var'),
                'skip_knowledge': ('knowledge_extraction', 'skip_knowledge_var'),
                'skip_review': ('review_composition', 'skip_review_var'),
                'skip_compare': ('review_comparison', 'skip_compare_var')
            }
            if option_name in option_mapping:
                step_key, var_name = option_mapping[option_name]
                if hasattr(self, var_name):
                    var = getattr(self, var_name)
                    var.set(True)
                self.update_step_status(step_key, 'completed')
                step_name = self.translate(step_key)
            self.on_setting_changed()
        except Exception as e:
            print(f"Error auto-checking skip option {option_name}: {e}")
    def set_step_running(self, step_key):
        self.update_step_status(step_key, 'running')
    def set_step_error(self, step_key, error_msg=""):
        self.update_step_status(step_key, 'error')
        if error_msg:
            step_name = self.translate(step_key)
            self.log(f"❌ {step_name} {self.translate('failed')}: {error_msg}")
    def update_progress_label(self, text):
        self.root.after(0, lambda: self.progress_label.config(text=text))
    def log(self, message):
        if not hasattr(self, 'log_text') or self.log_text is None:
            print(f"Early log: {message}")
            return
        if not message.endswith('\n'):
            message += '\n'
        try:
            self.log_text.insert(tk.END, message)
            self.log_text.see(tk.END)
        except tk.TclError:
            print(f"Log error: {message}")
            pass
    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title(self.translate('about_title'))
        about_window.geometry('500x400')
        about_window.configure(bg=self.colors['bg'])
        about_window.transient(self.root)
        about_window.grab_set()
        content_frame = tk.Frame(about_window, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        about_text = tk.Text(content_frame, wrap=tk.WORD, height=20, width=60,
                            bg=self.colors['entry_bg'], fg=self.colors['entry_fg'],
                            font=self.small_font)
        about_text.pack(fill=tk.BOTH, expand=True)
        about_content = self.translate('about_content')
        try:
            about_file = os.path.join(RootDirectory, 'about_info.txt')
            if os.path.exists(about_file):
                with open(about_file, 'r', encoding='utf-8') as f:
                    about_content = f.read()
        except Exception:
            pass
        about_text.insert(tk.END, about_content)
        about_text.config(state=tk.DISABLED)
        close_button = tk.Button(content_frame, text="Close", command=about_window.destroy,
                                bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                                font=self.main_font)
        close_button.pack(pady=10)
    def open_journal_editor(self):
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
            import importlib
            importlib.reload(Global_Journal)
            Global_Journal.User_defined.clear()
            Global_Journal.User_defined.extend(journals)
            if journals:
                import LiteratureSearch.One_key_download as One_key_download
                One_key_download.High_IF_publications['User_defined'] = journals
                One_key_download.Low_IF_publications['User_defined'] = journals
            self.log(f"Updated custom journal list ({len(journals)} journals)")
            SaveConfigParams()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update custom journals: {str(e)}")
    def on_closing(self):
        global GlobalStopFlag
        os.chdir(RootDirectory)
        try:
            shutil.copy(f'Temp{os.sep}run.log',
                       f"Temp{os.sep}logs{os.sep}run{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}.log")
        except Exception as e:
            print(f"Error saving log: {e}")
        if IsProcessRunning:
            if messagebox.askyesno("Confirm", "Process is running. Stop and exit?"):
                GlobalStopFlag = True
                self.root.destroy()
        else:
            self.root.destroy()
        if not os.path.basename(sys.executable).lower().startswith('python'):
            ExecuteCommand(f"TASKKILL /F /IM {os.path.basename(sys.executable)}")
    def show_configuration_errors(self, errors):
        error_window = tk.Toplevel(self.root)
        error_window.title(self.translate('configuration_check_failed'))
        error_window.geometry('500x400')
        error_window.configure(bg=self.colors['bg'])
        error_window.transient(self.root)
        error_window.grab_set()
        x = (error_window.winfo_screenwidth() // 2) - 250
        y = (error_window.winfo_screenheight() // 2) - 200
        error_window.geometry(f'500x400+{x}+{y}')
        main_frame = tk.Frame(error_window, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        title_label = tk.Label(main_frame, 
                              text=self.translate('missing_required_config'),
                              font=self.main_font, 
                              bg=self.colors['bg'], 
                              fg=self.colors['fg'])
        title_label.pack(pady=(0, 10))
        error_text = tk.Text(main_frame, wrap=tk.WORD, height=15, width=60,
                            bg=self.colors['entry_bg'], fg=self.colors['entry_fg'],
                            font=self.small_font)
        error_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        error_content = f"{self.translate('setup_required_before_start')}\n\n"
        error_content += f"{self.translate('check_settings_tabs')}\n\n"
        error_content += "❌ " + "\n❌ ".join(errors)
        error_text.insert(tk.END, error_content)
        error_text.config(state=tk.DISABLED)
        close_button = tk.Button(main_frame, 
                                text="确定 OK",
                                command=error_window.destroy,
                                bg=self.colors['button_bg'], 
                                fg=self.colors['button_fg'],
                                font=self.main_font)
        close_button.pack(pady=10)
    def translate_exception(self, exception_msg):
        exception_translations = {
            'No API keys': '缺少Serp API密钥',
            'Elsevier API key not set': '缺少Elsevier API密钥', 
            'No Key words': '缺少研究关键词',
            'No Screen words': '缺少筛选关键词',
            'No Available API.': '缺少大模型API密钥'
        }
        for en_msg, zh_msg in exception_translations.items():
            if en_msg.lower() in exception_msg.lower():
                return zh_msg
        return exception_msg
    def log_error_bold(self, message):
        if not hasattr(self, 'log_text') or self.log_text is None:
            print(f"Early error log: {message}")
            return
        try:
            bold_message = f"❌ **错误**: {message}\n"
            self.log_text.insert(tk.END, bold_message)
            self.log_text.see(tk.END)
            LogToFile(f"ERROR: {message}")
        except tk.TclError:
            print(f"Log error: {message}")
            pass
    def inject_stop_check_into_modules(self):
        try:
            import sys
            sys._GUI_STOP_FLAG = True
            modules_to_check = [
                'ReviewComposition.GenerateParagraphOfReview',
                'KnowledgeExtraction.GetAllResponse',
                'TopicFormulation.GetQuestionsFromReview',
                'LiteratureSearch.One_key_download'
            ]
            injected_count = 0
            for module_name in modules_to_check:
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                    if hasattr(module, '__dict__'):
                        module.__dict__['_STOP_REQUESTED'] = True
                        injected_count += 1
            return injected_count > 0
        except Exception as e:
            return False
    def force_shutdown_executors(self):
        try:
            shutdown_count = 0
            import concurrent.futures
            import gc
            for obj in gc.get_objects():
                try:
                    if isinstance(obj, concurrent.futures.ThreadPoolExecutor):
                        obj.shutdown(wait=False)
                        shutdown_count += 1
                    elif isinstance(obj, concurrent.futures.ProcessPoolExecutor):
                        obj.shutdown(wait=False)
                        shutdown_count += 1
                except Exception as e:
                    continue
            try:
                import multiprocessing
                for obj in gc.get_objects():
                    try:
                        if hasattr(obj, '__class__') and 'Pool' in str(obj.__class__):
                            if hasattr(obj, 'terminate'):
                                obj.terminate()
                                shutdown_count += 1
                    except:
                        continue
            except:
                pass
            return shutdown_count
        except Exception as e:
            return 0
    def send_multiple_interrupt_signals(self):
        try:
            signal_count = 0
            if os.name == 'nt':
                try:
                    os.kill(os.getpid(), signal.CTRL_C_EVENT)
                    self.log("⚡ 已发送CTRL+C信号")
                    signal_count += 1
                except:
                    pass
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    kernel32.GenerateConsoleCtrlEvent(0, 0)
                    self.log("⚡ 已发送控制台中断事件")
                    signal_count += 1
                except:
                    pass
                try:
                    kernel32.SetConsoleCtrlHandler(None, True)
                    time.sleep(0.1)
                    kernel32.SetConsoleCtrlHandler(None, False)
                    self.log("⚡ 已操作控制台处理器")
                    signal_count += 1
                except:
                    pass
            else:
                try:
                    os.kill(os.getpid(), signal.SIGINT)
                    self.log("⚡ 已发送SIGINT信号")
                    signal_count += 1
                except:
                    pass
                try:
                    os.kill(os.getpid(), signal.SIGTERM)
                    self.log("⚡ 已发送SIGTERM信号")
                    signal_count += 1
                except:
                    pass
            try:
                import _thread
                _thread.interrupt_main()
                self.log("⚡ 已发送主线程中断")
                signal_count += 1
            except:
                pass
            if signal_count > 0:
                self.log(f"✅ 已发送 {signal_count} 个中断信号")
            else:
                self.log("⚠️ 未能发送任何中断信号")
        except Exception as e:
            self.log(f"⚠️ 发送中断信号时出错: {str(e)}")
    def force_interrupt_python_execution(self):
        try:
            if os.name == 'nt':
                try:
                    os.kill(os.getpid(), signal.CTRL_C_EVENT)
                    self.log("⚡ 已发送CTRL+C信号")
                    return True
                except:
                    pass
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    kernel32.GenerateConsoleCtrlEvent(0, 0)
                    self.log("⚡ 已发送控制台中断事件")
                    return True
                except Exception as e:
                    self.log(f"⚠️ 发送控制台事件失败: {str(e)}")
            else:
                try:
                    os.kill(os.getpid(), signal.SIGINT)
                    self.log("⚡ 已发送SIGINT信号")
                    return True
                except Exception as e:
                    self.log(f"⚠️ 发送SIGINT失败: {str(e)}")
            return False
        except Exception as e:
            self.log(f"⚠️ 强制中断执行时出错: {str(e)}")
            return False
    def run_review_generation(self):
        global IsProcessRunning, GlobalStopFlag
        if not IsProcessRunning:
            config_errors = self.check_configuration_completeness()
            if config_errors:
                self.show_configuration_errors(config_errors)
                return
            self.calculate_max_token()
            IsProcessRunning = True
            GlobalStopFlag = False
            self.run_button.config(text=self.translate('stop_process'))
            self.status_label.config(text=self.translate('status_running'))
            self.update_progress_value(0)
            for step_key in self.step_status_indicators.keys():
                if not ConfigParams.get(self.step_status_indicators[step_key]['config_key'], False):
                    self.update_step_status(step_key, 'waiting', log_change=False)
            self.stop_event.clear()
            self.active_threads.clear()
            self.process_start_time = time.time()
            self.main_process_thread = threading.Thread(
                target=self.run_automatic_review_generation, 
                daemon=False,
                name="MainProcessThread"
            )
            self.active_threads.append(self.main_process_thread)
            self.main_process_thread.start()
        else:
            self.log(self.translate('stopping_process_immediately'))
            GlobalStopFlag = True
            self.run_button.config(text=self.translate('run_review'))
            self.status_label.config(text=self.translate('status_interrupted'))
            for step_key, indicator in self.step_status_indicators.items():
                if indicator['status'] == 'running':
                    self.update_step_status(step_key, 'error')
            IsProcessRunning = False
            self.force_kill_processes()
            self.log(self.translate('process_stopped_immediately'))
    def run_automatic_review_generation(self):
        old_stdout = sys.stdout
        try:
            sys.stdout = TextOutputRedirector(self.log_text, self)
            self.log(f"Start\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
            self.update_progress_value(0)
            os.chdir(f'{RootDirectory}{os.sep}Temp')
            if not ConfigParams['SkipSearching'] and not self.stop_event.is_set():
                self.literature_search_process()
                self.update_step_status('literature_search', 'completed')
            if self.stop_event.is_set() or GlobalStopFlag:
                self.log("❌ 用户停止：文献搜索被中断")
                return
            self.update_progress_value(20)
            global ClaudeApiFunctions, OpenAIApiFunctions, HasLLMBeenChecked
            if not HasLLMBeenChecked and not self.stop_event.is_set():
                self.initialize_llm_functions()
            if self.stop_event.is_set() or GlobalStopFlag:
                self.log("❌ 用户停止：LLM初始化被中断")
                return
            if not ConfigParams['SkipTopicFormulation'] and not self.stop_event.is_set():
                self.topic_formulation_process()
                self.update_step_status('topic_formulation', 'completed')
            if self.stop_event.is_set() or GlobalStopFlag:
                self.log("❌ 用户停止：主题构建被中断")
                return
            self.update_progress_value(40)
            if not ConfigParams['SkipKnowledgeExtraction'] and not self.stop_event.is_set():
                self.knowledge_extraction_process()
                self.update_step_status('knowledge_extraction', 'completed')
            if self.stop_event.is_set() or GlobalStopFlag:
                self.log("❌ 用户停止：知识提取被中断")
                return
            self.update_progress_value(60)
            if not ConfigParams['SkipReviewComposition'] and not self.stop_event.is_set():
                self.review_composition_process()
                self.update_step_status('review_composition', 'completed')
            if self.stop_event.is_set() or GlobalStopFlag:
                self.log("❌ 用户停止：综述整合被中断")
                return
            self.update_progress_value(80)
            print(f'\n综述生成完成，位于{RootDirectory}{os.sep}ReviewDraft.txt\n')
            subprocess.Popen(['notepad.exe', f'{RootDirectory}{os.sep}ReviewDraft.txt'])
            if not ConfigParams['SkipCompareTwoReviewArticles'] and not self.stop_event.is_set():
                self.compare_review_articles_process()
                self.update_step_status('review_comparison', 'completed')
            if self.stop_event.is_set() or GlobalStopFlag:
                self.log("❌ 用户停止：综述比较被中断")
                return
            self.update_progress_value(100)
            self.log(f"End\t{time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime())}")
            if not self.stop_event.is_set() and not GlobalStopFlag:
                self.root.after(0, lambda: self.process_completed_successfully())
        except Exception as e:
            if self.stop_event.is_set() or GlobalStopFlag or "stopped by user" in str(e):
                self.log(self.translate('process_stopped_by_user'))
                return
            error_msg = str(e)
            if any(zh_msg in error_msg for zh_msg in ['缺少Serp API密钥', '缺少Elsevier API密钥', '缺少研究关键词', '缺少筛选关键词', '缺少大模型API密钥']):
                self.log(f"Error: {error_msg}\n")
            else:
                translated_error = self.translate_exception(error_msg)
                self.log(f"Error: {translated_error}\n")
            self.root.after(0, lambda: self.status_label.config(text=self.translate('status_error')))
        finally:
            sys.stdout = old_stdout
            try:
                if self.main_process_thread in self.active_threads:
                    self.active_threads.remove(self.main_process_thread)
            except:
                pass
            global IsProcessRunning
            if not self.stop_event.is_set() and not GlobalStopFlag:
                IsProcessRunning = False
                self.root.after(0, lambda: self.run_button.config(text=self.translate('run_review')))
    def initialize_llm_functions(self):
        global ClaudeApiFunctions, OpenAIApiFunctions, HasLLMBeenChecked
        if self.stop_event.is_set() or GlobalStopFlag:
            return
        self.log("🔧 初始化LLM API函数...")
        ClaudeApiFunctions = {}
        claude_keys = EncryptedParamLists.get('ClaudeApiKey', [])
        claude_urls = EncryptedParamLists.get('ClaudeApiUrl', [])
        claude_models = EncryptedParamLists.get('ClaudeApiModel', [])
        claude_tokens = EncryptedParamLists.get('ClaudeApiTokens', [])
        claude_concurrency = EncryptedParamLists.get('ClaudeApiConcurrency', [])
        function_index = 0
        for i in range(len(claude_keys)):
            if self.stop_event.is_set() or GlobalStopFlag:
                return
            api_key = claude_keys[i]
            url = claude_urls[i] if i < len(claude_urls) else 'https://api.anthropic.com'
            model = claude_models[i] if i < len(claude_models) else 'claude-3-sonnet'
            tokens = claude_tokens[i] if i < len(claude_tokens) else '100000'
            concurrency = int(claude_concurrency[i]) if i < len(claude_concurrency) else 1
            for j in range(concurrency):
                ClaudeApiFunctions[function_index] = functools.partial(
                    Utility.GetResponse.GetResponseFromClaude, 
                    api_key=api_key
                )
                function_index += 1
            self.log(f"✅ Claude配置 #{i+1}: {model} (并发数: {concurrency})")
        OpenAIApiFunctions = {}
        openai_keys = EncryptedParamLists.get('OpenAIApiKey', [])
        openai_urls = EncryptedParamLists.get('OpenAIApiUrl', [])
        openai_models = EncryptedParamLists.get('OpenAIApiModel', [])
        openai_tokens = EncryptedParamLists.get('OpenAIApiTokens', [])
        openai_concurrency = EncryptedParamLists.get('OpenAIApiConcurrency', [])
        function_index = 0
        for i in range(len(openai_keys)):
            if self.stop_event.is_set() or GlobalStopFlag:
                return
            api_key = openai_keys[i]
            url = openai_urls[i] if i < len(openai_urls) else 'https://api.openai.com'
            model = openai_models[i] if i < len(openai_models) else 'gpt-4'
            tokens = openai_tokens[i] if i < len(openai_tokens) else '25000'
            concurrency = int(openai_concurrency[i]) if i < len(openai_concurrency) else 1
            for j in range(concurrency):
                OpenAIApiFunctions[function_index] = functools.partial(
                    Utility.GetResponse.GetResponseFromOpenAlClient,
                    url=url, 
                    key=api_key, 
                    model=model
                )
                function_index += 1
            self.log(f"✅ OpenAI配置 #{i+1}: {model} (并发数: {concurrency})")
        if self.stop_event.is_set() or GlobalStopFlag:
            return
        total_claude_instances = len(ClaudeApiFunctions)
        total_openai_instances = len(OpenAIApiFunctions)
        total_concurrency = self.get_total_concurrency()
        ConfigParams['Threads'] = total_concurrency
        self.log(f"🔧 LLM API函数初始化完成: Claude实例数={total_claude_instances}, OpenAI实例数={total_openai_instances}")
        self.log(f"🔧 总并发数: {total_concurrency} (将用于所有LLM调用步骤)")
        HasLLMBeenChecked = True
    def literature_search_process(self):
        self.root.after(0, lambda: self.set_step_running('literature_search'))
        self.update_progress_label(self.translate('literature_search'))
        try:
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            if not EncryptedParamLists.get('SerpApiList'):
                raise Exception('No API keys')
            if not ConfigParamLists.get('ResearchKeys'):
                raise Exception('No Key words')
            if not ConfigParamLists.get('ScreenKeys'):
                raise Exception('No Screen words')
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            self.log("🔍 检查 Elsevier API Key 可用性...")
            elsevier_api_key = self.get_elsevier_api_key()
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            LiteratureSearch.Advanced_Research.set_elsevier_api_key(elsevier_api_key)
            self.log("✅ Elsevier API Key 设置完成")
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            max_papers = ConfigParams.get('MaxPapers', 100)
            import math
            if max_papers <= 200:
                max_pages = math.ceil(max_papers / 10) + 5
            else:
                max_pages = 25
                max_papers = 200
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            self.log("📊 即将启动文献搜索...")
            LiteratureSearch.One_key_download.User_pages(
                EncryptedParamLists['SerpApiList'],
                ConfigParamLists['ResearchKeys'],
                ConfigParamLists['ScreenKeys'],
                int(ConfigParams['StartYear']),
                int(ConfigParams['EndYear']),
                ConfigParams['Q1'],
                ConfigParams['Q2&Q3'],
                ConfigParams['Demo'],
                max_pages=max_pages,
                max_papers=max_papers,
                STDOUT=sys.stdout
            )
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            ConfigParams['SkipSearching'] = True
            SaveConfigParams()
            self.root.after(0, lambda: self.auto_check_skip_option('skip_search'))
            self.root.after(0, lambda: self.log(self.translate('literature_search_completed')))
        except Exception as e:
            if "stopped by user" in str(e) or self.stop_event.is_set() or GlobalStopFlag:
                self.root.after(0, lambda: self.update_step_status('literature_search', 'error'))
                raise
            error_msg = str(e)
            translated_error = self.translate_exception(error_msg)
            self.root.after(0, lambda msg=translated_error: self.log_error_bold(msg))
            self.root.after(0, lambda msg=translated_error: self.set_step_error('literature_search', msg))
            raise Exception(translated_error)
    def review_composition_process(self):
        self.root.after(0, lambda: self.set_step_running('review_composition'))
        self.update_progress_label(self.translate('review_composition'))
        try:
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            if not EncryptedParamLists.get('ClaudeApiKey') and not EncryptedParamLists.get('OpenAIApiKey'):
                raise Exception('No Available API.')
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            answer_dir = f'{RootDirectory}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}Answer'
            if os.path.exists(answer_dir) and os.listdir(answer_dir):
                review_dir = f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph'
                os.makedirs(review_dir, exist_ok=True)
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                [shutil.copytree(
                    f'{answer_dir}{os.sep}{part}{os.sep}{num}',
                    f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}{int(part.split("PART")[-1]) * 7 + int(num)}',
                    dirs_exist_ok=True)
                    for part in os.listdir(answer_dir) if part.startswith('PART')
                    for num in os.listdir(f'{answer_dir}{os.sep}{part}')
                    if (not num.endswith('.txt')) and os.listdir(f'{answer_dir}{os.sep}{part}{os.sep}{num}')]
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                self.log("📊 即将启动综述整合...")
                ReviewComposition.GenerateParagraphOfReview.Main(
                    f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir',
                    ConfigParams['Topic'],
                    ConfigParams['Threads'],
                    ClaudeApiFunctions,
                    OpenAIApiFunctions,
                    STDOUT=sys.stdout
                )
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                ReviewComposition.GenerateRatingsForReviewParagraphs.Main(
                    f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir',
                    ConfigParams['Threads'],
                    ClaudeApiFunctions,
                    OpenAIApiFunctions,
                    STDOUT=sys.stdout
                )
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                best_paragraph_dir = f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}BestParagraph'
                os.makedirs(best_paragraph_dir, exist_ok=True)
                [shutil.copy(
                    f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph{os.sep}{para}',
                    f'{best_paragraph_dir}{os.sep}{para}'
                ) for para in os.listdir(f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph')
                    if re.match('BestParagraph\\d+.txt', para)]
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                ReviewComposition.ExtractSectionsWithTags.Main(best_paragraph_dir, STDOUT=sys.stdout)
                shutil.copy(f'{best_paragraph_dir}{os.sep}draft.txt', f'{RootDirectory}{os.sep}ReviewDraft.txt')
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                ConfigParams['SkipReviewComposition'] = True
                SaveConfigParams()
                self.root.after(0, lambda: self.auto_check_skip_option('skip_review'))
                self.root.after(0, lambda: self.log(self.translate('review_composition_completed')))
        except Exception as e:
            if "stopped by user" in str(e) or self.stop_event.is_set() or GlobalStopFlag:
                self.root.after(0, lambda: self.update_step_status('review_composition', 'error'))
                raise
            error_msg = str(e)
            translated_error = self.translate_exception(error_msg)
            if translated_error != error_msg:
                self.root.after(0, lambda msg=translated_error: self.log_error_bold(msg))
            self.log(f"Error in review composition: {translated_error}")
            self.root.after(0, lambda msg=translated_error: self.set_step_error('review_composition', msg))
            raise Exception(translated_error)
    def topic_formulation_process(self):
        self.root.after(0, lambda: self.set_step_running('topic_formulation'))
        self.update_progress_label(self.translate('topic_formulation'))
        try:
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            if not EncryptedParamLists.get('ClaudeApiKey') and not EncryptedParamLists.get('OpenAIApiKey'):
                raise Exception('No Available API.')
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            if os.path.exists(f'{RootDirectory}{os.sep}Temp{os.sep}LiteratureSearchWorkDir'):
                topic_dir = f'{RootDirectory}{os.sep}Temp{os.sep}TopicFormulationWorkDir'
                os.makedirs(topic_dir, exist_ok=True)
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                [shutil.copy(f'{RootDirectory}{os.sep}Temp{os.sep}LiteratureSearchWorkDir{os.sep}{f}',
                             f'{topic_dir}{os.sep}{f}')
                 for f in os.listdir(f'{RootDirectory}{os.sep}Temp{os.sep}LiteratureSearchWorkDir')
                 if f.startswith('10.') and f.endswith('_Review.txt')]
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                self.log("📊 即将启动主题构建...")
                TopicFormulation.GetQuestionsFromReview.Main(
                    topic_dir,
                    ConfigParams['Topic'],
                    ConfigParams['Threads'],
                    ClaudeApiFunctions,
                    OpenAIApiFunctions,
                    FromReview=not ConfigParams.get('DirectTopicGeneration', False),
                    STDOUT=sys.stdout,
                    MaxToken=ConfigParams['MaxToken']
                )
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                TopicFormulation.GetQuestionsFromReview.Main2(
                    topic_dir,
                    ConfigParams['Topic'],
                    ConfigParams['Threads'],
                    ClaudeApiFunctions,
                    OpenAIApiFunctions,
                    STDOUT=sys.stdout,
                    MaxToken=ConfigParams['MaxToken']
                )
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                TopicFormulation.GetQuestionsFromReview.Main3(
                    topic_dir,
                    ConfigParams['Topic'],
                    ConfigParams['Threads'],
                    ClaudeApiFunctions,
                    OpenAIApiFunctions,
                    STDOUT=sys.stdout,
                    MaxToken=ConfigParams['MaxToken']
                )
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")                
                ConfigParams['SkipTopicFormulation'] = True
                SaveConfigParams()
                self.root.after(0, lambda: self.auto_check_skip_option('skip_topic'))
                self.root.after(0, lambda: self.log(self.translate('topic_formulation_completed')))
        except Exception as e:
            if "stopped by user" in str(e) or self.stop_event.is_set() or GlobalStopFlag:
                self.root.after(0, lambda: self.update_step_status('topic_formulation', 'error'))
                raise
            error_msg = str(e)
            translated_error = self.translate_exception(error_msg)
            if translated_error != error_msg:
                self.root.after(0, lambda msg=translated_error: self.log_error_bold(msg))
            self.log(f"Error in topic formulation: {translated_error}")
            self.root.after(0, lambda msg=translated_error: self.set_step_error('topic_formulation', msg))
            raise Exception(translated_error)
    def knowledge_extraction_process(self):
        self.root.after(0, lambda: self.set_step_running('knowledge_extraction'))
        self.update_progress_label(self.translate('knowledge_extraction'))
        try:
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            if not EncryptedParamLists.get('ClaudeApiKey') and not EncryptedParamLists.get('OpenAIApiKey'):
                raise Exception('No Available API.')
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            if os.path.exists(f'{RootDirectory}{os.sep}Temp{os.sep}QuestionsForReview.txt'):
                knowledge_dir = f'{RootDirectory}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir'
                pdf_dir = f'{knowledge_dir}{os.sep}RawFromPDF'
                os.makedirs(pdf_dir, exist_ok=True)
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                [shutil.copy(f'{RootDirectory}{os.sep}Temp{os.sep}LiteratureSearchWorkDir{os.sep}{f}',
                             f'{pdf_dir}{os.sep}{f}')
                 for f in os.listdir(f'{RootDirectory}{os.sep}Temp{os.sep}LiteratureSearchWorkDir')
                 if f.startswith('10.') and f.endswith('.txt')]
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                self.log("📊 即将启动知识提取...")
                KnowledgeExtraction.XMLFormattedPrompt.GetDataList(knowledge_dir, MaxToken=ConfigParams['MaxToken'])
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                KnowledgeExtraction.GetAllResponse.Main(
                    knowledge_dir,
                    ConfigParams['Threads'],
                    ClaudeApiFunctions,
                    OpenAIApiFunctions,
                    STDOUT=sys.stdout,
                )
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                KnowledgeExtraction.AnswerIntegration.Main(
                    knowledge_dir,
                    ConfigParams['Threads'],
                    ClaudeApiFunctions,
                    OpenAIApiFunctions,
                    STDOUT=sys.stdout,
                    MaxToken=ConfigParams['MaxToken']
                )
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                try:
                    self.log("🔍 获取 Elsevier API Key...")
                    elsevier_api_key = self.get_elsevier_api_key()
                    self.log("✅ Elsevier API Key 获取成功")
                except Exception as e:
                    self.log(f"⚠️ 无法获取可用的 Elsevier API Key: {str(e)}")
                    elsevier_api_key = ''
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                KnowledgeExtraction.LinkAnswer.Main(knowledge_dir, elsevier_api_key)
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                KnowledgeExtraction.SplitIntoFolders.Main(f'{knowledge_dir}{os.sep}Answer', STDOUT=sys.stdout)
                if self.stop_event.is_set() or GlobalStopFlag:
                    raise Exception("Process stopped by user")
                ConfigParams['SkipKnowledgeExtraction'] = True
                SaveConfigParams()
                self.root.after(0, lambda: self.auto_check_skip_option('skip_knowledge'))
                self.root.after(0, lambda: self.log(self.translate('knowledge_extraction_completed')))
        except Exception as e:
            if "stopped by user" in str(e) or self.stop_event.is_set() or GlobalStopFlag:
                self.root.after(0, lambda: self.update_step_status('knowledge_extraction', 'error'))
                raise
            error_msg = str(e)
            translated_error = self.translate_exception(error_msg)
            if translated_error != error_msg:
                self.root.after(0, lambda msg=translated_error: self.log_error_bold(msg))
            self.log(f"Error in knowledge extraction: {translated_error}")
            self.root.after(0, lambda msg=translated_error: self.set_step_error('knowledge_extraction', msg))
            raise Exception(translated_error)
    def compare_review_articles_process(self):
        self.root.after(0, lambda: self.set_step_running('review_comparison'))
        self.update_progress_label(self.translate('review_comparison'))
        try:
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            if not EncryptedParamLists.get('ClaudeApiKey') and not EncryptedParamLists.get('OpenAIApiKey'):
                raise Exception('No Available API.')
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            self.log("📊 即将启动综述比较...")
            ReviewComposition.CompareTwoReviewArticles.Main(
                f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph',
                ConfigParams['Threads'],
                5,
                sys.stdout,
                ClaudeApiFunctions,
                OpenAIApiFunctions
            )
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            compare_path = f'{RootDirectory}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph{os.sep}CompareParagraph'
            ReviewComposition.Advanced_ComparedScore.Main2(compare_path)
            if self.stop_event.is_set() or GlobalStopFlag:
                raise Exception("Process stopped by user")
            ConfigParams['SkipCompareTwoReviewArticles'] = True
            SaveConfigParams()
            self.root.after(0, lambda: self.auto_check_skip_option('skip_compare'))
            self.root.after(0, lambda: self.log(self.translate('review_comparison_completed')))
        except Exception as e:
            if "stopped by user" in str(e) or self.stop_event.is_set() or GlobalStopFlag:
                self.root.after(0, lambda: self.update_step_status('review_comparison', 'error'))
                raise
            error_msg = str(e)
            translated_error = self.translate_exception(error_msg)
            if translated_error != error_msg:
                self.root.after(0, lambda msg=translated_error: self.log_error_bold(msg))
            self.log(f"Error in review comparison: {translated_error}")
            self.root.after(0, lambda msg=translated_error: self.set_step_error('review_comparison', msg))
            raise Exception(translated_error)
    def force_terminate_thread(self, thread):
        if not thread or not thread.is_alive():
            return False
        try:
            thread_id = thread.ident
            if thread_id is None:
                return False
            if os.name == 'nt':
                import ctypes
                import sys
                THREAD_TERMINATE = 0x0001
                THREAD_SUSPEND_RESUME = 0x0002
                THREAD_GET_CONTEXT = 0x0008
                THREAD_SET_CONTEXT = 0x0010
                THREAD_QUERY_INFORMATION = 0x0040
                THREAD_ALL_ACCESS = 0x1F03FF
                kernel32 = ctypes.windll.kernel32
                handle = None
                for access_right in [THREAD_ALL_ACCESS, THREAD_TERMINATE | THREAD_SUSPEND_RESUME, THREAD_TERMINATE]:
                    handle = kernel32.OpenThread(access_right, False, thread_id)
                    if handle:
                        break
                if handle:
                    try:
                        kernel32.SuspendThread(handle)
                        result = kernel32.TerminateThread(handle, -1)
                        if result:
                            kernel32.CloseHandle(handle)
                            return True
                        else:
                            error_code = kernel32.GetLastError()
                            try:
                                if hasattr(thread, '_target'):
                                    ctypes.pythonapi.PyThreadState_SetAsyncExc(
                                        ctypes.c_long(thread_id),
                                        ctypes.py_object(SystemExit)
                                    )
                                    kernel32.CloseHandle(handle)
                                    return True
                            except:
                                pass
                            kernel32.CloseHandle(handle)
                            return False
                    finally:
                        if handle:
                            kernel32.CloseHandle(handle)
                else:
                    try:
                        import ctypes
                        ctypes.pythonapi.PyThreadState_SetAsyncExc(
                            ctypes.c_long(thread_id),
                            ctypes.py_object(SystemExit)
                        )
                        return True
                    except:
                        pass
            else:
                import signal
                try:
                    os.kill(thread_id, signal.SIGTERM)
                    time.sleep(0.1)
                    if not thread.is_alive():
                        return True
                    os.kill(thread_id, signal.SIGKILL)
                    return True
                except:
                    pass
            return False
        except Exception as e:
            print(f"Error terminating thread {thread.name}: {e}")
            return False
    def monitor_and_interrupt_threads(self):
        try:
            interrupted_count = 0
            failed_count = 0
            all_threads = threading.enumerate()
            self.log(f"🔍 当前活跃线程总数: {len(all_threads)}")
            threads_to_interrupt = []
            for thread in all_threads:
                if thread == threading.main_thread():
                    continue
                if thread == threading.current_thread():
                    continue
                thread_name_lower = thread.name.lower()
                if any(gui_keyword in thread_name_lower for gui_keyword in ['tkinter', 'gui', 'mainloop', 'tk']):
                    continue
                threads_to_interrupt.append(thread)
            self.log(f"🎯 识别出需要中断的线程数: {len(threads_to_interrupt)}")
            for thread in threads_to_interrupt:
                try:
                    terminated = False
                    for _ in range(1):
                        if hasattr(thread, '_stop') and callable(thread._stop):
                            try:
                                thread._stop()
                                time.sleep(0.1)
                                if not thread.is_alive():
                                    terminated = True
                            except:
                                pass
                    if not terminated and hasattr(thread, '_stop_event'):
                        try:
                            thread._stop_event.set()
                            time.sleep(0.05)
                            if not thread.is_alive():
                                terminated = True
                        except:
                            pass
                    if not terminated:
                        if self.force_terminate_thread(thread):
                            terminated = True
                            interrupted_count += 1
                        else:
                            if os.name == 'nt' and thread.ident:
                                try:
                                    import ctypes
                                    ctypes.pythonapi.PyThreadState_SetAsyncExc(
                                        ctypes.c_long(thread.ident),
                                        ctypes.py_object(SystemExit)
                                    )
                                    time.sleep(0.1)
                                    if not thread.is_alive():
                                        terminated = True
                                        interrupted_count += 1
                                    else:
                                        ctypes.pythonapi.PyThreadState_SetAsyncExc(
                                            ctypes.c_long(thread.ident),
                                            None
                                        )
                                except:
                                    pass
                    if not terminated:
                        failed_count += 1
                        self.log(f"❌ 无法终止线程: {thread.name}")
                        try:
                            if hasattr(thread, '_target') and thread._target:
                                self.log(f"   目标函数: {thread._target}")
                            if hasattr(thread, '_args') and thread._args:
                                self.log(f"   参数: {thread._args[:50]}...")
                        except:
                            pass
                except Exception as e:
                    self.log(f"⚠️ 中断线程时出错: {thread.name}, {str(e)}")
                    failed_count += 1
                    continue
            time.sleep(0.5)
            remaining_threads = [t for t in threading.enumerate() 
                               if t not in [threading.main_thread(), threading.current_thread()]
                               and not any(gui in t.name.lower() for gui in ['tkinter', 'gui', 'mainloop', 'tk'])]
            if remaining_threads:
                self.force_cleanup_stubborn_threads(remaining_threads)
            return interrupted_count
        except Exception as e:
            self.log(f"⚠️ 监控线程时出错: {str(e)}")
            return 0
    def force_cleanup_stubborn_threads(self, threads):
        try:
            if os.name == 'nt':
                import ctypes
                kernel32 = ctypes.windll.kernel32
                for thread in threads:
                    if not thread.ident:
                        continue
                    try:
                        for _ in range(1):
                            handle = kernel32.OpenThread(0x1F03FF, False, thread.ident)
                            if handle:
                                suspend_count = kernel32.SuspendThread(handle)
                                if suspend_count != -1:
                                    kernel32.TerminateThread(handle, -1)
                                kernel32.CloseHandle(handle)
                        if thread.is_alive():
                            try:
                                thread._is_stopped = True
                                thread._tstate_lock = None
                            except:
                                pass
                    except Exception as e:
                        self.log(f"⚠️ 强制清理线程失败: {thread.name}, {str(e)}")
            time.sleep(0.5)
        except Exception as e:
            self.log(f"⚠️ 强制清理时出错: {str(e)}")
    def force_kill_processes(self):
        try:
            self.stop_event.set()
            global GlobalStopFlag
            GlobalStopFlag = True
            if self.inject_stop_check_into_modules():
                pass
            shutdown_count = self.force_shutdown_executors()
            if shutdown_count > 0:
                pass
            interrupted_count = self.monitor_and_interrupt_threads()
            if interrupted_count > 0:
                pass
            if self.main_process_thread and self.main_process_thread.is_alive():
                self.main_process_thread.join(timeout=1)
                if self.main_process_thread.is_alive():
                    if self.force_terminate_thread(self.main_process_thread):
                        pass
                        self.send_multiple_interrupt_signals()
                        time.sleep(1)
                        if self.main_process_thread.is_alive():
                            self.force_cleanup_stubborn_threads([self.main_process_thread])
            self.main_process_thread = None
            self.process_start_time = None
            self.active_threads.clear()
            remaining = len([t for t in threading.enumerate() 
                           if t not in [threading.main_thread(), threading.current_thread()]
                           and not any(gui in t.name.lower() for gui in ['tkinter', 'gui', 'mainloop', 'tk'])])
        except Exception as e:
            self.log(f"⚠️ 执行停止策略时出现警告: {str(e)}")
            import traceback
            traceback.print_exc()
