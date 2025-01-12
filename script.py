import argparse
import sys
import os
import shutil
import functools
from Utility import GetResponse
from TopicFormulation import GetQuestionsFromReview
RootDir = os.path.abspath('.')
TempDir = os.path.join(RootDir, 'Temp')
os.makedirs(TempDir, exist_ok=True)
os.chdir(TempDir)
sys.path.append(RootDir)
from LiteratureSearch import One_key_download, Advanced_Research
from TopicFormulation import GetQuestionsFromReview
from KnowledgeExtraction import XMLFormattedPrompt, GetAllResponse, AnswerIntegration, SplitIntoFolders, LinkAnswer
from ReviewComposition import GenerateParagraphOfReview, GenerateRatingsForReviewParagraphs, ExtractSectionsWithTags, \
    CompareTwoReviewArticles, Advanced_ComparedScore
import Utility.GetResponse
def run_literature_search(args):
    Advanced_Research.set_elsevier_api_key(args.elsevier_api_key)
    One_key_download.User_pages(
        args.serp_api_list,
        args.research_keys,
        args.screen_keys,
        args.start_year,
        args.end_year,
        args.q1,
        args.q23,
        args.demo
    )
def run_topic_formulation(args):
    claude_api = {}
    openai_api = {}
    if args.claude_api_keys:
        claude_api = {i: Utility.GetResponse.GetResponseFromClaude for i, _ in enumerate(args.claude_api_keys)}
    if args.openai_api_urls and args.openai_api_keys:
        openai_api = {i: functools.partial(Utility.GetResponse.GetResponseFromOpenAlClient,
                                           url=url, key=key, model=args.model)
                      for i, (url, key) in enumerate(zip(args.openai_api_urls, args.openai_api_keys))}
    if not claude_api and not openai_api:
        print("Warning: No API keys provided. The system will run with limited functionality.")
    work_dir = os.path.join(TempDir, 'TopicFormulationWorkDir')
    os.makedirs(work_dir, exist_ok=True)
    literature_search_dir = os.path.join(TempDir, 'LiteratureSearchWorkDir')
    if os.path.exists(literature_search_dir):
        for file in os.listdir(literature_search_dir):
            if file.startswith('10.') and file.endswith('_Review.txt'):
                shutil.copy(os.path.join(literature_search_dir, file), work_dir)
    else:
        print("Warning: Literature search results not found. Please run literature search first.")
    GetQuestionsFromReview.Main(
        work_dir,
        args.topic,
        args.threads,
        claude_api,
        openai_api,
        STDOUT=sys.stdout
    )
    if not os.path.exists(os.path.join(TempDir, 'ParagraphQuestionsForReview.txt')) or args.manual_outline:
        print("请在弹出的窗口中修改并保存大纲。关闭窗口后将执行下一步。")
        outline_path = os.path.join(work_dir, 'AllQuestionsFromReview', 'QuestionsFromReviewManual.txt')
        if os.path.exists(outline_path):
            os.system(f"notepad.exe {outline_path}")
        else:
            print("Warning: Outline file not found. Skipping manual editing.")
    GetQuestionsFromReview.Main2(
        work_dir,
        args.topic,
        args.threads,
        claude_api,
        openai_api,
        STDOUT=sys.stdout
    )
    if not os.path.exists(os.path.join(TempDir, 'ParagraphQuestionsForReview.txt')) or args.manual_outline:
        print("请在弹出的窗口中修改并保存大纲。关闭窗口后将执行下一步。")
        outline_path = os.path.join(work_dir, 'AllQuestionsFromReview', 'QuestionsFromReviewManual.txt')
        if os.path.exists(outline_path):
            os.system(f"notepad.exe {outline_path}")
        else:
            print("Warning: Outline file not found. Skipping manual editing.")
    GetQuestionsFromReview.Main2(
        work_dir,
        args.topic,
        args.threads,
        claude_api,
        openai_api,
        model=args.model
    )
def run_knowledge_extraction(args):
    claude_api = {}
    openai_api = {}
    if args.claude_api_keys:
        claude_api = {i: Utility.GetResponse.GetResponseFromClaude for i, _ in enumerate(args.claude_api_keys)}
    if args.openai_api_urls and args.openai_api_keys:
        openai_api = {i: functools.partial(Utility.GetResponse.GetResponseFromOpenAlClient,
                                           url=url, key=key, model=args.model)
                      for i, (url, key) in enumerate(zip(args.openai_api_urls, args.openai_api_keys))}
    if not claude_api and not openai_api:
        print("Warning: No API keys provided. The system will run with limited functionality.")
    work_dir = os.path.join(TempDir, 'KnowledgeExtractionWorkDir')
    os.makedirs(work_dir, exist_ok=True)
    XMLFormattedPrompt.GetDataList(work_dir, MaxToken=args.max_token)
    GetAllResponse.Main(
        work_dir,
        args.threads,
        claude_api,
        openai_api,
        STDOUT=sys.stdout
    )
    AnswerIntegration.Main(
        work_dir,
        args.threads,
        claude_api,
        openai_api,
        MaxToken=args.max_token,
        STDOUT=sys.stdout
    )
    LinkAnswer.Main(work_dir)
    SplitIntoFolders.Main(os.path.join(work_dir, "Answer"), STDOUT=sys.stdout)
def run_review_composition(args):
    claude_api = {}
    openai_api = {}
    if args.claude_api_keys:
        claude_api = {i: Utility.GetResponse.GetResponseFromClaude for i, _ in enumerate(args.claude_api_keys)}
    if args.openai_api_urls and args.openai_api_keys:
        openai_api = {i: functools.partial(Utility.GetResponse.GetResponseFromOpenAlClient,
                                           url=url, key=key, model=args.model)
                      for i, (url, key) in enumerate(zip(args.openai_api_urls, args.openai_api_keys))}
    if not claude_api and not openai_api:
        print("Warning: No API keys provided. The system will run with limited functionality.")
    work_dir = os.path.join(TempDir, 'ReviewCompositionWorkDir')
    os.makedirs(work_dir, exist_ok=True)
    raw_from_pdf_dir = os.path.join(work_dir, 'RawFromPDF')
    os.makedirs(raw_from_pdf_dir, exist_ok=True)
    literature_search_dir = os.path.join(TempDir, 'LiteratureSearchWorkDir')
    if os.path.exists(literature_search_dir):
        for file in os.listdir(literature_search_dir):
            if file.lower().endswith('.pdf'):
                shutil.copy(os.path.join(literature_search_dir, file), raw_from_pdf_dir)
        print(f"Copied PDF files to {raw_from_pdf_dir}")
    else:
        print("Warning: Literature search results not found. No PDF files copied.")
    GenerateParagraphOfReview.Main(
        work_dir,
        args.topic,
        args.threads,
        claude_api,
        openai_api,
        STDOUT=sys.stdout
    )
    GenerateRatingsForReviewParagraphs.Main(
        work_dir,
        args.threads,
        claude_api,
        openai_api,
        STDOUT=sys.stdout
    )
    ExtractSectionsWithTags.Main(os.path.join(work_dir, "BestParagraph"), STDOUT=sys.stdout)
    shutil.copy(os.path.join(work_dir, "BestParagraph", "draft.txt"), os.path.join(RootDir, "ReviewDraft.txt"))
def run_review_comparison(args):
    claude_api = {}
    openai_api = {}
    if args.claude_api_keys:
        claude_api = {i: functools.partial(Utility.GetResponse.GetResponseFromClaude, api_key=key)
                      for i, key in enumerate(args.claude_api_keys)}
    if args.openai_api_urls and args.openai_api_keys:
        openai_api = {i: functools.partial(Utility.GetResponse.GetResponseFromOpenAlClient,
                                           url=url, key=key, model=args.model)
                      for i, (url, key) in enumerate(zip(args.openai_api_urls, args.openai_api_keys))}
    if not claude_api and not openai_api:
        print("Warning: No API keys provided. The system will run with limited functionality.")
    work_dir = os.path.join(TempDir, 'ReviewCompositionWorkDir')
    try:
        CompareTwoReviewArticles.Main(
            os.path.join(work_dir, "Paragraph"),
            args.threads,
            args.repeat,
            sys.stdout,
            claude_api,
            openai_api
        )
    except Exception as e:
        print(f"Error in CompareTwoReviewArticles.Main: {str(e)}")
        print("Skipping comparison due to error.")
        return
    compare_path = os.path.join(work_dir, "Paragraph", "CompareParagraph")
    Advanced_ComparedScore.Main2(compare_path)
def main():
    parser = argparse.ArgumentParser(description="Automated Review Generation System")
    subparsers = parser.add_subparsers(dest='function', help='Function to run')
    search_parser = subparsers.add_parser('search', help='Run literature search')
    search_parser.add_argument("--serp_api_list", nargs="+", required=True, help="SerpAPI key list")
    search_parser.add_argument("--research_keys", nargs="+", required=True, help="Research keywords")
    search_parser.add_argument("--screen_keys", nargs="+", required=True, help="Screen keywords")
    search_parser.add_argument("--start_year", type=int, required=True, help="Start year for search")
    search_parser.add_argument("--end_year", type=int, required=True, help="End year for search")
    search_parser.add_argument("--q1", action="store_true", help="Include Q1 journals")
    search_parser.add_argument("--q23", action="store_true", help="Include Q2 and Q3 journals")
    search_parser.add_argument("--demo", action="store_true", help="Run in demo mode")
    search_parser.add_argument("--elsevier_api_key", required=True, help="Elsevier API key")
    topic_parser = subparsers.add_parser('topic', help='Run topic formulation')
    topic_parser.add_argument("--topic", required=True, help="Research topic")
    topic_parser.add_argument("--threads", type=int, default=4, help="Number of threads")
    topic_parser.add_argument("--claude_api_keys", nargs="+", help="Claude API keys")
    topic_parser.add_argument("--openai_api_urls", nargs="+", help="OpenAI compatible API URLs")
    topic_parser.add_argument("--openai_api_keys", nargs="+", help="OpenAI compatible API keys")
    topic_parser.add_argument("--model", default="gpt-3.5-turbo", help="Model name")
    topic_parser.add_argument("--manual_outline", action="store_true", help="Manually edit the outline")
    extract_parser = subparsers.add_parser('extract', help='Run knowledge extraction')
    extract_parser.add_argument("--threads", type=int, default=4, help="Number of threads")
    extract_parser.add_argument("--claude_api_keys", nargs="+", help="Claude API keys")
    extract_parser.add_argument("--openai_api_urls", nargs="+", help="OpenAI compatible API URLs")
    extract_parser.add_argument("--openai_api_keys", nargs="+", help="OpenAI compatible API keys")
    extract_parser.add_argument("--model", default="gpt-3.5-turbo", help="Model name")
    extract_parser.add_argument("--max_token", type=int, default=4000, help="Maximum token count")
    compose_parser = subparsers.add_parser('compose', help='Run review composition')
    compose_parser.add_argument("--topic", required=True, help="Research topic")
    compose_parser.add_argument("--threads", type=int, default=4, help="Number of threads")
    compose_parser.add_argument("--claude_api_keys", nargs="+", help="Claude API keys")
    compose_parser.add_argument("--openai_api_urls", nargs="+", help="OpenAI compatible API URLs")
    compose_parser.add_argument("--openai_api_keys", nargs="+", help="OpenAI compatible API keys")
    compose_parser.add_argument("--model", default="gpt-3.5-turbo", help="Model name")
    compare_parser = subparsers.add_parser('compare', help='Run review comparison')
    compare_parser.add_argument("--threads", type=int, default=4, help="Number of threads")
    compare_parser.add_argument("--claude_api_keys", nargs="+", help="Claude API keys")
    compare_parser.add_argument("--openai_api_urls", nargs="+", help="OpenAI compatible API URLs")
    compare_parser.add_argument("--openai_api_keys", nargs="+", help="OpenAI compatible API keys")
    compare_parser.add_argument("--model", default="gpt-3.5-turbo", help="Model name")
    compare_parser.add_argument("--repeat", type=int, default=5, help="Repeat count for comparison")
    args = parser.parse_args()
    if args.function is None:
        parser.print_help()
        sys.exit(1)
    try:
        if args.function == "search":
            run_literature_search(args)
        elif args.function == "topic":
            run_topic_formulation(args)
        elif args.function == "extract":
            run_knowledge_extraction(args)
        elif args.function == "compose":
            run_review_composition(args)
        elif args.function == "compare":
            run_review_comparison(args)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)
if __name__ == "__main__":
    main()
