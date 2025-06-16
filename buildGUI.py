import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path
class DeepReviewBuilder:
    def __init__(self):
        self.project_root = Path('.').resolve()
        self.required_files = [
            'main.py',
            'GUI.py', 
            'language_resources.jsonl',
            'font.ttf'
        ]
        self.backup_files = {}
    def check_requirements(self):
        print("🔍 检查构建要求...")
        missing_files = []
        for file in self.required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        if missing_files:
            print(f"❌ 缺少必要文件: {missing_files}")
            return False
        try:
            result = subprocess.run(['pyinstaller', '--version'], 
                                  capture_output=True, text=True)
            print(f"✅ PyInstaller版本: {result.stdout.strip()}")
        except FileNotFoundError:
            print("❌ PyInstaller未安装，请运行: pip install pyinstaller")
            return False
        print("✅ 所有要求已满足")
        return True
    def backup_original_files(self):
        print("📋 备份原始文件...")
        files_to_backup = ['main.py', 'GUI.py']
        for file in files_to_backup:
            if os.path.exists(file):
                backup_path = f"{file}.backup"
                shutil.copy2(file, backup_path)
                self.backup_files[file] = backup_path
                print(f"  ✅ 已备份: {file} -> {backup_path}")
    def modify_source_code(self):
        print("🔧 修改源代码...")
        self.modify_main_file()
        self.modify_gui_file()
        print("✅ 源代码修改完成")
    def modify_main_file(self):
        main_file = 'main.py'
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        insert_point = content.find("os.chdir('Temp')")
        if insert_point == -1:
            print("⚠️ 未找到os.chdir('Temp')，手动添加资源复制代码")
            return
        resource_copy_code = '''
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)
def copy_resources_to_temp():
    resource_files = ['language_resources.jsonl', 'font.ttf']
    for filename in resource_files:
        source_path = get_resource_path(filename)
        dest_path = os.path.join('Temp', filename)
        try:
            if os.path.exists(source_path):
                shutil.copy2(source_path, dest_path)
                print(f"✅ 已复制资源文件: {filename}")
            else:
                print(f"⚠️ 资源文件不存在: {source_path}")
        except Exception as e:
            print(f"❌ 复制资源文件失败 {filename}: {e}")
copy_resources_to_temp()
'''
        new_content = content[:insert_point] + resource_copy_code + content[insert_point:]
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✅ 已修改: {main_file}")
    def modify_gui_file(self):
        gui_file = 'GUI.py'
        with open(gui_file, 'r', encoding='utf-8') as f:
            content = f.read()
        old_load_func_start = content.find("def load_language_resources():")
        if old_load_func_start != -1:
            func_end = content.find("def ", old_load_func_start + 1)
            if func_end == -1:
                func_end = len(content)
            new_load_func = '''def load_language_resources():
    resources = {'zh': {}, 'en': {}}
    possible_paths = [
        'language_resources.jsonl',
        os.path.join('..', 'language_resources.jsonl'),
        os.path.join(RootDirectory, 'language_resources.jsonl'),
        os.path.join(RootDirectory, 'Temp', 'language_resources.jsonl'),
    ]
    for file_path in possible_paths:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line.strip())
                            key = data['key']
                            resources['zh'][key] = data['zh']
                            resources['en'][key] = data['en']
                print(f"✅ 成功加载语言资源: {file_path}")
                return resources
        except Exception as e:
            continue
    print("⚠️ 未找到语言资源文件，使用默认文本")
    return resources
'''
            new_content = content[:old_load_func_start] + new_load_func + content[func_end:]
            with open(gui_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  ✅ 已修改: {gui_file}")
    def create_spec_file(self):
        print("📝 创建.spec文件...")
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-
import os
datas = [
    ('language_resources.jsonl', '.'),
    ('font.ttf', '.'),
]
project_dirs = ['Utility', 'LiteratureSearch', 'TopicFormulation', 
                'KnowledgeExtraction', 'ReviewComposition', 'MultiDownload']
for dir_name in project_dirs:
    if os.path.exists(dir_name):
        datas.append((dir_name, dir_name))
hiddenimports = [
    'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.simpledialog', 'tkinter.font',
    'requests', 'psutil', 'json', 'hashlib', 'webbrowser', 'datetime', 'threading',
    'subprocess', 'shutil', 'traceback', 'functools', 'importlib', 'time', 're', 'os', 'sys', 'io',
    'moderngui_main', 'ModernGUI','tiktoken_ext.openai_public','tiktoken_ext'
]
excludes = [
    'tensorflow', 'tensorflow_estimator', 'tensorflow_addons', 'tensorflow_io_gcs_filesystem',
    'tensorboard', 'tensorboard_data_server', 'tensorboard_plugin_wit',
    'torch', 'torchvision', 'torchaudio',
    'keras', 'Keras_Preprocessing',
    'sklearn', 'scikit_learn', 'scikit_image',
    'xgboost', 'lightgbm', 'catboost',
    'cv2', 'opencv_python', 'opencv_contrib_python',
    'Pillow',
    'moviepy', 'imageio', 'imageio_ffmpeg',
    'skimage', 'scikit_image',
    'paddleocr', 'paddlepaddle', 'paddle_bfloat',
    'whisper',
    'pydub',
    'statsmodels',
    'sympy',
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
    'wx', 'wxPython',
    'flask', 'Flask', 'flask_babel',
    'fastapi', 'fastapi_cli', 'fastapi_poe',
    'starlette', 'uvicorn',
    'django',
    'jupyter', 'jupyter_core', 'jupyterlab', 'notebook', 'ipython', 'IPython',
    'nbformat', 'nbconvert',
    'pytest', 'unittest', 'doctest', 'coverage', 'coveralls',
    'nose', 'nose2',
    'sphinx', 'mkdocs',
    'pypandoc',
    'pdb', 'cProfile', 'profile', 'gprof2dot',
    'memory_profiler', 'line_profiler',
    'boto3', 'botocore', 's3transfer',
    'google_cloud', 'google_api_python_client', 'google_auth', 'google_auth_httplib2', 'google_auth_oauthlib',
    'azure', 'azure_storage', 'azure_identity',
    'tencentcloud_sdk_python', 'tencentcloud_sdk_python_common', 'tencentcloud_sdk_python_ims',
    'tccli',
    'bce_python_sdk',
    'sqlalchemy', 'SQLAlchemy',
    'pymongo', 'redis', 'psycopg2',
    'peewee', 'dynamo3',
    'python_docx', 'python_pptx', 'openpyxl', 'xlrd', 'XlsxWriter',
    'pdf2docx', 'pdf2image', 'pdfminer', 'PyPDF2', 'pikepdf',
    'msg_parser',
    'scrapy',
    'nltk', 'spacy', 'transformers',
    'langchain', 'langchainplus_sdk',
    'polyglot', 'langdetect', 'langid',
    'Morfessor',
    'plotly', 'bokeh', 'altair',
    'graphviz', 'pydot', 'pydotplus',
    'visualdl',
    'cryptography',
    'pycryptodome',
    'pyotp',
    'PyJWT',
    'pyusb', 'pyserial',
    'pywifi', 'netifaces',
    'python_geoip_python3',
    'pyglet', 'pygame',
    'lxml',
    'PyYAML', 'yaml',
    'toml', 'configobj',
    'h5py',
    'rarfile',
    'ase',
    'nibabel',
    'nipype',
    'netCDF4',
    'fire',
    'click',
    'typer',
    'bottle',
    'aiohttp', 'aiosignal', 'async_timeout',
    'trio', 'trio_websocket',
    'websockets',
    'datasets',
    'huggingface_hub', 'tokenizers', 'transformers',
    'zhipuai',
    'copyleaks',
    'etelemetry',
    'flywheel',
    'tweepy',
    'rank_bm25',
    'schedule',
    'retry',
    'unstructured',
    'prov',
    'setuptools', 'pip', 'wheel',
    'cramjam', 'fastparquet', 'pyarrow', 'pyarrow_hotfix',
    'lmdb',
    'xxhash',
    'google_generativeai', 'google_ai_generativelanguage',
    'Unidecode',
    'pypinyin',
    'Babel', 'babel',
    'patsy',
    'numba', 'llvmlite',
    'numexpr',
]
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DeepReview',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.png' if os.path.exists('icon.png') else None,
)
'''
        with open('DeepReview_auto.spec', 'w', encoding='utf-8') as f:
            f.write(spec_content)
        print("✅ .spec文件已创建")
        return 'DeepReview_auto.spec'
    def build_executable(self):
        print("🚀 开始构建可执行文件...")
        for dir_name in ['build', 'dist']:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                print(f"  🗑️ 已清理: {dir_name}")
        spec_file = self.create_spec_file()
        cmd = ['pyinstaller', spec_file]
        print(f"🔨 执行命令: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ 构建成功！")
            exe_path = 'dist/DeepReview.exe'
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"📦 可执行文件: {os.path.abspath(exe_path)}")
                print(f"📏 文件大小: {size_mb:.1f} MB")
                return True
            else:
                print("❌ 未找到生成的可执行文件")
                return False
        except subprocess.CalledProcessError as e:
            print("❌ 构建失败！")
            print("错误信息:")
            print(e.stderr)
            return False
    def restore_original_files(self):
        print("🔄 恢复原始文件...")
        for original_file, backup_file in self.backup_files.items():
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, original_file)
                os.remove(backup_file)
                print(f"  ✅ 已恢复: {original_file}")
    def test_executable(self):
        exe_path = 'dist/DeepReview.exe'
        if os.path.exists(exe_path):
            print("🧪 测试可执行文件...")
            print(f"请手动运行以下文件进行测试:")
            print(f"  {os.path.abspath(exe_path)}")
        else:
            print("❌ 可执行文件不存在，无法测试")
    def build(self):
        print("=" * 50)
        print("🏗️  Deep Review 自动构建工具")
        print("=" * 50)
        try:
            if not self.check_requirements():
                return False
            self.backup_original_files()
            self.modify_source_code()
            success = self.build_executable()
            if success:
                print("\n🎉 构建完成！")
                self.test_executable()
            else:
                print("\n💥 构建失败！")
            return success
        except Exception as e:
            print(f"\n💥 构建过程中发生错误: {e}")
            return False
        finally:
            self.restore_original_files()
            print("\n📋 清理完成")
if __name__ == "__main__":
    builder = DeepReviewBuilder()
    success = builder.build()
    if success:
        print("\n✅ 构建成功！可执行文件在 dist/ 目录中")
    else:
        print("\n❌ 构建失败！请检查错误信息")
        sys.exit(1)
