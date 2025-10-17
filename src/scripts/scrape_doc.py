# scrape_readthedocs.py
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import os
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time

class ReadTheDocscraper:
    def __init__(self, output_dir="data/documents"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ReadTheDocsScraper/1.0)'
        })

    def scrape_page(self, url, delay=1):
        """Scrape a single ReadTheDocs page and save as clean markdown"""
        
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract page title
            title = self._extract_title(soup, url)
            
            # Extract main content
            content = self._extract_content(soup)
            
            if not content:
                print(f"✗ No content found for {url}")
                return None
            
            # Clean and convert to markdown
            clean_content = self._clean_content(content)
            markdown_content = self._to_markdown(clean_content)
            
            # Save to file
            filename = self._generate_filename(url, title)
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(f"Source: {url}\n\n")
                f.write(markdown_content)
            
            print(f"✓ Saved: {filepath}")
            
            # Be polite to the server
            time.sleep(delay)
            return filepath
            
        except Exception as e:
            print(f"✗ Error scraping {url}: {e}")
            return None

    def _extract_title(self, soup, url):
        """Extract page title"""
        # Try multiple title sources
        title_candidates = [
            soup.find('h1'),
            soup.find('title'),
            soup.find('meta', {'property': 'og:title'}),
        ]
        
        for candidate in title_candidates:
            if candidate:
                if candidate.name == 'meta':
                    title = candidate.get('content', '')
                else:
                    title = candidate.get_text(strip=True)
                
                if title and len(title) > 3:
                    return self._clean_title(title)
        
        # Fallback: use URL path
        return urlparse(url).path.strip('/').replace('/', '_') or 'index'

    def _extract_content(self, soup):
        """Extract main content from ReadTheDocs page"""
        # Try ReadTheDocs-specific selectors (in order of preference)
        content_selectors = [
            'div.rst-content',           # Most ReadTheDocs sites
            'div.document',              # Sphinx default
            'div.body',                  # Alternative Sphinx
            'main',                      # HTML5 semantic
            'article',                   # Alternative semantic
            'div.content',               # Generic content class
            'div#main-content',          # Alternative main content
        ]
        
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                return content
        
        # Last resort: try to find the largest text container
        all_divs = soup.find_all('div')
        if all_divs:
            # Find div with most text content
            return max(all_divs, key=lambda div: len(div.get_text(strip=True)))
        
        return soup

    def _clean_content(self, content):
        """Remove navigation and irrelevant elements"""
        # Elements to remove completely
        remove_selectors = [
            'nav', 'footer', 'header', 'aside',
            '.navigation', '.nav', '.sidebar', '.toctree-wrapper',
            '.breadcrumb', '.breadcrumbs', '.edit-on-github',
            '.version-selector', '.search-box', '.social-links',
            '.prev-next-buttons', '.page-nav', '.site-footer',
            'script', 'style', 'noscript',
            '.admonition-title',  # Keep admonition content but remove title
        ]
        
        for selector in remove_selectors:
            for element in content.select(selector):
                element.decompose()
        
        # Remove common ReadTheDocs navigation text patterns
        navigation_patterns = [
            r'Edit on GitHub',
            r'Previous\s*Next',
            r'© Copyright.*',
            r'Built with.*Sphinx',
            r'Hosted on.*Read the Docs',
        ]
        
        text = content.get_text()
        for pattern in navigation_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return BeautifulSoup(text, 'html.parser')

    def _to_markdown(self, content):
        """Convert cleaned content to markdown"""
        # Convert HTML to markdown
        markdown = md(str(content), heading_style="ATX")
        
        # Clean up markdown
        lines = markdown.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines at start, but preserve structure later
            if line or cleaned_lines:
                cleaned_lines.append(line)
        
        # Remove excessive newlines
        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)  # Max 2 consecutive newlines
        
        return result.strip()

    def _clean_title(self, title):
        """Clean title for use as filename"""
        # Remove site suffixes
        title = re.sub(r'\s*—.*$', '', title)  # Remove " — Site Name"
        title = re.sub(r'\s*\|.*$', '', title)  # Remove " | Site Name"
        return title.strip()

    def _generate_filename(self, url, title):
        """Generate clean filename"""
        # Use title if it's reasonable, otherwise use URL path
        if len(title) < 60 and re.match(r'^[\w\s\-\.]+$', title):
            filename = re.sub(r'[^\w\s\-\.]', '', title)
            filename = re.sub(r'\s+', '_', filename)
        else:
            parsed = urlparse(url)
            filename = parsed.path.strip('/').replace('/', '_') or 'index'
        
        return f"{filename}.md"

    def scrape_multiple(self, urls, delay=1):
        """Scrape multiple URLs"""
        results = []
        for url in urls:
            result = self.scrape_page(url, delay)
            results.append(result)
        
        successful = [r for r in results if r is not None]
        print(f"\n📚 Scraping complete: {len(successful)}/{len(urls)} pages saved")
        return results

# Usage example
if __name__ == "__main__":
    # Initialize scraper
    scraper = ReadTheDocscraper(output_dir="/home/gpeng/projects/rag-chatbot/data/documents")
    
    # URLs to scrape
    urls = [
        "https://oicr-gsi.readthedocs.io/en/latest/informatics-pipelines/informatics-pipelines.html",
        "https://oicr-gsi.readthedocs.io/en/latest/informatics-pipelines/assays.html",
        "https://oicr-gsi.readthedocs.io/en/latest/data-review-reporting/data-review-and-reporting.html",
        "https://oicr-gsi.readthedocs.io/en/latest/infrastructure.html"
    ]
    
    # Scrape all pages
    scraper.scrape_multiple(urls, delay=1)