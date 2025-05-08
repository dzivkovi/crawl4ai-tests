# Filename: scrape_folder_to_markdown.py
"""
A generic web crawler that scrapes a website and saves its content as Markdown files.

Features:
- Performs a deep crawl starting from a specified URL
- Automatically filters links to stay within the same domain/path
- Saves Markdown content to a local directory structure
- Configurable crawl depth and verbosity
"""

import asyncio
import re
import sys
import argparse
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import List, Optional

# --- Dependency Check ---
try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CrawlResult
    from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
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

def create_url_pattern_from_start_url(start_url: str) -> str:
    """
    Create a wildcard URL pattern from a starting URL to limit crawling to the same domain/path.
    """
    parsed = urlparse(start_url)
    # Extract base domain and path
    base = f"{parsed.scheme}://{parsed.netloc}"

    # If there's a specific path, make it the base of our pattern
    if parsed.path and parsed.path != '/':
        # Remove trailing slash if present
        path_base = parsed.path.rstrip('/')
        # Create pattern with wildcard for anything under this path
        pattern = f"{base}{path_base}/*"
    else:
        # If no specific path, match anything on the domain
        pattern = f"{base}/*"

    return pattern


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Crawl a website and convert its pages to Markdown files",
        epilog="Example: python scrape_folder_to_markdown.py https://code.visualstudio.com/api vscode_docs"
    )

    parser.add_argument(
        "url", 
        help="Starting URL to crawl (e.g., https://code.visualstudio.com/api)"
    )

    parser.add_argument(
        "output_dir", 
        help="Directory to save Markdown files (e.g., vscode_docs)"
    )

    parser.add_argument(
        "-d", "--depth", 
        type=int,
        default=3,
        help="Maximum crawl depth (default: 3, recommended max: 5)"
    )

    parser.add_argument(
        "-q", "--quiet", 
        action="store_true",
        help="Reduce console logging for quieter operation"
    )

    return parser.parse_args()


def url_to_filepath(url: str, base_dir: str, start_url: str) -> Optional[Path]:
    """
    Converts a URL to a sanitized, structured local filepath within the base_dir.
    Creates a flat folder structure with related pages in the same directory.
    """
    try:
        parsed_url = urlparse(url)
        parsed_start = urlparse(start_url)

        # Remove leading '/' and decode URL encoding
        path_part = unquote(parsed_url.path.lstrip('/'))
        path_part = path_part.split('#')[0]  # Remove fragment

        # Sanitize path components
        safe_components = []
        for component in path_part.split('/'):
            safe_component = re.sub(r'[<>:"\\|?*\s]', '_', component)
            safe_component = re.sub(r'_+', '_', safe_component)
            safe_component = safe_component.strip('._')
            safe_component = safe_component[:100]  # Limit component length
            if safe_component:
                safe_components.append(safe_component)

        # Extract the path components from the start URL for comparison
        start_path = parsed_start.path.strip('/')
        start_components = [c for c in start_path.split('/') if c]

        # Check if this is the start URL itself
        if url == start_url or (len(safe_components) <= len(start_components) and
                               all(a == b for a, b in zip(safe_components, start_components))):
            # This is the start URL or a parent of it - save as index.md in root
            return Path(base_dir) / "index.md"

        # Determine which components to use for directory and filename
        # Skip components that are part of the start_url
        remaining_components = safe_components[len(start_components):]

        if not remaining_components:
            # If nothing remains after removing start components, use index.md
            return Path(base_dir) / "index.md"

        # For pages directly under the start URL with no further path components
        if len(remaining_components) == 1:
            if parsed_url.path.endswith('/'):
                # It's a directory-like page - save as index.md in a subfolder
                folder_name = remaining_components[0]
                return Path(base_dir) / folder_name / "index.md"
            else:
                # It's a page - save as {name}.md in the base directory
                filename = remaining_components[0]
                if not filename.lower().endswith(".md"):
                    filename += ".md"
                return Path(base_dir) / filename

        # For nested paths, use the first component after start_url as the directory
        # and the last component as the filename
        section_dir = remaining_components[0]

        # If the URL ends with /, use the last path component as the filename
        if parsed_url.path.endswith('/'):
            filename = remaining_components[-1]
        else:
            filename = remaining_components[-1]

        if not filename.lower().endswith(".md"):
            filename += ".md"

        # Create path using section directory and filename
        return Path(base_dir) / section_dir / filename

    except Exception as e:  # pylint: disable=broad-except
        # Catch potential errors during path conversion
        print(f"  [ERROR] Could not convert URL '{url}' to filepath: {e}")
        return None


async def main():
    """Main function to run the web crawler."""
    args = parse_arguments()

    # Set up configuration from arguments
    # pylint: disable=invalid-name
    START_URL = args.url
    OUTPUT_DIR = args.output_dir
    MAX_DEPTH = args.depth
    VERBOSE_LOGGING = not args.quiet

    # Generate the URL pattern from the start URL
    API_URL_PATTERN = create_url_pattern_from_start_url(START_URL)

    print("--- Web Scraper using Crawl4AI (Filtered Crawl) ---")
    print(f"Starting crawl from: {START_URL}")
    print(f"Saving Markdown files to: '{OUTPUT_DIR}/'")
    print(f"Filtering crawl to URL pattern: {API_URL_PATTERN}")
    print(f"Max crawl depth: {MAX_DEPTH}")
    print("-" * 50)

    # Ensure output directory exists and is writable
    output_path = Path(OUTPUT_DIR)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        # Test if directory is writable by creating and removing a test file
        test_file = output_path / ".write_test"
        test_file.touch()
        test_file.unlink()
    except PermissionError:
        print(f"[ERROR] Output directory '{OUTPUT_DIR}' is not writable. Please check permissions.")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-except
        print(f"[ERROR] Failed to create or access output directory '{OUTPUT_DIR}': {e}")
        sys.exit(1)

    # --- Configure Crawl-Time Filtering ---
    # Create a filter to match only URLs within the specified path
    api_url_filter = URLPatternFilter(patterns=[API_URL_PATTERN])
    # Create a filter chain containing the URL filter
    filter_chain = FilterChain([api_url_filter])
    # --- End Filter Configuration ---

    # Configure the deep crawl strategy using the filter_chain
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=MAX_DEPTH,
            filter_chain=filter_chain,  # Apply the filter during crawl
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
    except Exception as e:  # pylint: disable=broad-except
        print(f"\n[ERROR] A critical error occurred during crawling: {e}")
        if not results:
            print("No results obtained.")
            return  # Exit if crawl failed early

    print("\n--- Crawl Finished ---")
    print(f"Attempted to process {len(results)} pages matching the filter and depth limits.")
    print("Processing results and saving Markdown files...")

    # Process results and save relevant files
    for result in results:
        # Double-check success and markdown content
        if result.success and result.markdown:
            # Convert URL to filepath
            filepath = url_to_filepath(result.url, OUTPUT_DIR, START_URL)
            if filepath:  # Proceed only if path conversion was successful
                try:
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    filepath.write_text(result.markdown, encoding='utf-8', errors='replace')
                    print(f"  [SAVED] {result.url} -> {filepath}")
                    scraped_count += 1
                except OSError as e:  # Catch file system errors specifically
                    print(f"  [ERROR] Could not save file {filepath}: {e}")
                except Exception as e:  # pylint: disable=broad-except
                    print(f"  [ERROR] Unexpected error processing {result.url}: {e}")
        elif not result.success:
            # Log failed pages
            print(f"  [FAILED] {result.url} (Status: {result.status_code}, Error: {result.error})")

    print("-" * 50)
    print(f"Successfully saved {scraped_count} Markdown files matching "
          f"'{API_URL_PATTERN}' path to '{OUTPUT_DIR}'.")
    print("\n--- Usage with LLMs or AI Tools ---")
    print(f"The Markdown files in '{OUTPUT_DIR}' can now be used with tools like Aider, Claude, or other LLMs.")
    print("-" * 50)


# Standard Python entry point check
if __name__ == "__main__":
    # It's recommended to run `crawl4ai-setup` or `playwright install --with-deps`
    # once manually in your terminal before running this script for the first time.
    asyncio.run(main())
