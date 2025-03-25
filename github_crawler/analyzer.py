import requests
import time

# Keep the Google Gemini import for backward compatibility
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Google Generative AI package not installed. Gemini functionality will be disabled.")

class RepoAnalyzer:
    def __init__(self, gemini_api_key="", use_ollama=False, ollama_model="codellama:7b"):
        """
        Initialize the repository analyzer.

        Args:
            gemini_api_key (str, optional): Google Gemini API key
            use_ollama (bool, optional): Whether to use Ollama instead of Gemini
            ollama_model (str, optional): Ollama model to use
        """
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        
        # Initialize Gemini model if API key is provided and not using Ollama
        self.gemini_available = False
        if gemini_api_key and not use_ollama and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=gemini_api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                self.gemini_available = True
                print("Gemini model initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Gemini model: {e}")
        
        # Initialize Ollama availability if specified
        self.ollama_available = False
        if use_ollama:
            try:
                # Test if Ollama is available by making a simple request
                response = requests.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    self.ollama_available = True
                    print(f"Ollama service initialized successfully, using {self.ollama_model} model")
                else:
                    print(f"Ollama service is not available. Status code: {response.status_code}")
            except Exception as e:
                print(f"Failed to connect to Ollama service: {e}")

    def analyze_repo(self, repo):
        """
        Analyze a repository using either Gemini or Ollama based on configuration.
        
        Args:
            repo (dict): Repository information
            
        Returns:
            str: "Yes" if suitable, "No" if not, with a brief explanation
        """
        if self.use_ollama and self.ollama_available:
            return self.analyze_repo_with_ollama(repo)
        elif self.gemini_available:
            return self.analyze_repo_with_gemini(repo)
        else:
            # Fallback when no AI service is available
            matches = repo.get('keyword_match_count', 0)
            if matches >= 2:
                return "Yes (fallback - multiple keywords matched)"
            return "Yes (fallback - pre-filtered repo)"

    def analyze_repo_with_gemini(self, repo):
        """
        Analyze a repository using Gemini to determine if it's suitable for training
        a model for embedded systems.
        
        Args:
            repo (dict): Repository information
            
        Returns:
            str: "Yes" if suitable, "No" if not, with a brief explanation
        """
        if not self.gemini_available:
            return "N/A (Gemini API not configured)"
            
        try:
            # Build a more structured prompt for the model with clear criteria based on user feedback
            prompt = f"""
            Analyze if this GitHub repository is suitable for training a model to generate test cases and 
            CMake files for embedded systems projects. ONLY answer with "Yes" or "No" followed by a very brief reason.
            
            Repository details:
            - Name: {repo.get('name')}
            - Full Name: {repo.get('full_name')}
            - Description: {repo.get('description', 'No description')}
            - Language: {repo.get('language', 'Unknown')}
            - Stars: {repo.get('stargazers_count', 0)}
            - Topics: {', '.join(repo.get('topics', []))}
            - Matching Keywords: {', '.join(repo.get('matching_keywords', []))}
            
            Criteria for YES:
            1. Contains embedded systems code (not just documentation)
            2. Has .c, .cpp, .h, or .hpp files that demonstrate embedded systems functionality
            3. Has test files or examples showing usage patterns
            4. Focuses on hardware interaction, firmware, or low-level code
            
            Criteria for NO:
            1. Very minimal code samples (only a few files with minimal content)
            2. Pure documentation repositories with no actual code
            
            Note this repository was pre-filtered for embedded systems relevance, so most should be suitable.
            """
            
            # Add a retry mechanism without timeout
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Get response from Gemini without a timeout parameter
                    response = self.model.generate_content(prompt)
                    
                    # Extract the answer - look for "Yes" or "No"
                    answer_text = response.text.strip()
                    if "yes" in answer_text.lower()[:10]:
                        return "Yes - " + answer_text.split("Yes", 1)[1].strip()[:100]
                    elif "no" in answer_text.lower()[:10]:
                        return "No - " + answer_text.split("No", 1)[1].strip()[:100]
                    else:
                        # For non-compliant responses, try to extract a Yes/No anyway
                        if "suitable" in answer_text.lower() and "not" not in answer_text.lower()[:30]:
                            return "Yes - " + answer_text[:100]
                        elif "not suitable" in answer_text.lower() or "unsuitable" in answer_text.lower():
                            return "No - " + answer_text[:100]
                        else:
                            # Last resort fallback using keyword matching
                            if repo.get('keyword_match_count', 0) >= 2:
                                return "Yes - Based on keywords and pre-filtering"
                            else:
                                return "No - Insufficient evidence in repo content"
                                
                except Exception as e:
                    print(f"Attempt {attempt+1} failed. Retrying...")
                    if attempt < max_retries - 1:
                        time.sleep(3)  # Wait before retry
                    else:
                        raise e
                    
        except Exception as e:
            print(f"Error analyzing repo with Gemini: {e}")
            
            # Fallback logic when API fails completely - more lenient based on user feedback
            matches = repo.get('keyword_match_count', 0)
            language = repo.get('language', '').lower()
            
            # Simple heuristic when API fails - more permissive as requested
            if matches >= 1 and language in ['c', 'c++', 'assembly']:
                return "Yes (fallback - embedded systems repo by keywords)"
            elif matches >= 2:  # Even without specific language, if keywords match well
                return "Yes (fallback - multiple keywords matched)"
            
            return "Yes (fallback - pre-filtered repo)"  # Default to Yes as requested
            
    def analyze_repo_with_ollama(self, repo):
        """
        Analyze a repository using Ollama's LLM to determine if it's suitable for training
        a model for embedded systems.
        
        Args:
            repo (dict): Repository information
            
        Returns:
            str: "Yes" if suitable, "No" if not, with a brief explanation
        """
        if not self.ollama_available:
            return "N/A (Ollama service not available)"
            
        try:
            # Build an improved prompt that emphasizes the importance of actual code files
            # and makes the default judgment more lenient toward "Yes"
            prompt = f"""
            You are tasked with analyzing GitHub repositories for embedded systems code suitability. 
            Your goal is to determine if this repository contains useful embedded systems code that can be used 
            for training a model to generate test cases and CMake files.
            
            Repository details:
            - Name: {repo.get('name')}
            - Full Name: {repo.get('full_name')}
            - Description: {repo.get('description', 'No description')}
            - Language: {repo.get('language', 'Unknown')}
            - Stars: {repo.get('stargazers_count', 0)}
            - Topics: {', '.join(repo.get('topics', []))}
            - Matching Keywords: {', '.join(repo.get('matching_keywords', []))}
            
            IMPORTANT GUIDELINES:
            1. This repository has already been pre-filtered to match embedded systems keywords.
            2. If the repository has been filtered to match multiple embedded keywords, it is HIGHLY LIKELY to be suitable.
            3. If the repository contains C, C++, or Assembly language files, it is LIKELY to be suitable for embedded systems.
            4. ANY repository with embedded systems code, firmware, or low-level hardware interaction code IS SUITABLE.
            5. The PRESENCE OF .c, .cpp, .h, or .hpp FILES strongly indicates this is a SUITABLE repository.
            
            ANSWER FORMAT:
            - Start with EXACTLY "Yes -" or "No -" followed by a brief explanation
            - Keep your explanation concise and strictly focused on the repository's suitability
            - Your entire response should not exceed 100 characters
            
            DEFAULT BIAS:
            - When in doubt, answer "Yes" since the repository has already been pre-filtered
            - Only answer "No" if you are CERTAIN the repository has NO actual code or is completely unrelated to embedded systems
            
            Give your assessment now:
            """
            
            # Add a retry mechanism with better error handling
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Make request to Ollama API with a longer timeout
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": self.ollama_model,
                            "prompt": prompt,
                            "stream": False,
                            "max_tokens": 200  # Limit token generation to keep responses concise
                        },
                        timeout=180  # Increase timeout to give more processing time
                    )
                    
                    if response.status_code == 200:
                        response_json = response.json()
                        answer_text = response_json.get("response", "").strip()
                        
                        # Improved parsing to extract the Yes/No and explanation
                        if answer_text.lower().startswith("yes"):
                            # Extract just the explanation part after "Yes -"
                            explanation = answer_text.split("Yes -", 1)[1].strip() if "Yes -" in answer_text else answer_text.split("Yes", 1)[1].strip()
                            # Ensure explanation doesn't get cut off
                            return f"Yes - {explanation[:95]}"
                        elif answer_text.lower().startswith("no"):
                            # Extract just the explanation part after "No -"
                            explanation = answer_text.split("No -", 1)[1].strip() if "No -" in answer_text else answer_text.split("No", 1)[1].strip()
                            
                            # Double-check if we should override a "No" response
                            language = repo.get('language', '').lower()
                            keyword_count = repo.get('keyword_match_count', 0)
                            
                            # Override conditions - be more permissive
                            if language in ['c', 'c++', 'assembly'] and keyword_count >= 1:
                                return f"Yes - Contains {language} code and matches embedded keywords"
                            elif keyword_count >= 2:
                                return f"Yes - Matches multiple embedded keywords ({keyword_count})"
                            else:
                                return f"No - {explanation[:95]}"
                        else:
                            # For non-compliant responses that don't start with Yes/No
                            if "suitable" in answer_text.lower() and "not" not in answer_text.lower()[:30]:
                                return f"Yes - {answer_text[:95]}"
                            elif "not suitable" in answer_text.lower() or "unsuitable" in answer_text.lower():
                                # Still double-check override conditions
                                language = repo.get('language', '').lower()
                                keyword_count = repo.get('keyword_match_count', 0)
                                
                                if language in ['c', 'c++', 'assembly'] and keyword_count >= 1:
                                    return f"Yes - Contains {language} code and matches embedded keywords"
                                elif keyword_count >= 2:
                                    return f"Yes - Matches multiple embedded keywords ({keyword_count})"
                                else:
                                    return f"No - {answer_text[:95]}"
                            else:
                                # Default to Yes for ambiguous responses
                                return f"Yes - Repository appears relevant to embedded systems"
                    else:
                        print(f"Ollama API returned status code {response.status_code}")
                        if attempt < max_retries - 1:
                            time.sleep(3)  # Wait before retry
                        else:
                            print(f"Failed after {max_retries} attempts")
                                
                except Exception as e:
                    print(f"Attempt {attempt+1} failed with error: {e}. Retrying...")
                    if attempt < max_retries - 1:
                        time.sleep(3)  # Wait before retry
                    else:
                        raise e
                    
        except Exception as e:
            print(f"Error analyzing repo with Ollama: {e}")
            
            # More permissive fallback logic when API fails completely
            matches = repo.get('keyword_match_count', 0)
            language = repo.get('language', '').lower()
            
            # More lenient heuristic when API fails - almost always say Yes
            if language in ['c', 'c++', 'assembly']:
                return f"Yes (fallback - contains {language} code for embedded systems)"
            elif matches >= 1:  # Even with just one keyword match
                return f"Yes (fallback - matches {matches} embedded keywords)"
            
            return "Yes (fallback - pre-filtered repo)"