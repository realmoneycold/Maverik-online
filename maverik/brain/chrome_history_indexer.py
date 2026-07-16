import os
import sqlite3
import shutil
import chromadb
from chromadb.utils import embedding_functions

def index_chrome_history():
    """
    Reads the Google Chrome history SQLite database, extracts URLs, and indexes them into ChromaDB.
    """
    # Chrome locks the History database, so we must copy it to a temp file first
    history_path = os.path.expanduser("~/.config/google-chrome/Default/History")
    temp_path = os.path.expanduser("~/.config/google-chrome/Default/History_temp")
    
    if not os.path.exists(history_path):
        print(f"Chrome history not found at {history_path}")
        return
        
    print("Copying Chrome History database...")
    shutil.copy2(history_path, temp_path)
    
    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        
        # Get the last 1000 visited URLs
        cursor.execute('''
            SELECT urls.url, urls.title, urls.visit_count, urls.last_visit_time
            FROM urls
            ORDER BY urls.last_visit_time DESC
            LIMIT 1000
        ''')
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} history entries. Indexing to ChromaDB...")
        
        # Initialize ChromaDB
        chroma_db_path = os.path.expanduser("~/.maverik_chroma_db")
        client = chromadb.PersistentClient(path=chroma_db_path)
        
        ollama_ef = embedding_functions.OllamaEmbeddingFunction(
            url="http://localhost:11434/api/embeddings",
            model_name="nomic-embed-text"
        )
        
        collection = client.get_or_create_collection(
            name="browser_history",
            embedding_function=ollama_ef
        )
        
        documents = []
        metadatas = []
        ids = []
        
        for i, row in enumerate(rows):
            url, title, visit_count, last_visit_time = row
            # Filter out empty or meaningless entries
            if not title or title.strip() == "":
                title = url
                
            content = f"Title: {title}\nURL: {url}"
            documents.append(content)
            metadatas.append({"url": url, "visit_count": visit_count})
            ids.append(f"history_{i}")
            
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Successfully indexed {len(documents)} browser history entries.")
            
    except Exception as e:
        print(f"Error reading history database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    index_chrome_history()
