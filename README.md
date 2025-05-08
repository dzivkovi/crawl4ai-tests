# Crawl4AI for VS Code API Documentation Scraping

This project uses [Crawl4AI](https://github.com/unclecode/crawl4ai) to create a local, searchable copy of the API documentation.

## Step 1: Create a Virtual Environment

```bash
# Create a virtual environment named .venv
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate
```

## Step 2: Install Dependencies

Once your virtual environment is activated, install the required packages:

```bash
# Install required packages
pip install -r requirements.txt

# Run post-installation setup (it will install Playwright browser binaries)
crawl4ai-setup

# Optionally verify installation (may not work behind corporate firewalls)
crawl4ai-doctor
```

## Step 3: Run the Scraper

### Single Page Scraping

```bash
# Convert a single page (if using the standalone script)
python src/scrape_page_to_markdown.py
```

Single page scraper implements the idea from [@AICodeKing](https://www.youtube.com/@AICodeKing)'s video [Crawl4AI + Aider & Cline : AI Coding with WEB SCRAPING is AMAZING! (Knowledge Base & Documentation)](https://www.youtube.com/watch?v=W7V1J6EFiUs):

![idea](images/crawl4ai_scraper.jpg)

### Recursive Scraping

Way too often, we need to scrape the whole subtree. E.g. here's the script I wrote to fetch all VSCode APIs. Use it as a starting point to get your APIs converted into LLM-friendly Markdown format:

```bash
# Full VS Code API documentation crawl
python src/scrape_vscode_api_docs.py
```

After running the script, you'll find the VS Code API documentation saved as Markdown files in the `vscode_api_docs` directory with a structure that mirrors the original website.

## Troubleshooting

If you encounter browser-related issues, you can install browsers manually:

```bash
# Install only Chromium (recommended for this project)
python -m playwright install chromium

# OR for full installation with system dependencies (needed on some Linux systems)
python -m playwright install --with-deps chromium
```

## License & Attribution

This project is licensed under the Apache License 2.0 with a required attribution clause. See the [Apache 2.0 License](https://github.com/unclecode/crawl4ai/blob/main/LICENSE) file for details.

<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://img.shields.io/badge/Powered%20by-Crawl4AI-blue?style=flat-square" alt="Powered by Crawl4AI"/>
</a>
