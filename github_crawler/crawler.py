import requests
import time
from .models import Repository

class GitHubCrawler:
    def __init__(self, token=None):
        """
        Initialize the GitHub crawler.

        Args:
            token (str, optional): GitHub API token for higher rate limits
        """
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
        self.rate_limit_remaining = 0
        self.rate_limit_reset = 0

    def search_repos(self, query, language=None, sort="stars", order="desc", min_stars=10, max_pages=5):
        """
        Search for repositories matching the query.

        Args:
            query (str): Search query
            language (str, optional): Filter by programming language
            sort (str, optional): Sort results by ('stars', 'forks', 'updated')
            order (str, optional): Sort order ('desc' or 'asc')
            min_stars (int, optional): Minimum number of stars
            max_pages (int, optional): Maximum number of pages to fetch

        Returns:
            list: List of repository information
        """
        search_query = f"{query} stars:>={min_stars}"
        if language:
            search_query += f" language:{language}"

        url = f"{self.base_url}/search/repositories"
        params = {
            "q": search_query,
            "sort": sort,
            "order": order,
            "per_page": 100
        }

        all_repos = []
        page = 1

        while page <= max_pages:
            params["page"] = page
            response = self._make_request(url, params=params)

            if not response or "items" not in response:
                break

            if len(response["items"]) == 0:
                break

            all_repos.extend(response["items"])
            page += 1

            # Check if we reached the last page
            if len(response["items"]) < 100:
                break

        return all_repos
    
    # def analyze_repo(self, repo_data):
    #     """
    #     Use the associated analyzer to analyze a repository.
        
    #     Args:
    #         repo_data (dict): Repository data dictionary
            
    #     Returns:
    #         str: AI analysis response
    #     """
    #     print(f"analyze_repo called, has analyzer: {hasattr(self, 'analyzer')}")
    #     if hasattr(self, 'analyzer') and self.analyzer is not None:
    #         try:
    #             print("Calling analyzer.analyze_repo")
    #             result = self.analyzer.analyze_repo(repo_data)
    #             print(f"Analyzer result: {result}")
    #             return result
    #         except Exception as e:
    #             print(f"Error in analyzer.analyze_repo: {e}")
    #             # Fall through to fallback
    #     else:
    #         print("No analyzer available, using fallback")
        
    #     # Fallback when no analyzer is available or on error
    #     matches = repo_data.get('keyword_match_count', 0)
    #     if matches >= 2:
    #         return "Yes (fallback - multiple keywords matched)"
    #     return "Yes (fallback - pre-filtered repo)"

    def filter_embedded_systems_repos(self, repos, required_keywords, exclude_keywords):
        """
        Filter repositories to only include those related to specific embedded systems keywords
        and exclude those related to courses.

        Args:
            repos (list): List of repository information
            required_keywords (list): List of keywords to look for
            exclude_keywords (list): List of keywords to exclude

        Returns:
            list: Filtered list of repositories with keyword match count
        """
        filtered_repos = []

        for repo in repos:
            # Check if any exclude keyword appears in name, description, or topics
            should_exclude = False

            name = repo.get("name", "").lower()
            description = repo.get("description", "").lower() if repo.get("description") else ""
            topics = [t.lower() for t in repo.get("topics", [])]

            # Combine all text fields for searching
            all_text = f"{name} {description} {' '.join(topics)}"

            # Check for exclusion keywords
            for keyword in exclude_keywords:
                if keyword.lower() in all_text:
                    should_exclude = True
                    break

            if should_exclude:
                continue

            # Count matches for required keywords
            match_count = 0
            matches = []

            for keyword in required_keywords:
                keyword_lower = keyword.lower()
                if (keyword_lower in name or
                    keyword_lower in description or
                    keyword_lower in topics):
                    match_count += 1
                    matches.append(keyword)

            # Only include if at least one keyword matches
            if match_count > 0:
                repo_copy = repo.copy()
                repo_copy["keyword_match_count"] = match_count
                repo_copy["matching_keywords"] = matches
                filtered_repos.append(repo_copy)

        # Sort by number of keyword matches (highest first)
        filtered_repos.sort(key=lambda x: x["keyword_match_count"], reverse=True)
        return filtered_repos

    def _make_request(self, url, params=None):
        """
        Make a request to the GitHub API with rate limit handling.

        Args:
            url (str): API endpoint URL
            params (dict, optional): Query parameters

        Returns:
            dict: Response JSON or None on error
        """
        # Check if we need to wait for rate limit reset
        if self.rate_limit_remaining <= 1 and self.rate_limit_reset > 0:
            wait_time = self.rate_limit_reset - time.time()
            if wait_time > 0:
                print(f"Rate limit reached. Waiting for {wait_time:.0f} seconds...")
                time.sleep(wait_time + 1)  # Add a buffer second

        try:
            response = requests.get(url, headers=self.headers, params=params)

            # Update rate limit info
            self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            reset_time = response.headers.get("X-RateLimit-Reset")
            if reset_time:
                self.rate_limit_reset = int(reset_time)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403 and "rate limit" in response.text.lower():
                print("Rate limit exceeded.")
                return None
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return None

        except Exception as e:
            print(f"Request error: {e}")
            return None