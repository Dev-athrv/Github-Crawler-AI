# GitHub Repository Crawler

A modular tool to crawl GitHub repositories and analyze them using AI models (Ollama or Gemini).

## Structure

```
github-crawler/
├── github_crawler/
│   ├── __init__.py
│   ├── crawler.py
│   ├── analyzer.py
│   ├── utils.py
│   └── models.py
├── scripts/
│   ├── run_with_gemini.py
│   └── run_with_ollama.py
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/github-crawler.git
   cd github-crawler
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your API keys:
   - For GitHub (optional, but recommended to avoid rate limits)
   - For Gemini (required if using Gemini mode)

## Usage

### Using with Ollama

```bash
# Basic usage
python scripts/run_with_ollama.py

# With parameters
python scripts/run_with_ollama.py --github-token YOUR_TOKEN --min-stars 100 --max-results 200 --analyze
```

### Using with Gemini

```bash
# Set your Gemini API key as an environment variable
export GEMINI_API_KEY=your_api_key

# Basic usage
python scripts/run_with_gemini.py

# With parameters
python scripts/run_with_gemini.py --github-token YOUR_TOKEN --min-stars 100 --max-results 200 --analyze
```

### Command Line Arguments

Both scripts support the following arguments:

- `--github-token`: Your GitHub token for higher rate limits
- `--min-stars`: Minimum number of stars for repositories (default: 10)
- `--max-results`: Maximum number of repositories to collect (default: 100)
- `--max-pages`: Maximum number of pages to crawl (default: 5)
- `--output-json`: Path to output JSON file
- `--output-csv`: Path to output CSV file
- `--analyze`: Flag to enable AI analysis of repositories

Additionally, the Gemini script requires:
- `--gemini-api-key`: Your Gemini API key (can also be set via GEMINI_API_KEY environment variable)

## Output

The crawler produces two output files:
- JSON file with detailed repository information
- CSV file with structured repository data

## License

[Your license information here]