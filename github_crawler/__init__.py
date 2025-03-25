from .crawler import GitHubCrawler
from .analyzer import RepoAnalyzer
from .utils import  save_csv , run_crawler
from .models import Repository

__version__ = "1.0.0"

# Import the main function to make it available at the module level

__all__ = [
    'GitHubCrawler',
    'RepoAnalyzer',
    'Repository',
    'save_json',
    'save_csv',
    'run_crawler'
]