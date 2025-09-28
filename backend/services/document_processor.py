import os
import sqlite3
import pickle

class DocumentProcessor:
    def process_documents(self, file_paths: list) -> None:
        os.makedirs("sample_data", exist_ok=True)
        conn = sqlite3.connect("sample_data/sample.db")
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS documents (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     filename TEXT,
                     content TEXT
                     )""")
        for path in file_paths:
            filename = os.path.basename(path)
            ext = filename.split('.')[-1].lower()
            content = ""
            try:
                if ext == 'txt':
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                elif ext == 'csv':
                    import pandas as pd
                    df = pd.read_csv(path)
                    content = df.to_csv(index=False)
                else:
                    content = f"[{ext} file uploaded] (content extraction not implemented in demo)"
            except Exception as e:
                content = f"[error reading file: {e}]"
            c.execute("INSERT INTO documents(filename, content) VALUES (?,?)", (filename, content))
        conn.commit()
        conn.close()
        self.build_tfidf_index()

    def build_tfidf_index(self):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from scipy import sparse
        except Exception as e:
            print("skipping index build (missing sklearn/scipy):", e)
            return

        conn = sqlite3.connect("sample_data/sample.db")
        c = conn.cursor()
        rows = c.execute("SELECT id, content FROM documents").fetchall()
        doc_ids = [r[0] for r in rows]
        docs = [r[1] or "" for r in rows]
        if not docs:
            conn.close()
            return
        vectorizer = TfidfVectorizer(stop_words='english', max_features=2000)
        vectors = vectorizer.fit_transform(docs)
        os.makedirs("sample_data/index", exist_ok=True)
        with open("sample_data/index/vectorizer.pkl", "wb") as f:
            pickle.dump(vectorizer, f)
        sparse.save_npz("sample_data/index/vectors.npz", vectors)
        with open("sample_data/index/doc_ids.pkl", "wb") as f:
            pickle.dump(doc_ids, f)
        conn.close()
