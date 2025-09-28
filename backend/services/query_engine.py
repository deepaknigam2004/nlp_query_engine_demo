import time, os, pickle, sqlite3
from sqlalchemy import create_engine, text, inspect
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse

from .schema_discovery import SchemaDiscovery

class QueryEngine:
    def __init__(self, connection_string: str = None):
        if not connection_string:
            connection_string = "sqlite:///./sample_data/sample.db"
        self.connection_string = connection_string
        self.schema = SchemaDiscovery().analyze_database(connection_string)
        self.cache = {}
        self.vectorizer = None
        self.doc_vectors = None
        self.doc_ids = None
        self._load_index()

    def _load_index(self):
        idx_dir = "sample_data/index"
        try:
            if os.path.exists(os.path.join(idx_dir, "vectorizer.pkl")):
                with open(os.path.join(idx_dir, "vectorizer.pkl"), "rb") as f:
                    self.vectorizer = pickle.load(f)
                self.doc_vectors = sparse.load_npz(os.path.join(idx_dir, "vectors.npz"))
                with open(os.path.join(idx_dir, "doc_ids.pkl"), "rb") as f:
                    self.doc_ids = pickle.load(f)
        except Exception as e:
            print("could not load index:", e)
            self.vectorizer = None
            self.doc_vectors = None
            self.doc_ids = None

    def process_query(self, user_query: str) -> dict:
        t0 = time.time()
        key = user_query.strip().lower()
        if key in self.cache:
            out = dict(self.cache[key])
            out['cache_hit'] = True
            out['time_ms'] = int((time.time() - t0) * 1000)
            return out

        doc_keywords = ['resume', 'resumes', 'cv', 'skill', 'skills', 'experience', 'document', 'documents']
        if any(k in key for k in doc_keywords):
            results = self._document_search(user_query, top_k=5)
            out = {'query_type': 'document', 'results': results, 'time_ms': int((time.time() - t0) * 1000), 'sources': 'documents'}
            self.cache[key] = out
            return out

        sql = self._map_to_sql(user_query)
        if sql:
            try:
                connect_args = {"check_same_thread": False} if self.connection_string.startswith("sqlite:") else {}
                engine = create_engine(self.connection_string, connect_args=connect_args)
                with engine.connect() as conn:
                    rows = conn.execute(text(sql)).fetchall()
                    # results = [dict(r) for r in rows]
                    results = [dict(r._mapping) for r in rows]
            except Exception as e:
                out = {'query_type': 'error', 'error': str(e), 'time_ms': int((time.time() - t0) * 1000)}
                return out
            out = {'query_type': 'sql', 'sql': sql, 'results': results, 'time_ms': int((time.time() - t0) * 1000), 'sources': 'database'}
            self.cache[key] = out
            return out

        results = self._document_search(user_query, top_k=5)
        out = {'query_type': 'fallback_document', 'results': results, 'time_ms': int((time.time() - t0) * 1000), 'sources': 'documents'}
        self.cache[key] = out
        return out

    def _document_search(self, query: str, top_k: int = 5):
        if not self.vectorizer or self.doc_vectors is None:
            return []
        qv = self.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.doc_vectors)[0]
        import numpy as np
        idxs = np.argsort(-sims)[:top_k]
        results = []
        conn = sqlite3.connect('sample_data/sample.db')
        c = conn.cursor()
        for idx in idxs:
            try:
                doc_id = int(self.doc_ids[idx])
                row = c.execute('SELECT id, filename, content FROM documents WHERE id = ?', (doc_id,)).fetchone()
                if row:
                    results.append({'id': row[0], 'filename': row[1], 'snippet': (row[2] or '')[:400], 'score': float(sims[idx])})
            except Exception:
                continue
        conn.close()
        return results

    def _find_table_like(self, tokens, prefer='emp'):
        tables = self.schema.get('tables', {}) if self.schema else {}
        for t in tables:
            low = t.lower()
            for token in tokens:
                if token in low:
                    return t
        for t in tables:
            if any(x in t.lower() for x in ['emp', 'staff', 'person', 'people']):
                return t
        return None

    def _map_to_sql(self, user_query: str) -> str:
        q = user_query.lower()
        tokens = q.split()
        if 'how many' in q or 'count' in q or 'number of' in q:
            table = self._find_table_like(tokens, prefer='emp')
            if table:
                return f"SELECT COUNT(*) as count FROM {table} LIMIT 1"
        if 'average' in q and 'salary' in q:
            table = self._find_table_like(tokens, prefer='emp')
            cols = self.schema.get('tables', {}).get(table, {}).get('columns', {}) if self.schema else {}
            salary_col = None
            for c in cols:
                if any(x in c.lower() for x in ['salary', 'comp', 'pay', 'rate']):
                    salary_col = c
                    break
            dept_col = None
            for c in cols:
                if any(x in c.lower() for x in ['dept', 'department', 'division']):
                    dept_col = c
                    break
            if table and salary_col and dept_col and 'by' in q and 'department' in q:
                return f"SELECT {dept_col} as department, AVG({salary_col}) as average_salary FROM {table} GROUP BY {dept_col} LIMIT 100"
            if table and salary_col:
                return f"SELECT AVG({salary_col}) as average_salary FROM {table} LIMIT 1"
        if 'list' in q or 'show me' in q or 'who' in q or 'employees' in q or 'employee' in q:
            table = self._find_table_like(tokens, prefer='emp')
            if table:
                cols = self.schema.get('tables', {}).get(table, {}).get('columns', {}).keys()
                sel = ', '.join(list(cols)[:8]) if cols else '*'
                import re
                m = re.search(r'over\s+(\d+[kK]?)', q)
                if m:
                    num_raw = m.group(1)
                    if num_raw.lower().endswith('k'):
                        num = int(num_raw[:-1]) * 1000
                    else:
                        num = int(num_raw)
                    salary_col = None
                    for c in self.schema.get('tables', {}).get(table, {}).get('columns', {}):
                        if any(x in c.lower() for x in ['salary','comp','pay','rate']):
                            salary_col = c
                            break
                    if salary_col:
                        return f"SELECT {sel} FROM {table} WHERE {salary_col} >= {num} LIMIT 100"
                return f"SELECT {sel} FROM {table} LIMIT 100"
        return None
