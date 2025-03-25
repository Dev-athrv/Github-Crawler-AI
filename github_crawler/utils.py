"""
Utility functions for the GitHub crawler.
"""

import json
import csv
import time
import os
from typing import List, Dict, Any, Optional


def save_csv(repos: List[Dict[str, Any]], filename: str) -> None:
    """
    Save repository data to a CSV file with additional columns.

    Args:
        repos (list): List of repository information
        filename (str): Output CSV filename
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Write header with AI response column
        csvwriter.writerow([
            'github_url',
            'name',
            'description',
            'language',
            'stars',
            'keyword_matches',
            'matching_keywords',
            'topics',
            'ai_response'
        ])

        # Write data
        for repo in repos:
            # Join topics and matching keywords with commas
            topics_str = ', '.join(repo.get('topics', []))
            matching_keywords_str = ', '.join(repo.get('matching_keywords', []))

            csvwriter.writerow([
                repo.get('html_url'),
                repo.get('name'),
                repo.get('description', ''),
                repo.get('language', ''),
                repo.get('stars', 0),
                repo.get('keyword_match_count', 0),
                matching_keywords_str,
                topics_str,
                repo.get('ai_response', 'N/A')
            ])

    print(f"CSV data saved to {filename}")


def run_crawler(github_token: Optional[str] = None, 
                gemini_api_key: Optional[str] = None, 
                use_ollama: bool = False, 
                min_stars: int = 10, 
                max_results: int = 100, 
                output_json: str = "embedded_repos.json", 
                output_csv: str = "embedded_repos.csv", 
                sort: str = "stars", 
                max_pages: int = 10, 
                analyze_with_ai: bool = True) -> List[Dict[str, Any]]:
    """
    Run the GitHub crawler with the specified parameters.
    This function replaces the command-line based main() to work better in notebooks or scripts.
    
    Args:
        github_token: GitHub API token
        gemini_api_key: Google Gemini API key
        use_ollama: Whether to use Ollama for AI analysis
        min_stars: Minimum repository stars to include
        max_results: Maximum number of results to return
        output_json: Output JSON filename
        output_csv: Output CSV filename
        sort: How to sort GitHub results
        max_pages: Maximum pages to fetch from GitHub API
        analyze_with_ai: Whether to use AI analysis
        
    Returns:
        List of repository data dictionaries
    """
    from github_crawler.crawler import GitHubCrawler
    from github_crawler.analyzer import RepoAnalyzer

    
    # Define the specific keywords you're looking for
    required_keywords = [
        "MSP430", "TM4C123", "MSP432", "STM32", "STM32F7", "STM8",
        "ESP8266", "Raspberry", "Beaglebone", "Assembly", "RTOS",
        "Automotive", "OS", "WindowCE", "Compiler", "Bootloader",
        "embedded", "embedded gui", "firmware", "driver", "microcontroller",
        "real-time", "baremetal", "bare-metal", "HAL", "BSP"  
    ]

    # Define keywords to exclude repositories related to courses
    exclude_keywords = [
        "course", "tutorial", "learn", "training", "workshop",
        "lesson", "lecture", "class", "video course", "udemy",
        "coursera", "edx", "education", "bootcamp"
    ]

    # Initialize crawler with proper error handling for API keys
    try:
        crawler = GitHubCrawler(token=github_token)
        
        # Initialize analyzer separately if AI analysis is requested
        analyzer = None
        if analyze_with_ai:
            analyzer = RepoAnalyzer(gemini_api_key=gemini_api_key, use_ollama=use_ollama)
            print(f"Analyzer initialized: use_ollama={use_ollama}, gemini_available={getattr(analyzer, 'gemini_available', False)}, ollama_available={getattr(analyzer, 'ollama_available', False)}")
    except Exception as e:
        print(f"Error initializing crawler: {e}")
        print("Continuing without AI capabilities...")
        crawler = GitHubCrawler(token=github_token)
        analyzer = None
        analyze_with_ai = False

    # First, try searching with a broader query
    broader_queries = [
        "embedded systems",
        "firmware",
        "microcontroller",
        "STM32",
        "MSP430",
        "RTOS"
    ]

    all_repos = []

    for query in broader_queries:
        try:
            print(f"Searching for '{query}' repositories in C...")
            c_repos = crawler.search_repos(
                query,
                language="c",
                min_stars=min_stars,
                max_pages=max_pages
            )
            all_repos.extend(c_repos or [])

            print(f"Searching for '{query}' repositories in C++...")
            cpp_repos = crawler.search_repos(
                query,
                language="c++",
                min_stars=min_stars,
                max_pages=max_pages
            )
            all_repos.extend(cpp_repos or [])

            # Add assembly language search for broader coverage
            if query in ["embedded systems", "firmware"]:
                print(f"Searching for '{query}' repositories in Assembly...")
                asm_repos = crawler.search_repos(
                    query,
                    language="assembly",
                    min_stars=min_stars,
                    max_pages=max_pages
                )
                all_repos.extend(asm_repos or [])
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            print("Continuing with next query...")

    # Remove duplicates based on full_name
    unique_repos = {}
    for repo in all_repos:
        full_name = repo.get("full_name")
        if full_name not in unique_repos:
            unique_repos[full_name] = repo

    unique_repos_list = list(unique_repos.values())
    print(f"Found {len(unique_repos_list)} unique repositories before filtering")

    # Apply our custom filtering
    filtered_repos = crawler.filter_embedded_systems_repos(
        unique_repos_list,
        required_keywords,
        exclude_keywords
    )

    # Prepare output
    output_data = []
    
    # Process in batches with more pause time between repositories
    batch_size = 3  # Even smaller batch size to allow more time per repo
    for batch_start in range(0, min(len(filtered_repos), max_results), batch_size):
        batch_end = min(batch_start + batch_size, min(len(filtered_repos), max_results))
        print(f"\nProcessing batch {batch_start//batch_size + 1} ({batch_start+1}-{batch_end} of {min(len(filtered_repos), max_results)})")
        
        for idx in range(batch_start, batch_end):
            repo = filtered_repos[idx]
            repo_data = {
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "html_url": repo.get("html_url"),
                "description": repo.get("description"),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count"),
                "forks": repo.get("forks_count"),
                "last_updated": repo.get("updated_at"),
                "topics": repo.get("topics", []),
                "keyword_match_count": repo.get("keyword_match_count", 0),
                "matching_keywords": repo.get("matching_keywords", [])
            }
            
            # Analyze with AI if requested
            if analyze_with_ai:
                print(f"Analyzing repository {idx+1}/{min(len(filtered_repos), max_results)}: {repo.get('name')}")
                try:
                    # Use the unified analyze_repo method that chooses the right backend
                    ai_response = analyzer.analyze_repo(repo_data)
                    repo_data["ai_response"] = ai_response
                    ai_type = "Ollama" if use_ollama else "Gemini"
                    print(f"{ai_type} assessment: {ai_response}")
                except Exception as e:
                    # Even if analysis completely fails, provide a default yes with explanation
                    print(f"Analysis failed with error: {e}")
                    repo_data["ai_response"] = f"Yes (API error - defaulting to yes)"
                    print(f"Default assessment: {repo_data['ai_response']}")
                
                # Add a longer delay between repos to prevent overlapping responses
                time.sleep(4)  
            else:
                # Provide fallback analysis if AI is not available - default to yes as requested
                repo_data["ai_response"] = "Yes (fallback - pre-filtered repo)"
                print(f"Fallback assessment: {repo_data['ai_response']}")
            
            output_data.append(repo_data)
        
        # Save results after each batch as a backup
        try:
            # Save to JSON file
            with open(f"{output_json}.temp", 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
                
            # Rename to actual filename
            if os.path.exists(output_json):
                os.replace(f"{output_json}.temp", output_json)
            else:
                os.rename(f"{output_json}.temp", output_json)
                
            print(f"Saved progress to {output_json}")
        except Exception as e:
            print(f"Error saving progress: {e}")

    # Final save to both JSON and CSV
    try:
        # Save to JSON file
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        # Save to CSV file with github_url and topics columns
        save_csv(output_data, output_csv)

        # Print results
        print(f"\nFound {len(output_data)} embedded systems repositories matching your criteria")
        print(f"JSON results saved to {output_json}")
        print(f"CSV results saved to {output_csv}")
        print("\nTop 10 repositories by keyword matches:")
        for i, repo in enumerate(output_data[:10]):
            print(f"{i+1}. {repo['name']} ({repo['stars']} stars) - {repo['keyword_match_count']} keyword matches")
            print(f"   Matching keywords: {', '.join(repo['matching_keywords'])}")
            print(f"   {repo['html_url']}")
            print(f"   {repo['description']}")
            if "ai_response" in repo:
                print(f"   AI assessment: {repo['ai_response']}")
            print()
    except Exception as e:
        print(f"Error saving final results: {e}")
        
    return output_data