from typing import List, Union
import uuid
import os 


DEFAULT_IGNORE_PATTERNS = [
    # Python
    '*.pyc', '*.pyo', '*.pyd', '__pycache__', '.pytest_cache', '.coverage',
    '.tox', '.nox', '.mypy_cache', '.ruff_cache', '.hypothesis',
    'poetry.lock', 'Pipfile.lock',
    
    # JavaScript/Node
    'node_modules', 'bower_components', 'package-lock.json', 'yarn.lock',
    '.npm', '.yarn', '.pnpm-store',
    
    # Version control
    '.git', '.svn', '.hg', '.gitignore', '.gitattributes', '.gitmodules',
    
    # Images and media
    '*.svg', '*.png', '*.jpg', '*.jpeg', '*.gif', '*.ico', '*.pdf',
    '*.mov', '*.mp4', '*.mp3', '*.wav',
    
    # Virtual environments
    'venv', '.venv', 'env', '.env', 'virtualenv',
    
    # IDEs and editors
    '.idea', '.vscode', '.vs', '*.swp', '*.swo', '*.swn',
    '.settings', '.project', '.classpath', '*.sublime-*',
    
    # Temporary and cache files
    '*.log', '*.bak', '*.swp', '*.tmp', '*.temp',
    '.cache', '.sass-cache', '.eslintcache',
    '.DS_Store', 'Thumbs.db', 'desktop.ini',
    
    # Build directories and artifacts
    'build', 'dist', 'target', 'out',
    '*.egg-info', '*.egg', '*.whl',
    '*.so', '*.dylib', '*.dll', '*.class',
    
    # Documentation
    'site-packages', '.docusaurus', '.next', '.nuxt',
    
    # Other common patterns
    '*.min.js', '*.min.css',  # Minified files
    '*.map',  # Source maps
    '.terraform', '*.tfstate*',  # Terraform
    'vendor/',  # Dependencies in various languages
]

TMP_BASE_PATH = "../tmp"

def parse_url(url: str) -> dict:
    parsed = {
        "user_name": None,
        "repo_name": None,
        "type": None,
        "branch": None,
        "commit": None,
        "subpath": "/",
        "local_path": None,
        "url": None,
        "slug": None,
        "id": None,
    }
    
    url = url.split(" ")[0]
    if not url.startswith('https://'):
        url = 'https://' + url
        
    # Extract domain and path
    url_parts = url.split('/')
    domain = url_parts[2]
    path_parts = url_parts[3:]
    
    if len(path_parts) < 2:
        raise ValueError("Invalid repository URL. Please provide a valid Git repository URL.")
        
    parsed["user_name"] = path_parts[0]
    parsed["repo_name"] = path_parts[1]
    
    # Keep original URL format
    parsed["url"] = f"https://{domain}/{parsed['user_name']}/{parsed['repo_name']}"
    parsed['slug'] = f"{parsed['user_name']}-{parsed['repo_name']}"
    parsed["id"] = str(uuid.uuid4())
    parsed["local_path"] = f"{TMP_BASE_PATH}/{parsed['id']}/{parsed['slug']}"

    if len(path_parts) > 3:
        parsed["type"] = path_parts[2]
        parsed["branch"] = path_parts[3]
        if len(parsed['branch']) == 40 and all(c in '0123456789abcdefABCDEF' for c in parsed['branch']):
            parsed["commit"] = parsed['branch']
            
        parsed["subpath"] = "/" + "/".join(path_parts[4:])
    return parsed

### 📝 **Normalize Pattern**
def normalize_pattern(pattern: str) -> str:
    """
    Normalize a pattern by stripping and formatting.

    Args:
        pattern (str): The ignore pattern.

    Returns:
        str: Normalized pattern.
    """
    pattern = pattern.strip()
    pattern = pattern.lstrip(os.sep)
    if pattern.endswith(os.sep):
        pattern += "*"
    return pattern

### 📝 **Parse Patterns**
def parse_patterns(pattern: Union[List[str], str]) -> List[str]:
    """
    Parse and validate patterns.

    Args:
        pattern (Union[List[str], str]): Patterns to parse.

    Returns:
        List[str]: Parsed patterns.
    """
    if isinstance(pattern, list):
        pattern = ",".join(pattern)

    for p in pattern.split(","):
        if not all(c.isalnum() or c in "-_./+*" for c in p.strip()):
            raise ValueError(
                f"Pattern '{p}' contains invalid characters. Only alphanumeric characters, dash (-), underscore (_), dot (.), forward slash (/), plus (+), and asterisk (*) are allowed."
            )
    return [normalize_pattern(p) for p in pattern.split(",")]

### 📝 **Override Ignore Patterns**
def override_ignore_patterns(ignore_patterns: List[str], include_patterns: List[str]) -> List[str]:
    """
    Remove include patterns from ignore patterns.

    Args:
        ignore_patterns (List[str]): Ignore patterns.
        include_patterns (List[str]): Include patterns.

    Returns:
        List[str]: Updated ignore patterns.
    """
    for pattern in include_patterns:
        if pattern in ignore_patterns:
            ignore_patterns.remove(pattern)
    return ignore_patterns


### 📝 **Parse Path**
def parse_path(path: str) -> dict:
    """
    Parse a local file path.

    Args:
        path (str): File path.

    Returns:
        dict: Parsed path details.
    """
    return {
        "local_path": os.path.abspath(path),
        "slug": os.path.basename(os.path.dirname(path)) + "/" + os.path.basename(path),
        "subpath": "/",
        "id": str(uuid.uuid4()),
        "url": None,
    }


def parse_query(source: str, max_file_size: int, from_web: bool, include_patterns: Union[List[str], str] = None, ignore_patterns: Union[List[str], str] = None) -> dict:
    if from_web:
        query = parse_url(source)
    else:
        if source.startswith("https://") or "github.com" in source:
            query = parse_url(source)
        else:
            query = parse_path(source)
    query['max_file_size'] = max_file_size

    if ignore_patterns and ignore_patterns != "":
        ignore_patterns = DEFAULT_IGNORE_PATTERNS + parse_patterns(ignore_patterns)
    else:
        ignore_patterns = DEFAULT_IGNORE_PATTERNS
    
    if include_patterns and include_patterns != "":
        include_patterns = parse_patterns(include_patterns)
        ignore_patterns = override_ignore_patterns(ignore_patterns, include_patterns)
    else: 
        include_patterns = None
    
    query['ignore_patterns'] = ignore_patterns
    query['include_patterns'] = include_patterns
    
    return query

### 📝 **Parse .gitignore**
def parse_gitignore(gitignore_path: str) -> List[str]:
    """
    Parse .gitignore and return ignore patterns.

    Args:
        gitignore_path (str): Path to the .gitignore file.

    Returns:
        List[str]: List of ignore patterns.
    """
    ignore_patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Ensure directory patterns end with '/'
                    if os.path.isdir(os.path.join(os.path.dirname(gitignore_path), line)):
                        line = line.rstrip('/') + '/'
                    ignore_patterns.append(line)
    return ignore_patterns


### 📝 **Parse Query**
def parse_query(source: str, max_file_size: int, from_web: bool,
                include_patterns: Union[List[str], str] = None,
                ignore_patterns: Union[List[str], str] = None) -> dict:
    """
    Parse the query and apply ignore patterns.

    Args:
        source (str): Source path or URL.
        max_file_size (int): Maximum file size.
        from_web (bool): Web source or local.
        include_patterns (Union[List[str], str]): Include patterns.
        ignore_patterns (Union[List[str], str]): Ignore patterns.

    Returns:
        dict: Query object with patterns.
    """
    if from_web:
        query = parse_url(source)
    else:
        query = parse_path(source)
    
    query['max_file_size'] = max_file_size

    # Start with default ignore patterns
    final_ignore_patterns = DEFAULT_IGNORE_PATTERNS.copy()

    # Load from .gitignore
    gitignore_path = os.path.join(query['local_path'], '.gitignore')
    print(f"find .gitignore on project --> {gitignore_path}")

    if os.path.exists(gitignore_path):
        gitignore_patterns = parse_gitignore(gitignore_path)
        final_ignore_patterns.extend(gitignore_patterns)
        print(f"\n🛡️  Patterns from: {gitignore_path}")
        for pattern in gitignore_patterns:
            print(f"  - {pattern}")
    # Add user-defined ignore patterns
    if ignore_patterns:
        final_ignore_patterns.extend(parse_patterns(ignore_patterns))
    
    # Handle include patterns
    if include_patterns:
        include_patterns = parse_patterns(include_patterns)
        final_ignore_patterns = override_ignore_patterns(final_ignore_patterns, include_patterns)
    
    query['ignore_patterns'] = final_ignore_patterns
    query['include_patterns'] = include_patterns
    # 🖨️ Print patterns to the console
    print("\n🛡️  Applied Ignore Patterns:")
    for pattern in final_ignore_patterns:
        print(f"  - {pattern}")
    
    if include_patterns:
        print("\n✅ Included Patterns:")
        for pattern in include_patterns:
            print(f"  - {pattern}")
    else:
        print("\n✅ Included Patterns: None")

    return query
    return query