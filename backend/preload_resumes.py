import os
sample_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'sample_data', 'resumes')
sample_dir = os.path.abspath(sample_dir)
files = [os.path.join(sample_dir, f) for f in os.listdir(sample_dir) if f.endswith('.txt')]
from backend.services.document_processor import DocumentProcessor
dp = DocumentProcessor()
dp.process_documents(files)
print('Preloaded', len(files), 'documents.')
