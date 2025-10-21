import os
import git
from pathlib import Path
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import re
import mimetypes


class RepositoryIngester:
    def __init__(self, base_path: str = "./data/repositories"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Enhanced file type mappings
        self.doc_extensions = {'.md', '.rst', '.txt', '.adoc', '.asciidoc', '.org'}
        self.code_extensions = {
            '.wdl', '.java', '.py', '.sh', '.js', '.ts', '.jsx', '.tsx',
            '.go', '.rs', '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php',
            '.scala', '.kt', '.swift', '.r', '.sql'
        }
        self.config_extensions = {
            '.json', '.yaml', '.yml', '.toml', '.ini', '.xml', 
            '.conf', '.config', '.properties'
        }
        
        # Special files without extensions
        self.special_files = {
            'Dockerfile': 'code',
            'Makefile': 'code',
            'Vagrantfile': 'code',
            '.gitignore': 'configuration',
            '.dockerignore': 'configuration',
            'requirements.txt': 'configuration',
            'package.json': 'configuration',
            'pom.xml': 'configuration',
            'build.gradle': 'configuration',
            'Cargo.toml': 'configuration',
            'go.mod': 'configuration',
            'README': 'documentation',
            'LICENSE': 'documentation',
            'CHANGELOG': 'documentation',
        }

        # Files to exclude (common infrastructure files that are identical across repos)
        self.exclude_files = {
            'Jenkinsfile',           # CI/CD pipeline - usually identical
            '.gitignore',            # Git config - usually identical
            '.dockerignore',         # Docker config - usually identical
            'LICENSE',               # License files - often identical
            '.gitlab-ci.yml',        # GitLab CI - usually identical
            '.travis.yml',           # Travis CI - usually identical
            'circle.yml',            # CircleCI - usually identical
            '.github/workflows',     # GitHub Actions - often identical
            'compare.sh'
        }
        
        # Language detection mapping
        self.lang_map = {
            '.py': 'python',
            '.java': 'java',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'react',
            '.tsx': 'react-typescript',
            '.wdl': 'wdl',
            '.sh': 'bash',
            '.bash': 'bash',
            '.go': 'go',
            '.rs': 'rust',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c-header',
            '.hpp': 'cpp-header',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php',
            '.scala': 'scala',
            '.kt': 'kotlin',
            '.swift': 'swift',
            '.r': 'r',
            '.sql': 'sql',
            '.md': 'markdown',
            '.rst': 'restructuredtext',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
        }

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded"""
        file_name = file_path.name
        
        # Check exact filename matches
        if file_name in self.exclude_files:
            return True
        
        # Check if file is in excluded directory path
        path_str = str(file_path)
        for excluded_path in self.exclude_files:
            if excluded_path in path_str:
                return True
        
        return False
        
    def clone_or_update_repo(self, repo_url: str) -> Path:
        """Clone or update a repository"""
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        local_path = self.base_path / repo_name
        
        print(f"Processing repository: {repo_name}")
        
        if local_path.exists():
            print(f"  Updating existing repository...")
            try:
                repo = git.Repo(local_path)
                repo.remotes.origin.pull()
            except Exception as e:
                print(f"  Warning: Could not update repository: {e}")
        else:
            print(f"  Cloning repository...")
            git.Repo.clone_from(repo_url, local_path)
        
        return local_path
    
    def get_file_metadata(self, file_path: Path, repo_path: Path) -> Dict:
        """Get comprehensive file metadata"""
        relative_path = file_path.relative_to(repo_path)
        suffix = file_path.suffix.lower()
        file_name = file_path.name
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        # Determine category
        category = self.categorize_file(file_path)
        
        # Detect programming language for code files
        language = self.detect_language(file_path)
        
        metadata = {
            'source_file': str(relative_path),
            'file_name': file_name,
            'file_type': suffix if suffix else 'no_extension',
            'file_category': category,
            'mime_type': mime_type or 'unknown',
            'repo_name': repo_path.name,
            'source_type': 'repository'
        }
        
        # Add language info for code files
        if language:
            metadata['language'] = language
        
        # Add directory context
        parent_dir = relative_path.parent.name if relative_path.parent != Path('.') else 'root'
        metadata['directory'] = parent_dir
        
        return metadata
    
    def categorize_file(self, file_path: Path) -> str:
        """Categorize file by type with special file handling"""
        file_name = file_path.name
        suffix = file_path.suffix.lower()
        
        # Check special files first
        if file_name in self.special_files:
            return self.special_files[file_name]
        
        # Check by extension
        if suffix in self.doc_extensions:
            return 'documentation'
        elif suffix in self.code_extensions:
            return 'code'
        elif suffix in self.config_extensions:
            return 'configuration'
        else:
            return 'other'
    
    def detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        suffix = file_path.suffix.lower()
        return self.lang_map.get(suffix, '')
    
    def extract_files(
        self, 
        repo_path: Path,
        include_categories: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract files with enhanced metadata"""
        if include_categories is None:
            include_categories = ['documentation', 'code', 'configuration']
        
        documents = []
        exclude_dirs = {
            '.git', 'node_modules', '__pycache__', '.pytest_cache', 
            'target', 'build', 'dist', '.idea', '.vscode', 'venv',
            '.gradle', '.mvn', 'bin', 'obj', 'vendor', '.next'
        }
        
        # Exclude patterns for files
        exclude_patterns = {
            '.class', '.pyc', '.pyo', '.so', '.dll', '.dylib',
            '.exe', '.bin', '.o', '.a', '.jar', '.war',
            '.min.js', '.bundle.js',  # Minified/bundled files
            '.lock', '.log'
        }
        
        excluded_count = 0
        
        for file_path in repo_path.rglob('*'):
            # Skip directories and excluded paths
            if file_path.is_dir():
                continue
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
            if any(file_path.name.endswith(pattern) for pattern in exclude_patterns):
                continue
            
            # Skip excluded common files
            if self.should_exclude_file(file_path):
                excluded_count += 1
                continue
            
            # Get metadata
            metadata = self.get_file_metadata(file_path, repo_path)
            category = metadata['file_category']
            
            # Skip if not in included categories
            if category not in include_categories:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Skip empty or very small files
                if len(content.strip()) < 50:
                    continue
                
                # Add file size to metadata
                metadata['file_size'] = len(content)
                
                documents.append({
                    'content': content,
                    'metadata': metadata
                })
                
            except Exception as e:
                print(f"  Error reading {file_path}: {e}")
                continue
        
        if excluded_count > 0:
            print(f"  Excluded {excluded_count} common infrastructure files")
        print(f"  Extracted {len(documents)} files from {repo_path.name}")
        return documents


class SmartChunker:
    """Unified chunker that handles different content types intelligently"""
    
    def __init__(self):
        self.wdl_pattern = re.compile(r'(task|workflow|struct)\s+(\w+)\s*\{', re.MULTILINE)
        
        # Different chunking strategies by category
        self.chunk_configs = {
            'documentation': {
                'chunk_size': 1500,
                'chunk_overlap': 200,
                'separators': ["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " "]
            },
            'code': {
                'chunk_size': 1200,
                'chunk_overlap': 150,
                'separators': ["\n\nclass ", "\n\ndef ", "\n\nfunction ", "\n\n", "\n"]
            },
            'configuration': {
                'chunk_size': 800,
                'chunk_overlap': 100,
                'separators': ["\n\n", "\n"]
            }
        }
        
        # Language-specific separators for better code chunking
        self.language_separators = {
            'python': ["\n\nclass ", "\n\ndef ", "\n\nasync def ", "\n\n@", "\n\n", "\n"],
            'java': ["\n\npublic class ", "\n\nclass ", "\n\npublic ", "\n\nprivate ", "\n\n", "\n"],
            'javascript': ["\n\nfunction ", "\n\nconst ", "\n\nlet ", "\n\nclass ", "\n\nexport ", "\n\n", "\n"],
            'typescript': ["\n\nfunction ", "\n\nconst ", "\n\nlet ", "\n\nclass ", "\n\nexport ", "\n\ninterface ", "\n\n", "\n"],
            'bash': ["\n\nfunction ", "\n\n# ", "\n\n", "\n"],
            'sql': ["\n\nCREATE ", "\n\nALTER ", "\n\nSELECT ", "\n\n", ";\n"],
        }
    
    def chunk(self, content: str, metadata: Dict[str, Any]) -> List[Document]:
        """Smart chunking based on file category and language"""
        category = metadata.get('file_category', 'other')
        file_type = metadata.get('file_type', '')
        language = metadata.get('language', '')
        
        # Special handling for WDL files
        if file_type == '.wdl' or language == 'wdl':
            return self._chunk_wdl(content, metadata)
        
        # Get appropriate separators
        if language and language in self.language_separators:
            separators = self.language_separators[language]
            config = self.chunk_configs.get('code')
        else:
            config = self.chunk_configs.get(category, self.chunk_configs['code'])
            separators = config['separators']
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config['chunk_size'],
            chunk_overlap=config['chunk_overlap'],
            separators=separators,
            length_function=len,
        )
        
        chunks = splitter.split_text(content)
        
        return [
            Document(
                page_content=chunk,
                metadata={
                    **metadata,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'chunking_strategy': language if language else category
                }
            )
            for i, chunk in enumerate(chunks)
        ]
    
    def _chunk_wdl(self, content: str, metadata: Dict[str, Any]) -> List[Document]:
        """Special chunking for WDL workflow files"""
        chunks = []
        
        # Extract imports (keep as separate chunk)
        import_lines = [line for line in content.split('\n') if line.strip().startswith('import')]
        if import_lines:
            chunks.append(Document(
                page_content='\n'.join(import_lines),
                metadata={
                    **metadata,
                    'chunk_type': 'wdl_imports',
                    'wdl_element_type': 'imports'
                }
            ))
        
        # Extract structured elements (tasks, workflows, structs)
        for match in self.wdl_pattern.finditer(content):
            element_type = match.group(1)  # task, workflow, or struct
            element_name = match.group(2)
            element_content = self._extract_wdl_block(content, match.start())
            
            if element_content:
                chunks.append(Document(
                    page_content=element_content,
                    metadata={
                        **metadata,
                        'chunk_type': f'wdl_{element_type}',
                        'wdl_element_type': element_type,
                        'wdl_element_name': element_name
                    }
                ))
        
        # If no semantic chunks found, fall back to whole file
        if not chunks:
            chunks.append(Document(
                page_content=content,
                metadata={
                    **metadata,
                    'chunk_type': 'wdl_full_file'
                }
            ))
        
        return chunks
    
    def _extract_wdl_block(self, content: str, start_pos: int) -> str:
        """Extract a balanced brace block starting from position"""
        brace_count = 0
        in_block = False
        
        for i in range(start_pos, len(content)):
            char = content[i]
            
            if char == '{':
                brace_count += 1
                in_block = True
            elif char == '}':
                brace_count -= 1
                
                if in_block and brace_count == 0:
                    return content[start_pos:i+1]
        
        return ""


def ingest_repositories(
    repo_urls: List[str],
    vector_service,
    include_categories: List[str] = None
) -> Dict[str, int]:
    """
    Main ingestion function
    
    Args:
        repo_urls: List of GitHub repository URLs
        vector_service: VectorService instance
        include_categories: List of categories to include (default: all)
    
    Returns:
        Dictionary with ingestion statistics
    """
    ingester = RepositoryIngester()
    chunker = SmartChunker()
    
    if include_categories is None:
        include_categories = ['documentation', 'code', 'configuration']
    
    stats = {
        'total_repos': len(repo_urls),
        'total_files': 0,
        'total_chunks': 0,
        'by_category': {},
        'by_language': {},
        'failed_repos': []
    }
    
    all_documents = []
    
    for repo_url in repo_urls:
        try:
            # Clone/update repository
            repo_path = ingester.clone_or_update_repo(repo_url)
            
            # Extract files
            files = ingester.extract_files(repo_path, include_categories)
            stats['total_files'] += len(files)
            
            # Process each file
            for file_doc in files:
                content = file_doc['content']
                metadata = file_doc['metadata']
                
                # Track stats by category
                category = metadata['file_category']
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
                
                # Track stats by language
                language = metadata.get('language', 'unknown')
                if language:
                    stats['by_language'][language] = stats['by_language'].get(language, 0) + 1
                
                # Chunk the content
                try:
                    chunks = chunker.chunk(content, metadata)
                    all_documents.extend(chunks)
                    stats['total_chunks'] += len(chunks)
                except Exception as e:
                    print(f"  Warning: Could not chunk {metadata['source_file']}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error processing repository {repo_url}: {e}")
            stats['failed_repos'].append({'url': repo_url, 'error': str(e)})
            import traceback
            traceback.print_exc()
            continue
    
    # Add to vector store
    if all_documents:
        print(f"\nAdding {len(all_documents)} chunks to vector store...")
        try:
            vector_service.add_documents(all_documents)
            print("✓ Successfully added all chunks")
        except Exception as e:
            print(f"✗ Error adding documents to vector store: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No documents to add")
    
    return stats


def print_stats(stats: Dict[str, Any]):
    """Print formatted statistics"""
    print("\n" + "="*70)
    print("INGESTION COMPLETE!")
    print("="*70)
    print(f"  Repositories processed: {stats['total_repos']}")
    print(f"  Files extracted: {stats['total_files']}")
    print(f"  Chunks created: {stats['total_chunks']}")
    
    if stats['by_category']:
        print(f"\n  By category:")
        for category, count in sorted(stats['by_category'].items()):
            print(f"    - {category}: {count} files")
    
    if stats['by_language']:
        print(f"\n  By language:")
        for language, count in sorted(stats['by_language'].items(), key=lambda x: x[1], reverse=True):
            print(f"    - {language}: {count} files")
    
    if stats['failed_repos']:
        print(f"\n  Failed repositories: {len(stats['failed_repos'])}")
        for failed in stats['failed_repos']:
            print(f"    - {failed['url']}: {failed['error']}")
    
    print("="*70)


if __name__ == "__main__":
    from rag_chatbot.services.vector_service import VectorService
    
    # List of repositories to ingest
    with open("data/repos.txt") as f:
        REPO_URLS = [line.strip() for line in f if line.strip()]
    
    print("Starting repository ingestion...")
    print(f"Repositories to process: {len(REPO_URLS)}")
    
    # Initialize vector service
    vector_service = VectorService()
    
    # Ingest repositories
    # You can filter what to include:
    stats = ingest_repositories(
        REPO_URLS, 
        vector_service,
        include_categories=['documentation', 'code', 'configuration']
    )
    
    # Print results
    print_stats(stats)