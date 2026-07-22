import sys
sys.path.insert(0,'.')
from dotenv import load_dotenv; load_dotenv()
from src.backend.agents.ocr_utils import extract_text
from src.backend.agents.document_agent import DocumentAgent
import pathlib

pdf_path = pathlib.Path('test-data/poland/identity/generated/PL-ID-001.pdf')
with open(pdf_path,'rb') as f:
    file_bytes = f.read()

print('File size:', len(file_bytes))
text, conf = extract_text(file_bytes, 'application/pdf')
print('OCR text:', repr(text[:200]))

agent = DocumentAgent()
result = agent.extract_fields(text, 'identity_card', 'PL')
print('Fields extracted:', len(result))
for r in result:
    print(' ', r['field_name'], r['value'], r['confidence'])
