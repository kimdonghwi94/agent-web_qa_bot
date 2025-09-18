"""
Web Analyzer Skill - URL to Markdown conversion functionality
Adapted from web-analyzer-mcp project
"""

import re
import time
from typing import Optional, Dict, Any, List, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup, Comment, Tag
from difflib import get_close_matches


# Tag scoring system for content importance
TAG_SCORES = {
    'h1': 3.0, 'h2': 2.5, 'h3': 2.0, 'h4': 1.5,
    'p': 1.5, 'li': 1.2, 'ul': 1.0, 'ol': 1.0,
    'table': 2.0, 'thead': 0.5, 'tbody': 0.5,
    'tr': 0.3, 'td': 0.2, 'th': 0.3,
    'img': 1.5, 'figure': 1.5, 'figcaption': 1.2,
    'blockquote': 1.0, 'code': 1.0, 'pre': 1.0,
    'strong': 0.5, 'em': 0.5, 'a': 0.0,
    'span': 0.3, 'div': 0.5,
}

# Container scoring for parent elements
CONTAINER_SCORES = {
    'main': 3,
    'article': 2,
    'section': 2,
    'body': 1,
    'div': 0.5,
}


def validate_url(url: str) -> bool:
    """Validate if the given string is a valid URL."""
    url_regex = re.compile(
        r"^(https?:\/\/)?"
        r"(www\.)?"
        r"([a-zA-Z0-9.-]+)"
        r"(\.[a-zA-Z]{2,})?"
        r"(:\d+)?"
        r"(\/[^\s]*)?$",
        re.IGNORECASE,
    )
    return bool(url_regex.match(url))


def ensure_url_scheme(url: str) -> str:
    """Ensure URL has a proper scheme (http/https)."""
    if not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url


def extract_html_content(url: str) -> str:
    """Extract HTML content from URL using Selenium."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        driver.get(url)

        # Wait for dynamic content
        time.sleep(2)

        html_content = driver.page_source
        return html_content

    except Exception as e:
        raise Exception(f"Failed to extract content from {url}: {str(e)}")
    finally:
        if driver:
            driver.quit()


def parse_special_elements(soup: BeautifulSoup) -> Dict[str, List[str]]:
    """Parse special elements like images, links, and code blocks."""
    special_elements = {
        'images': [],
        'links': [],
        'code_blocks': []
    }

    # Extract images
    for img in soup.find_all('img'):
        src = img.get('src', '')
        alt = img.get('alt', '')
        if src:
            special_elements['images'].append(f"![{alt}]({src})")

    # Extract important links
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        text = link.get_text(strip=True)
        if href and text and len(text) > 3:
            special_elements['links'].append(f"[{text}]({href})")

    # Extract code blocks
    for code in soup.find_all(['code', 'pre']):
        code_text = code.get_text(strip=True)
        if code_text and len(code_text) > 10:
            special_elements['code_blocks'].append(f"```\n{code_text}\n```")

    return special_elements


def clean_html_content(soup: BeautifulSoup) -> BeautifulSoup:
    """Clean HTML content by removing unwanted elements."""
    # Remove unwanted tags
    unwanted_tags = [
        'script', 'style', 'meta', 'link', 'noscript',
        'iframe', 'embed', 'object', 'form', 'input',
        'button', 'select', 'textarea', 'nav', 'footer',
        'header', 'aside', 'advertisement'
    ]

    for tag_name in unwanted_tags:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove elements with unwanted classes/ids
    unwanted_patterns = [
        'advertisement', 'ads', 'popup', 'modal', 'cookie',
        'newsletter', 'subscribe', 'social', 'share',
        'related', 'sidebar', 'menu', 'navigation'
    ]

    for pattern in unwanted_patterns:
        for element in soup.find_all(attrs={'class': re.compile(pattern, re.I)}):
            element.decompose()
        for element in soup.find_all(attrs={'id': re.compile(pattern, re.I)}):
            element.decompose()

    return soup


def calculate_element_score(element: Tag) -> float:
    """Calculate importance score for an HTML element."""
    if not isinstance(element, Tag):
        return 0.0

    score = TAG_SCORES.get(element.name.lower(), 0.5)

    # Boost score based on content length
    text_length = len(element.get_text(strip=True))
    if text_length > 100:
        score *= 1.5
    elif text_length > 50:
        score *= 1.2

    # Boost score for elements in important containers
    parent = element.parent
    while parent:
        if hasattr(parent, 'name') and parent.name:
            container_boost = CONTAINER_SCORES.get(parent.name.lower(), 0)
            score += container_boost * 0.1
        parent = parent.parent

    # Penalty for elements with little content
    if text_length < 10:
        score *= 0.3

    return score


def rank_content_by_importance(soup: BeautifulSoup) -> List[Tuple[Tag, float]]:
    """Rank content elements by importance score."""
    scored_elements = []

    # Focus on content-bearing elements
    content_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'blockquote', 'table']

    for tag_name in content_tags:
        for element in soup.find_all(tag_name):
            score = calculate_element_score(element)
            if score > 0.1:  # Only include elements with meaningful scores
                scored_elements.append((element, score))

    # Sort by score (highest first)
    scored_elements.sort(key=lambda x: x[1], reverse=True)

    return scored_elements


def convert_to_markdown(special_elements: Dict[str, List[str]], main_content: List[Tuple[Tag, float]]) -> str:
    """Convert parsed content to markdown format."""
    markdown_parts = []

    # Add main content
    seen_text = set()
    for element, score in main_content:
        text = element.get_text(strip=True)

        # Skip duplicate content
        if text in seen_text or len(text) < 10:
            continue
        seen_text.add(text)

        tag_name = element.name.lower()

        if tag_name.startswith('h'):
            # Headers
            level = int(tag_name[1])
            markdown_parts.append(f"{'#' * level} {text}")
        elif tag_name == 'p':
            # Paragraphs
            markdown_parts.append(text)
        elif tag_name == 'li':
            # List items
            markdown_parts.append(f"- {text}")
        elif tag_name == 'blockquote':
            # Blockquotes
            markdown_parts.append(f"> {text}")
        elif tag_name == 'table':
            # Simple table representation
            markdown_parts.append(f"**Table:** {text}")
        else:
            # Default case
            markdown_parts.append(text)

        markdown_parts.append("")  # Add spacing

    # Add special elements
    if special_elements['code_blocks']:
        markdown_parts.append("## Code Blocks")
        markdown_parts.extend(special_elements['code_blocks'])
        markdown_parts.append("")

    if special_elements['images']:
        markdown_parts.append("## Images")
        markdown_parts.extend(special_elements['images'][:5])  # Limit to 5 images
        markdown_parts.append("")

    if special_elements['links']:
        markdown_parts.append("## Important Links")
        # Get unique links and limit to 10
        unique_links = list(dict.fromkeys(special_elements['links']))[:10]
        markdown_parts.extend(unique_links)

    return "\n".join(markdown_parts)


def url_to_markdown(url: str) -> str:
    """
    Convert a URL to markdown format using advanced content extraction.

    This is the main function that replaces the original build_output function.
    It extracts HTML, analyzes content importance, and converts to markdown.

    Args:
        url: The URL to analyze and convert

    Returns:
        str: Markdown formatted content
    """
    try:
        # Ensure valid URL
        clean_url = ensure_url_scheme(url)

        # Extract HTML content
        html_content = extract_html_content(clean_url)

        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract special elements before cleaning
        special_elements = parse_special_elements(soup)

        # Clean HTML content
        cleaned_soup = clean_html_content(soup)

        # Rank content by importance
        main_content = rank_content_by_importance(cleaned_soup)

        # Convert to markdown
        markdown_result = convert_to_markdown(special_elements, main_content)

        return markdown_result

    except Exception as e:
        return f"Error processing URL {url}: {str(e)}"


class WebAnalyzerSkill:
    """Web Analyzer Skill for converting URLs to markdown content."""

    def __init__(self):
        self.name = "web_analyzer"
        self.description = "웹 페이지 URL을 마크다운 형식으로 변환하여 내용을 추출합니다"

    async def execute(self, url: str) -> Dict[str, Any]:
        """
        Execute the web analyzer skill.

        Args:
            url: The URL to analyze

        Returns:
            Dict containing the markdown content and metadata
        """
        try:
            if not validate_url(url):
                return {
                    'success': False,
                    'error': 'Invalid URL format',
                    'result': None
                }

            markdown_content = url_to_markdown(url)

            return {
                'success': True,
                'error': None,
                'result': markdown_content,
                'metadata': {
                    'url': url,
                    'processed_at': time.time(),
                    'content_length': len(markdown_content)
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'result': None
            }