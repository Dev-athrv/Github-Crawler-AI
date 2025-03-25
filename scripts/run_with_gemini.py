#!/usr/bin/env python3
"""
Script to run the GitHub crawler with Gemini for embedding and analysis.
"""
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


# Add the parent directory to the path to allow importing the package
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from github_crawler import run_crawler


def main():
    parser = argparse.ArgumentParser(
        description="Run GitHub crawler with Gemini for embedding and analysis."
    )
    parser.add_argument(
        "--github-token", 
        help="GitHub token to increase rate limit", 
        default=None
    )
    parser.add_argument(
        "--gemini-api-key", 
        help="Gemini API key", 
        default=os.environ.get("GEMINI_API_KEY")
    )
    parser.add_argument(
        "--min-stars", 
        type=int, 
        help="Minimum number of stars for repositories", 
        default=10
    )
    parser.add_argument(
        "--max-results", 
        type=int, 
        help="Maximum number of repositories to collect", 
        default=100
    )
    parser.add_argument(
        "--max-pages", 
        type=int, 
        help="Maximum number of pages to crawl", 
        default=5
    )
    parser.add_argument(
        "--output-json", 
        help="Path to output JSON file", 
        default="gemini_embedded_repos.json"
    )
    parser.add_argument(
        "--output-csv", 
        help="Path to output CSV file", 
        default="gemini_embedded_repos.csv"
    )
    parser.add_argument(
        "--analyze", 
        action="store_true", 
        help="Analyze repositories with AI"
    )
    
    args = parser.parse_args()

    if not args.gemini_api_key:
        parser.error("Gemini API key is required. Provide it via --gemini-api-key or set the GEMINI_API_KEY environment variable.")

    # Run the crawler
    results = run_crawler(
        github_token=args.github_token,
        gemini_api_key=args.gemini_api_key,
        use_ollama=False,  # Use Gemini for embeddings
        min_stars=args.min_stars,
        max_results=args.max_results,
        output_json=args.output_json,
        output_csv=args.output_csv,
        analyze_with_ai=args.analyze,
        max_pages=args.max_pages
    )

    print(f"\nCrawling complete! Results saved to {args.output_json} and {args.output_csv}")
    print(f"Found {len(results)} repositories that match the criteria.")


if __name__ == "__main__":
    main()