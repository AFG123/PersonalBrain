import json
import os
from typing import List
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

def load_document_paths() -> tuple[List[dict], List[dict]]:
    """Load document paths from paths.json"""
    with open('paths.json', 'r') as f:
        data = json.load(f)
    return data.get('document_directories', []), data.get('individual_documents', [])

def load_directory(directory_config: dict) -> List[dict]:
    """Load all PDFs from a directory"""
    base_path = Path(directory_config['directory_path'])
    if not base_path.exists():
        print(f"Warning: Directory {base_path} does not exist")
        return []

    # Get all PDF files in the directory
    pattern = "**/*.pdf" if directory_config.get('recursive', True) else "*.pdf"
    pdf_files = list(base_path.glob(pattern))
    
    all_docs = []
    for pdf_path in pdf_files:
        # Skip files matching exclude patterns
        if any(pdf_path.match(pattern) for pattern in directory_config.get('exclude_patterns', [])):
            continue
            
        try:
            try:
                loader = PyPDFLoader(str(pdf_path))
                docs = loader.load()
                
                # Add metadata to each page
                for doc in docs:
                    tags = directory_config.get('tags', []) + ['auto-indexed']
                    doc.metadata.update({
                        'source': str(pdf_path),
                        'type': 'pdf',
                        'directory': str(base_path),
                        'description': directory_config.get('description', ''),
                        'tags': ', '.join(tags)
                    })
                all_docs.extend(docs)
                print(f"Successfully loaded {pdf_path}")
            except Exception as e:
                print(f"Error loading {pdf_path}: {str(e)}")
            
        except Exception as e:
            print(f"Error loading {pdf_path}: {str(e)}")
            continue
    
    return all_docs

def load_and_split_documents():
    """Load documents and split them into chunks"""
    directories, individual_docs = load_document_paths()
    
    all_docs = []
    
    # Load documents from directories
    for directory_config in directories:
        docs = load_directory(directory_config)
        all_docs.extend(docs)
    
    # Load individual documents
    for doc_config in individual_docs:
        if not os.path.exists(doc_config['path']):
            print(f"Warning: File {doc_config['path']} does not exist")
            continue
            
        try:
            loader = PyPDFLoader(doc_config['path'])
            docs = loader.load()
            
            # Add metadata
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
    
    # Split documents into chunks
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
    """Initialize ChromaDB with documents"""
    try:
        # Load and split documents
        splits = load_and_split_documents()
        
        # Initialize embeddings
        embeddings = OllamaEmbeddings(model="mxbai-embed-large")
        
        # Create and persist vector store
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory="chroma_db"
        )
        vectorstore.persist()
        return vectorstore
        
    except Exception as e:
        print(f"Error initializing vector store: {str(e)}")
        raise

# Create retriever instance
vectorstore = initialize_vectorstore()
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)
 
def search(query: str, k: int = 6, metadata_filter: dict | None = None):
    """Search the vectorstore and return Document objects.

    - query: text query
    - k: number of results
    - metadata_filter: optional dict to filter results, e.g. {"source": "..."}
    """
    if metadata_filter:
        return vectorstore.similarity_search(query, k=k, filter=metadata_filter)
    return vectorstore.similarity_search(query, k=k)