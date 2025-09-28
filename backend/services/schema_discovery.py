from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

class SchemaDiscovery:
    current_schema = {}

    def analyze_database(self, connection_string: str) -> dict:
        engine = None
        try:
            connect_args = {"check_same_thread": False} if connection_string.startswith("sqlite:") else {}
            engine = create_engine(connection_string, connect_args=connect_args)
            inspector = inspect(engine)
            tables_info = {}
            with engine.connect() as conn:
                for tbl in inspector.get_table_names():
                    cols = inspector.get_columns(tbl)
                    col_info = {c['name']: str(c['type']) for c in cols}
                    sample_rows = []
                    try:
                        res = conn.execute(text(f"SELECT * FROM {tbl} LIMIT 3"))
                        rows = res.fetchall()
                        for r in rows:
                            rowd = dict(r.items()) if hasattr(r, 'items') else dict(zip(r.keys(), r))
                            sample_rows.append(rowd)
                    except Exception:
                        sample_rows = []
                    tables_info[tbl] = {"columns": col_info, "sample": sample_rows}
            SchemaDiscovery.current_schema = {"connection_string": connection_string, "tables": tables_info}
            return SchemaDiscovery.current_schema
        except SQLAlchemyError as e:
            raise
