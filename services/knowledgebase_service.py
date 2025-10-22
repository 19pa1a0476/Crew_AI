import os
import uuid
import stat
import shutil
import tempfile
import git
from urllib.parse import urlparse
from typing import List, Dict, Set
from langchain.text_splitter import Language
from agno.document import Document as AgnoDocument
from utilities.kb_file_parser_util import KnowledgebaseFileParser
from concurrent.futures import ThreadPoolExecutor
from utilities.llm_manager import embedding_model
from langchain_core.documents import Document as LangDocument
from git.exc import GitCommandError, InvalidGitRepositoryError
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter



def get_language_by_extension(extension: str) -> Language:
    """
    Map file extensions to corresponding Language enum values
    """
    extension_to_language = {
        # C and C++
        '.c': Language.C,
        '.h': Language.C,
        '.cpp': Language.CPP,
        '.hpp': Language.CPP,
        '.cc': Language.CPP,
        '.cxx': Language.CPP,
        
        # Web technologies
        '.js': Language.JS,
        '.jsx': Language.JS,
        '.ts': Language.TS,
        '.tsx': Language.TS,
        '.html': Language.HTML,
        '.htm': Language.HTML,
        
        # JVM languages
        '.java': Language.JAVA,
        '.kt': Language.KOTLIN,
        '.kts': Language.KOTLIN,
        '.scala': Language.SCALA,
        '.sc': Language.SCALA,
        
        # Scripting languages
        '.py': Language.PYTHON,
        '.pyw': Language.PYTHON,
        '.rb': Language.RUBY,
        '.rbw': Language.RUBY,
        '.php': Language.PHP,
        '.php3': Language.PHP,
        '.php4': Language.PHP,
        '.php5': Language.PHP,
        '.lua': Language.LUA,
        '.pl': Language.PERL,
        '.pm': Language.PERL,

        
        # Systems programming
        '.go': Language.GO,
        '.rs': Language.RUST,
        '.swift': Language.SWIFT,
        
        # Microsoft
        '.cs': Language.CSHARP,
        '.csx': Language.CSHARP,
        
        # Other languages
        '.hs': Language.HASKELL,
        '.lhs': Language.HASKELL,
        '.ex': Language.ELIXIR,
        '.exs': Language.ELIXIR,
        '.cbl': Language.COBOL,
        '.cob': Language.COBOL,
        '.sol': Language.SOL,
        
        # Documentation and markup
        '.md': Language.MARKDOWN,
        '.markdown': Language.MARKDOWN,
        '.rst': Language.RST,
        '.tex': Language.LATEX,
        
        # Protocol buffers
        '.proto': Language.PROTO,
    }
    return extension_to_language.get(extension.lower())


def clone_repo(repo_url: str, access_token: str = None, branch_name: str = None):
    """
    Clone a public or private Git repository to the .tmp directory.
    
    Args:
        repo_url (str): HTTPS URL of the Git repository.
        access_token (str, optional): Personal access token for private repos.
        branch_name (str, optional): Name of the branch to clone. If not specified, default branch is cloned.
        
    Returns:
        str: Path to the cloned repository.
        
    Raises:
        Exception: For invalid URL, authentication failure, or other errors.
    """
    try:
        # Create .tmp directory if it doesn't exist
        base_dir = os.path.join(os.getcwd(), ".tmp")
        os.makedirs(base_dir, exist_ok=True)

        # Parse repo name from URL
        parsed_url = urlparse(repo_url)
        repo_name = os.path.splitext(os.path.basename(parsed_url.path))[0]
        clone_path = os.path.join(base_dir, repo_name)

        # Remove existing clone if present
        if os.path.exists(clone_path):
            print(f"[INFO] Removing existing folder: {clone_path}")
            delete_temp_repository(clone_path)

        # Handle token injection for private repos
        if access_token:
            if "@" in parsed_url.netloc:
                raise ValueError("Repo URL contains embedded credentials. Remove them.")
            repo_url = repo_url.replace("https://", f"https://{access_token}@", 1)

        print(f"[INFO] Cloning repository from: {repo_url}")
        if branch_name:
            print(f"[INFO] Cloning branch: {branch_name}")
            git.Repo.clone_from(repo_url, clone_path, branch=branch_name, depth=1)
        else:
            git.Repo.clone_from(repo_url, clone_path)

        print(f"[SUCCESS] Repository cloned to: {clone_path}")
        return clone_path, repo_name

    except GitCommandError as e:
        delete_temp_repository(clone_path=clone_path)
        raise Exception(f"[ERROR] Git command failed: {e.stderr.strip() if e.stderr else str(e)}")
    except InvalidGitRepositoryError:
        delete_temp_repository(clone_path=clone_path)
        raise Exception("[ERROR] Invalid Git repository URL.")
    except Exception as e:
        delete_temp_repository(clone_path=clone_path)
        raise Exception(f"[ERROR] Unexpected error: {str(e)}")
        

def split_documents_by_language(documents: List, language: Language, chunk_size: int = 2000, chunk_overlap: int = 200) -> List:
    """
    Split documents using language-specific text splitter
    """
    try:
        if getattr(language, "value", language).lower() == "unknown":
            document_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        else:
            document_splitter = RecursiveCharacterTextSplitter.from_language(
                language=language,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        return document_splitter.split_documents(documents)
    except Exception as e:
        print(f"Error splitting documents for language {language}: {str(e)}")
        return documents
    

def load_code_files(
    clone_path: str,
    extension_list: List[str],
    parser_threshold: int = 2000
) -> List:
    """
    Load and parse code files using language-specific parsers
    
    Args:
        clone_path: Path to the directory containing code files
        extension_list: List of file extensions to process (e.g., ['.java', '.py'])
        parser_threshold: Threshold for the language parser
        
    Returns:
        List of parsed documents
    """
    # Group extensions by their corresponding language
    language_groups: Dict[Language, List[str]] = {}
    for ext in extension_list:
        lang = get_language_by_extension(ext) or "unknown"
        if lang not in language_groups:
            language_groups[lang] = []
        language_groups[lang].append(ext)
    
    print(language_groups)
    all_documents = []
    
    for language, extensions in language_groups.items():
        lang_str = getattr(language, "value", language).lower()
        print("language", lang_str)

        # Choosing the appropriate parser for reading the content as per the file extension
        if lang_str=="html" or lang_str=="markdown" or lang_str=="unknown":
            parser = KnowledgebaseFileParser()
        else:
            parser=LanguageParser(language=language,parser_threshold=parser_threshold)

        try:
            loader = GenericLoader.from_filesystem(
                path = clone_path,
                glob="**/*",
                suffixes=extensions,
                parser=parser
            )

            documents = loader.load()
            print(f"No of Documents : {len(documents)}")
            document_chunks = split_documents_by_language(
                documents=documents,
                language=language,
                chunk_size=2000,
                chunk_overlap=200
            )
            print(f"No of Documents Chunks: {len(document_chunks)}")
            all_documents.extend(document_chunks)
        except Exception as e:
            print(f"Error loading files with extensions {extensions}: {str(e)}")
    
    return all_documents

def delete_temp_repository(clone_path):
    # Delete the cloned repository
    if os.path.exists(clone_path):
        try:
            shutil.rmtree(clone_path, onerror=on_rm_error)
            print("Cloned repository deleted successfully.")
        except OSError as e:
            return(f"Error deleting cloned repository: {e}")


# Helper function for providing the required permissions for deleting the cloned project directory
def on_rm_error(func, path, exc_info):
    """ Error handler for `shutil.rmtree`. 
        If the error is due to an access error (read-only file), 
        it attempts to add write permission and then retries.
    """
    # Check if the file is read-only
    if not os.access(path, os.W_OK):
        # Add write permission
        os.chmod(path, stat.S_IWUSR)
        # Retry the removal
        func(path)
    else:
        raise


def chunked(iterable: List, batch_size: int):
    """Yield successive batches of given size from the iterable."""
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]
    

def convert_langchain_to_agno(docs: List[LangDocument], name: str) -> List[AgnoDocument]:
    """
    Convert a list of LangChain Document objects to Agno Document objects,
    with batched embeddings.
    """
    agno_docs = []
    contents = [doc.page_content for doc in docs]
    print("Content size:", len(contents))

    all_embeddings = []
    for batch in chunked(contents, 200):
        print(f"Processing batch of size {len(batch)}")
        embeddings = embedding_model.embed_documents(batch)
        all_embeddings.extend(embeddings)

    print("Embeddings size:", len(all_embeddings))

    for doc, embedding in zip(docs, all_embeddings):
        agno_doc = AgnoDocument(
            content=doc.page_content,
            meta_data=doc.metadata or {},
            name=name,
            embedding=embedding
        )
        agno_docs.append(agno_doc)
    return agno_docs


def convert_agno_to_langchain(docs: List[AgnoDocument]) -> List[LangDocument]:
    """
    Convert a list of Agno Document objects to LangChain Document objects.
    Embeddings are ignored since LangChain Document doesn't hold them directly.
    """
    langchain_docs = []
    for doc in docs:
        lc_doc = LangDocument(
            page_content=doc.content,
            metadata=doc.meta_data or {}
        )
        langchain_docs.append(lc_doc)
    return langchain_docs


def remove_duplicate_doc(documents: List[AgnoDocument]) -> List[AgnoDocument]:
    seen: Set[str] = set()
    unique_documents = []

    for doc in documents:
        if doc.content not in seen:
            seen.add(doc.content)
            unique_documents.append(doc)
    return unique_documents

