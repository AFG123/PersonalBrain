import json
import os
from typing import List
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, UnstructuredPowerPointLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

# Lazy-initialized vectorstore to avoid heavy work at import time
_vectorstore = None


def load_document_paths() -> tuple[List[dict], List[dict]]:
    """Load document paths from paths.json"""
    with open('paths.json', 'r') as f:
        data = json.load(f)
    return data.get('document_directories', []), data.get('individual_documents', [])


def load_directory(directory_config: dict) -> List[dict]:
    """Load all supported files from a directory (.pdf, .docx, .pptx)"""
    base_path = Path(directory_config['directory_path'])
    if not base_path.exists():
        print(f"Warning: Directory {base_path} does not exist")
        return []

    recursive = directory_config.get('recursive', True)
    patterns = ["**/*.pdf", "**/*.docx", "**/*.pptx"] if recursive else ["*.pdf", "*.docx", "*.pptx"]
    files = []
    for pattern in patterns:
        files.extend(base_path.glob(pattern))

    all_docs = []
    for file_path in files:
        if any(file_path.match(pattern) for pattern in directory_config.get('exclude_patterns', [])):
            continue
        try:
            if file_path.suffix.lower() == ".pdf":
                loader = PyPDFLoader(str(file_path))
                file_type = "pdf"
            elif file_path.suffix.lower() == ".docx":
                loader = UnstructuredWordDocumentLoader(str(file_path))
                file_type = "word"
            elif file_path.suffix.lower() == ".pptx":
                loader = UnstructuredPowerPointLoader(str(file_path))
                file_type = "powerpoint"
            else:
                continue
            docs = loader.load()
            for doc in docs:
                tags = directory_config.get('tags', []) + ['auto-indexed']
                doc.metadata.update({
                    'source': str(file_path),
                    'type': file_type,
                    'directory': str(base_path),
                    'description': directory_config.get('description', ''),
                    'tags': ', '.join(tags)
                })
            all_docs.extend(docs)
            print(f"Successfully loaded {file_path}")
        except Exception as e:
            print(f"Error loading {file_path}: {str(e)}")
            continue

    return all_docs


def load_and_split_documents():
    """Load documents and split them into chunks"""
    directories, individual_docs = load_document_paths()

    all_docs = []

    for directory_config in directories:
        docs = load_directory(directory_config)
        all_docs.extend(docs)

    for doc_config in individual_docs:
        if not os.path.exists(doc_config['path']):
            print(f"Warning: File {doc_config['path']} does not exist")
            continue
        try:
            loader = PyPDFLoader(doc_config['path'])
            docs = loader.load()
            for doc in docs:
                tags = doc_config.get('tags', [])
                doc.metadata.update({
                    'source': doc_config['path'],
                    'type': doc_config['type'],
                    'description': doc_config.get('description', ''),
                    'tags': ', '.join(tags)
                })
            all_docs.extend(docs)
        except Exception as e:
            print(f"Error loading {doc_config['path']}: {str(e)}")
            continue

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    if not all_docs:
        raise ValueError("No documents were successfully loaded!")

    splits = text_splitter.split_documents(all_docs)
    print(f"Loaded {len(all_docs)} documents, split into {len(splits)} chunks")
    return splits


def initialize_vectorstore():
    """Initialize ChromaDB with documents (expensive)"""
    try:
        splits = load_and_split_documents()
        embeddings = OllamaEmbeddings(model="mxbai-embed-large")
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory="chroma_db"
        )
        # Chroma 0.4.x persists automatically; keep old call safe
        try:
            vectorstore.persist()
        except Exception:
            pass
        return vectorstore
    except Exception as e:
        print(f"Error initializing vector store: {str(e)}")
        raise


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = initialize_vectorstore()
    return _vectorstore


def search(query: str, k: int = 6, metadata_filter: dict | None = None):
    """Search the (lazily initialized) vectorstore and return Document objects."""
    vs = get_vectorstore()
    if metadata_filter:
        return vs.similarity_search(query, k=k, filter=metadata_filter)
    return vs.similarity_search(query, k=k)
