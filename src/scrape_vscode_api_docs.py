# Filename: scrape_vscode_api_docs.py
"""
Scrapes VS Code API documentation under /api using Crawl4AI.

Performs a deep crawl starting from the API root URL, filtering
links during the crawl to stay within the /api path, and saves
Markdown content to a local directory structure.
"""

import asyncio
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import List, Optional, Dict, Any # Keep needed types

# --- Dependency Check ---
try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CrawlResult
    from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
    # Import filter classes based on the documentation
    from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter
except ImportError as e:
    print(f"[ERROR] Missing required library: {e}")
    print("Please install Crawl4AI and its dependencies:")
    print("  pip install crawl4ai")
    print("Then run the setup command in your terminal:")
    print("  crawl4ai-setup")
    print("Or alternatively:")
    print("  playwright install --with-deps")
    sys.exit(1)

# --- Configuration ---
START_URL = "https://code.visualstudio.com/api"
# Pattern for URLPatternFilter to keep crawl within /api/*
# Uses wildcard (*) matching
API_URL_PATTERN = "https://code.visualstudio.com/api/*"
OUTPUT_DIR = "vscode_api_docs"
# Adjust max crawl depth as needed. Deeper means more potential pages.
MAX_DEPTH = 3
# Set to False to reduce Crawl4AI's console logging
VERBOSE_LOGGING = True
# --- End Configuration ---

def url_to_filepath(url: str, base_dir: str) -> Optional[Path]:
    """
    Converts a URL to a sanitized, structured local filepath within the base_dir.
    Assumes URL has already been filtered to be within the desired API path.
    Fix: Prevents adding .md extension if already present.
    """
    try:
        parsed_url = urlparse(url)
        # Filtering check based on path prefix is removed here,
        # relying on the crawl-time filter_chain.

        # Remove leading '/' and decode URL encoding
        path_part = unquote(parsed_url.path.lstrip('/'))
        path_part = path_part.split('#')[0] # Remove fragment

        # Sanitize path components
        safe_components = []
        for component in path_part.split('/'):
            safe_component = re.sub(r'[<>:"\\|?*\s]', '_', component)
            safe_component = re.sub(r'_+', '_', safe_component)
            safe_component = safe_component.strip('._')
            safe_component = safe_component[:100] # Limit component length
            if safe_component:
                safe_components.append(safe_component)

        # Determine filename and directory path
        # Check if path corresponds to the base API path itself (e.g., /api or /api/)
        # Need the original prefix for this check
        base_api_path_components = [c for c in urlparse(START_URL).path.strip('/').split('/') if c]
        is_base_api_path = safe_components == base_api_path_components

        # Treat base path or paths ending in '/' as index.md
        if not safe_components or parsed_url.path.endswith('/') or is_base_api_path:
            filename = "index.md"
            # Use all components for directory path if it's an index
            dir_components = safe_components
        else:
            # Otherwise, last component is filename, rest is directory path
            last_component = safe_components[-1]
            # *** FIX: Check if last component already ends with .md (case-insensitive) ***
            if last_component.lower().endswith(".md"):
                filename = last_component # Use as is
            else:
                filename = last_component + ".md" # Append .md
            # *** End Fix ***
            dir_components = safe_components[:-1]

        # Create the full path using pathlib for cross-platform compatibility
        full_dir_path = Path(base_dir).joinpath(*dir_components)
        filepath = full_dir_path / filename
        return filepath

    except Exception as e:
        # Catch potential errors during path conversion
        print(f"  [ERROR] Could not convert URL '{url}' to filepath: {e}")
        return None

async def main():
    """Main function to run the web crawler."""
    print("--- VS Code API Docs Scraper using Crawl4AI (Filtered Crawl) ---")
    print(f"Starting crawl from: {START_URL}")
    print(f"Saving Markdown files to: '{OUTPUT_DIR}/'")
    print(f"Filtering crawl to URL pattern: {API_URL_PATTERN}")
    print(f"Max crawl depth: {MAX_DEPTH}")
    print("-" * 50)

    # Ensure output directory exists
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # --- Configure Crawl-Time Filtering ---
    # Create a filter to match only URLs within the API path
    api_url_filter = URLPatternFilter(patterns=[API_URL_PATTERN])
    # Create a filter chain containing the URL filter
    filter_chain = FilterChain([api_url_filter])
    # --- End Filter Configuration ---

    # Configure the deep crawl strategy using the filter_chain
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=MAX_DEPTH,
            filter_chain=filter_chain, # Apply the filter during crawl
            include_external=False
        ),
        verbose=VERBOSE_LOGGING
    )

    scraped_count = 0
    results: List[CrawlResult] = []

    try:
        async with AsyncWebCrawler() as crawler:
            print("Crawler initialized. Starting filtered crawl...")
            # This should now only crawl URLs matching the filter_chain
            results = await crawler.arun(START_URL, config=config)
    # Catch specific TypeErrors that might still occur if filter_chain isn't supported
    except TypeError as e:
         print(f"\n[ERROR] TypeError during crawler configuration: {e}")
         print("This might indicate the 'filter_chain' parameter is not supported "
               "in your crawl4ai version for BFSDeepCrawlStrategy.")
         print("Consider updating crawl4ai (`pip install -U crawl4ai`) or "
               "reverting to a script version that used post-crawl filtering.")
         return
    except Exception as e: # Catch other broad exceptions during crawl
        print(f"\n[ERROR] An critical error occurred during crawling: {e}")
        if not results:
            print("No results obtained.")
            return # Exit if crawl failed early

    print("\n--- Crawl Finished ---")
    print(f"Attempted to process {len(results)} pages matching the filter and depth limits.")
    print("Processing results and saving Markdown files...")

    # Process results and save relevant files
    for result in results:
        # Double-check success and markdown content
        if result.success and result.markdown:
            # url_to_filepath no longer needs the primary filter check
            filepath = url_to_filepath(result.url, OUTPUT_DIR)
            if filepath: # Proceed only if path conversion was successful
                try:
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    filepath.write_text(result.markdown, encoding='utf-8', errors='replace')
                    print(f"  [SAVED] {result.url} -> {filepath}")
                    scraped_count += 1
                except OSError as e: # Catch file system errors specifically
                    print(f"  [ERROR] Could not save file {filepath}: {e}")
                except Exception as e: # Catch other unexpected errors during file save
                    print(f"  [ERROR] Unexpected error processing {result.url}: {e}")
        elif not result.success:
             # Log failed pages (these should now only be pages within the /api path)
             print(f"  [FAILED] {result.url} (Status: {result.status_code}, Error: {result.error})")

    print("-" * 50)
    print(f"Successfully saved {scraped_count} Markdown files matching "
          f"'{API_URL_PATTERN}' path to '{OUTPUT_DIR}'.")
    print("\n--- Usage with Aider ---")
    print(f"Use '/read {OUTPUT_DIR}/<path/to/your/file.md>' to add specific docs.")
    print("-" * 50)


# Standard Python entry point check
if __name__ == "__main__":
    # It's recommended to run `crawl4ai-setup` or `playwright install --with-deps`
    # once manually in your terminal before running this script for the first time.
    asyncio.run(main())
