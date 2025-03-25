class Repository:
    """
    Data model for GitHub repository information
    """
    def __init__(self, repo_data):
        """
        Initialize a Repository object from GitHub API data
        
        Args:
            repo_data (dict): Repository data from GitHub API
        """
        self.name = repo_data.get("name", "")
        self.full_name = repo_data.get("full_name", "")
        self.html_url = repo_data.get("html_url", "")
        self.description = repo_data.get("description", "")
        self.language = repo_data.get("language", "")
        self.stars = repo_data.get("stargazers_count", 0)
        self.forks = repo_data.get("forks_count", 0)
        self.last_updated = repo_data.get("updated_at", "")
        self.topics = repo_data.get("topics", [])
        self.keyword_match_count = repo_data.get("keyword_match_count", 0)
        self.matching_keywords = repo_data.get("matching_keywords", [])
        self.ai_response = repo_data.get("ai_response", "N/A")
        
    def to_dict(self):
        """
        Convert repository object to dictionary
        
        Returns:
            dict: Repository data as dictionary
        """
        return {
            "name": self.name,
            "full_name": self.full_name,
            "html_url": self.html_url,
            "description": self.description,
            "language": self.language,
            "stars": self.stars,
            "forks": self.forks,
            "last_updated": self.last_updated,
            "topics": self.topics,
            "keyword_match_count": self.keyword_match_count,
            "matching_keywords": self.matching_keywords,
            "ai_response": self.ai_response
        }