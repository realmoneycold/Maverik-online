import os
import glob
import chromadb
from typing import List

# Use Ollama for embeddings
from chromadb.utils import embedding_functions

def index_documents(directory: str = "~/Documents"):
    """
    Crawls the specified directory and indexes text/markdown files into ChromaDB.
    """
    directory = os.path.expanduser(directory)
    print(f"Starting to index documents in {directory}...")
    
    # Initialize ChromaDB client (persistent storage)
    chroma_db_path = os.path.expanduser("~/.maverik_chroma_db")
    client = chromadb.PersistentClient(path=chroma_db_path)
    
    # Set up Ollama embedding function
    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text"
    )
    
    # Create or get the collection
    collection = client.get_or_create_collection(
        name="local_documents",
        embedding_function=ollama_ef
    )
    
    # Simple chunker
    def chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    supported_extensions = ['.md', '.txt', '.py', '.json', '.csv']
    doc_id = 0
    
    for root, _, files in os.walk(directory):
        # Skip common hidden/build directories
        if any(skip in root for skip in ['.git', 'node_modules', '__pycache__', '.venv']):
            continue
            
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_extensions:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    if not content.strip():
                        continue
                        
                    chunks = chunk_text(content)
                    
                    ids = []
                    documents = []
                    metadatas = []
                    
                    for i, chunk in enumerate(chunks):
                        doc_id += 1
                        ids.append(f"doc_{doc_id}")
                        documents.append(chunk)
                        metadatas.append({"source": file_path, "chunk": i})
                        
                    # Add to ChromaDB
                    if documents:
                        collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                        print(f"Indexed {file_path} ({len(chunks)} chunks)")
                        
                except Exception as e:
                    print(f"Failed to read {file_path}: {e}")

    print(f"Finished indexing. Total chunks stored: {doc_id}")

if __name__ == "__main__":
    # You can pass a custom path here
    index_documents("~/Documents")
