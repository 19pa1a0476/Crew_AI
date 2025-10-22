import json
import yaml
import markdown
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from langchain_core.documents import Document
from langchain_community.document_loaders.base import BaseBlobParser

class KnowledgebaseFileParser(BaseBlobParser):
    """A parser for Markdown, JSON, YAML, XML, and HTML content using LangChain Blob."""

    def lazy_parse(self, blob, source: str = None):
        """
        Parse the blob and yield Document objects based on file type.

        Args:
            blob: LangChain Blob object
            source: Optional source string to override metadata source

        Yields:
            Document objects
        """
        # Get the file extension from blob source or path
        blob_source = source or blob.source or ""
        ext = blob_source.lower()

        # Get content as string
        try:
            content = blob.as_string()
        except Exception as e:
            # fallback if blob cannot be read
            yield Document(page_content="", metadata={"source": blob_source})
            return

        # ----- Markdown -----
        if ext.endswith(".md"):
            html_content = markdown.markdown(content)
            text = BeautifulSoup(html_content, "html.parser").get_text(separator="\n")
            yield Document(page_content=text, metadata={"source": blob_source})

        # ----- JSON -----
        elif ext.endswith(".json"):
            try:
                data = json.loads(content)
                text = json.dumps(data, indent=2)
                yield Document(page_content=text, metadata={"source": blob_source})
            except Exception as e:
                yield Document(page_content=content, metadata={"source": blob_source})

        # ----- YAML -----
        elif ext.endswith(".yaml") or ext.endswith(".yml"):
            try:
                data = yaml.safe_load(content)
                text = yaml.dump(data)
                yield Document(page_content=text, metadata={"source": blob_source})
            except Exception as e:
                yield Document(page_content=content, metadata={"source": blob_source})

        # ----- XML -----
        elif ext.endswith(".xml"):
            try:
                root = ET.fromstring(content)
                text = ET.tostring(root, encoding="unicode")
                yield Document(page_content=text, metadata={"source": blob_source})
            except Exception as e:
                yield Document(page_content=content, metadata={"source": blob_source})

        # ----- HTML -----
        elif ext.endswith(".html"):
            text = BeautifulSoup(content, "html.parser").get_text(separator="\n")
            yield Document(page_content=text, metadata={"source": blob_source})
        
        # ----- TEXT/OTHER -----
        else:
            yield Document(page_content=content, metadata={"source": blob_source})

    def parse(self, blob, source: str = None):
        """Return all documents as a list."""
        return list(self.lazy_parse(blob, source))
