<p align="center">
  <img src="https://github.com/Invalid-Null/AutomaticReviewGeneration/blob/main/Icon.png" height="150">
</p>

<h1 align="center">
  自动综述生成
  <br>
  Automatic Review Generation
</h1>

基于大语言模型的自动综述生成

Automatic Review Generation Method based on Large Language Models

[![Python package](https://github.com/Invalid-Null/AutomaticReviewGeneration/actions/workflows/python-package.yml/badge.svg)](https://github.com/Invalid-Null/AutomaticReviewGeneration/actions/workflows/python-package.yml)
![GitHub License](https://img.shields.io/github/license/Invalid-Null/AutomaticReviewGeneration?logo=github)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/Invalid-Null/AutomaticReviewGeneration/total)
![GitHub commit activity](https://img.shields.io/github/commit-activity/t/Invalid-Null/AutomaticReviewGeneration)
![GitHub last commit](https://img.shields.io/github/last-commit/Invalid-Null/AutomaticReviewGeneration)

![Support Platform](https://img.shields.io/badge/GUI%20平台-Windows-lightgrey.svg)
![Language](https://img.shields.io/badge/语言-Python3-yellow.svg)
![](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=Python&logoColor=ffffff)

# 重要提示：运行本系统需要以下API密钥 | Important: The following API keys are required

在开始使用前，请确保您拥有以下必要的API密钥：

Before starting, please ensure you have the following necessary API keys:

1. Google搜索API（用于Google Scholar搜索）| Google Search API (for Google Scholar search):
   
   - 获取地址 | Get from: https://serpapi.com/
2. 大语言模型API（选择一个或两个）| Large Language Model API (Choose one or both):
   
   - Claude：https://claude.ai/chats
   - 或 OpenAI格式兼容的API | Or OpenAI format compatible API
3. Elsevier研究产品API | Elsevier Research Products API:
   
   - 获取地址 | Get from: https://dev.elsevier.com/

注意：缺少某些API密钥可能会限制系统的部分功能。

Note: Missing certain API keys may limit some system functionalities.

# 概述 | Overview

本系统自动化了学术综述文章的生成过程。它包括文献搜索、主题制定、知识提取、综述撰写和综述比较等模块。

This system automates the process of generating academic review articles. It includes modules for literature search, topic formulation, knowledge extraction, review composition, and review comparison.

# 快速开始 | Quick Start

快速使用自动综述生成系统：

Get started with Automatic Review Generation quickly:

1. 下载软件 | Download Software:
   
   - 从[Releases](https://github.com/Invalid-Null/AutomaticReviewGeneration/releases)页面下载最新版本的`GUI.exe`
   - Download the latest `GUI.exe` from the [Releases](https://github.com/Invalid-Null/AutomaticReviewGeneration/releases) page
2. 配置API密钥 | Configure API Keys:
   
   - 在GUI界面中配置上述必要的API密钥 | Configure the above required API keys in GUI interface
3. 开始使用 | Start Using:
   
   - 运行GUI.exe | Run GUI.exe
   - 选择研究主题 | Select your research topic
   - 开始自动生成综述 | Start automatic review generation

注意：如果您是开发者或需要自定义功能，请参考下方的开发者安装指南。

Note: If you are a developer or need customized features, please refer to the developer installation guide below.

# 教程 | Tutorials

图形化界面使用中文教程 | Chinese tutorial on using GUI
English tutorial on using GUI

# 功能特性 | Features

文献搜索：搜索和下载相关学术论文。

Literature Search: Searches and downloads relevant academic papers.

主题制定：基于文献生成研究问题和大纲。

Topic Formulation: Generates research questions and outlines based on literature.

知识提取：从论文中提取并结构化知识。

Knowledge Extraction: Extracts and structures knowledge from papers.

综述撰写：撰写综述段落并生成草稿。

Review Composition: Composes review paragraphs and generates a draft.

综述比较：比较和评估不同的综述文章。

Review Comparison: Compares and evaluates different review articles.

## 操作系统要求 | OS Requirements

### GUI支持 | GUI Support

GUI支持*Windows*系统，并已在以下环境测试：

The GUI is supported for *Windows* and has been tested on:

+ Windows 10：需要Microsoft Edge浏览器进行文献下载。
  
  Windows 10: Microsoft Edge browser is required for literature downloading.

### 包支持 | Package Support

该包支持*Linux*、*Windows*或其他支持Python 3的平台。已在以下环境测试：

The package is supported for *Linux*, *Windows*, or other platforms that support Python 3. It has been tested on:

+ Windows 10：支持完整流程，需要Microsoft Edge浏览器进行文献下载。
  
  Windows 10: Full process supported, Microsoft Edge browser is required for literature downloading.
+ CentOS 7：支持除LiteratureSearch模块外的其他功能。
  
  CentOS 7: Supported without the LiteratureSearch module.

## 开发者安装 | Developer Installation

### 要求 | Requirements

- Python 3.7+
- Microsoft Edge（用于文献下载）| Microsoft Edge (for literature downloading)
- 所需Python包（通过`pip install -r requirements.txt`安装）：
  
  Required Python packages (install via `pip install -r requirements.txt`):
  
  - anthropic
  - beautifulsoup4
  - crossrefapi
  - elsapy
  - func-timeout
  - google-search-results
  - httpx
  - matplotlib
  - numpy
  - openai
  - pandas
  - pingouin
  - psutil
  - requests
  - rsa
  - scipy
  - selenium
  - serpapi
  - statsmodels
  - sympy
  - tiktoken
  - tqdm


### 步骤 | Steps

1. 克隆仓库：
   
   Clone the repository:
   
   ```
   git clone https://github.com/Invalid-Null/AutomaticReviewGeneration.git
   cd AutomaticReviewGeneration
   ```
2. 安装所需包：
   
   Install required packages:
   
   ```
   pip install -r requirements.txt
   ```

### GUI安装指南（Windows） | GUI Installation Guide (Windows):

在Windows上打包GUI：

To pack the GUI on Windows:

```
pyinstaller -Fw GUI.py -i Icon.png --hidden-import=tiktoken_ext.openai_public --hidden-import=tiktoken_ext
```

## 使用方法 | Usage

### GUI使用 | GUI Usage

运行GUI应用程序：

Run the GUI application:

```
python GUI_Advance.py
```

### 命令行使用 | Command-Line Usage

使用`script.py`进行命令行操作。以下是每个模块的示例，包含详细的参数说明：

Use `script.py` for command-line operations. Here are examples for each module with detailed parameter explanations:

1. 文献搜索 | Literature Search:
   
   ```
   python script.py search --serp_api_list key1 key2 --research_keys ai ml --screen_keys review survey --start_year 2020 --end_year 2023 --q1 --demo --elsevier_api_key YOUR_KEY
   ```
   
   参数 | Parameters:
   
   - `--serp_api_list`：SerpAPI密钥列表（必需） | List of SerpAPI keys (required)
   - `--research_keys`：研究关键词列表（必需） | List of research keywords (required)
   - `--screen_keys`：筛选关键词列表（必需） | List of screening keywords (required)
   - `--start_year`：搜索起始年份（必需） | Start year for the search (required)
   - `--end_year`：搜索结束年份（必需） | End year for the search (required)
   - `--q1`：包括Q1期刊（标志） | Include Q1 journals (flag)
   - `--q23`：包括Q2和Q3期刊（标志） | Include Q2 and Q3 journals (flag)
   - `--demo`：以演示模式运行（标志） | Run in demo mode (flag)
   - `--elsevier_api_key`：Elsevier API密钥（必需） | Elsevier API key (required)
2. 主题制定 | Topic Formulation:
   
   ```
   python script.py topic --topic "您的研究主题" [--threads 4] [--claude_api_keys key1 key2] [--openai_api_urls url1 url2] [--openai_api_keys key1 key2] [--model gpt-3.5-turbo] [--manual_outline]
   ```
   
   参数 | Parameters:
   
   - `--topic`：指定您的研究主题（必需） | Specify your research topic (required)
   - `--threads`：并行处理的线程数（默认：4） | Number of threads for parallel processing (default: 4)
   - `--claude_api_keys`：Claude API密钥列表（可选） | List of Claude API keys (optional)
   - `--openai_api_urls`：OpenAI兼容API URL列表（可选） | List of OpenAI compatible API URLs (optional)
   - `--openai_api_keys`：OpenAI兼容API密钥列表（可选） | List of OpenAI compatible API keys (optional)
   - `--model`：指定要使用的AI模型（默认：gpt-3.5-turbo） | Specify the AI model to use (default: gpt-3.5-turbo)
   - `--manual_outline`：可选标志，启用大纲的手动编辑 | Optional flag to enable manual editing of the outline
3. 知识提取 | Knowledge Extraction:
   
   ```
   python script.py extract --threads 4 --claude_api_keys key1 key2 --openai_api_urls url1 url2 --openai_api_keys key1 key2 --model gpt-3.5-turbo --max_token 4000
   ```
   
   参数 | Parameters:
   
   - `--threads`：并行处理的线程数（必需） | Number of threads for parallel processing (required)
   - `--claude_api_keys`：Claude API密钥列表（必需） | List of Claude API keys (required)
   - `--openai_api_urls`：OpenAI兼容API URL列表（必需） | List of OpenAI compatible API URLs (required)
   - `--openai_api_keys`：OpenAI兼容API密钥列表（必需） | List of OpenAI compatible API keys (required)
   - `--model`：指定要使用的AI模型（必需） | Specify the AI model to use (required)
   - `--max_token`：最大令牌数（必需） | Maximum token count (required)
4. 综述撰写 | Review Composition:
   
   ```
   python script.py compose --topic "您的研究主题" --threads 4 --claude_api_keys key1 key2 --openai_api_urls url1 url2 --openai_api_keys key1 key2 --model gpt-3.5-turbo
   ```
   
   参数 | Parameters:
   
   - `--topic`：研究主题（必需） | Research topic (required)
   - `--threads`：并行处理的线程数（必需） | Number of threads for parallel processing (required)
   - `--claude_api_keys`：Claude API密钥列表（必需） | List of Claude API keys (required)
   - `--openai_api_urls`：OpenAI兼容API URL列表（必需） | List of OpenAI compatible API URLs (required)
   - `--openai_api_keys`：OpenAI兼容API密钥列表（必需） | List of OpenAI compatible API keys (required)
   - `--model`：指定要使用的AI模型（必需） | Specify the AI model to use (required)
5. 综述比较 | Review Comparison:
   
   ```
   python script.py compare --threads 4 --claude_api_keys key1 key2 --openai_api_urls url1 url2 --openai_api_keys key1 key2 --model gpt-3.5-turbo --repeat 5
   ```
   
   参数 | Parameters:
   
   - `--threads`：并行处理的线程数（必需） | Number of threads for parallel processing (required)
   - `--claude_api_keys`：Claude API密钥列表（必需） | List of Claude API keys (required)
   - `--openai_api_urls`：OpenAI兼容API URL列表（必需） | List of OpenAI compatible API URLs (required)
   - `--openai_api_keys`：OpenAI兼容API密钥列表（必需） | List of OpenAI compatible API keys (required)
   - `--model`：指定要使用的AI模型（必需） | Specify the AI model to use (required)
   - `--repeat`：比较重复次数（必需） | Number of repetitions for comparison (required)

## 目录结构 | Directory Structure

- Temp/: 所有操作的工作目录 | Working directory for all operations
- LiteratureSearch/: 文献搜索模块 | Module for literature search
- TopicFormulation/: 主题制定模块 | Module for topic formulation
- KnowledgeExtraction/: 知识提取模块 | Module for knowledge extraction
- ReviewComposition/: 综述撰写和比较模块 | Module for review composition and comparison
- Utility/: 实用函数和模块 | Utility functions and modules

# 发表情况 | Publication

专利申请已被专利局受理；文章正在提交中。

The patent application has been accepted by the Patent Office; the article is being submitted.

[arXiv预印本 | arXiv Preprint](https://arxiv.org/abs/2407.20906)

引用格式 | Citation Format:

论文引用 | Paper Citation:

```
Wu S, Ma X, Luo D, et al. Automated review generation method based on large language models[J]. arXiv preprint arXiv:2407.20906, 2024.
```

BibTeX:

```
@misc{wu2024automatedreviewgenerationmethod,
  title={Automated Review Generation Method Based on Large Language Models}, 
  author={Shican Wu and Xiao Ma and Dehui Luo and Lulu Li and Xiangcheng Shi and Xin Chang and Xiaoyun Lin and Ran Luo and Chunlei Pei and Zhi-Jian Zhao and Jinlong Gong},
  year={2024},
  eprint={2407.20906},
  archivePrefix={arXiv},
  primaryClass={cs.CL},
  url={https://arxiv.org/abs/2407.20906}, 
}
```

# 许可证 | License

本项目采用Apache 2.0许可证。

This project is covered under the Apache 2.0 License.

# 注意事项 | Note

在运行系统之前，请确保您拥有必要的API密钥（SerpAPI、Elsevier、Claude、OpenAI）。如果缺少某些API密钥，系统可以以有限的功能运行。

Ensure you have the necessary API keys (SerpAPI, Elsevier, Claude, OpenAI) before running the system. The system can run with limited functionality if some API keys are missing.

# 警告 | Warning

该程序需要以基于Windows的GUI程序作为运行的基础，命令行界面作为辅助功能。命令行界面的输出和运行方式不应作为最终参考。

The program requires a Windows-based GUI program as its foundation for operation, with the command-line interface serving as an auxiliary feature. The output and running mode of the command-line interface should not be considered as the final reference.

# 常见问题 | FAQ

Q: 如何获取所需的API密钥？
How to obtain the required API keys?

A: 请访问各API提供商的官方网站：
Please visit the official websites of API providers:

- SerpAPI: https://serpapi.com/
- Claude: https://claude.ai/
- OpenAI: https://openai.com/
- Elsevier: https://dev.elsevier.com/

Q: 是否支持其他操作系统？
Is it supported on other operating systems?

A: GUI界面目前仅支持Windows系统，但命令行接口支持所有主流操作系统。
The GUI interface currently only supports Windows, but the command-line interface supports all major operating systems.

Q: 可以使用离线模式吗？
Can it be used offline?

A: 不可以，系统需要联网访问各种API服务。
No, the system requires internet access to various API services.


