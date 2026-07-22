from dotenv import load_dotenv
load_dotenv()
import os
print('Key set:', bool(os.getenv('OPENAI_API_KEY')))
from src.backend.agents.document_agent import DocumentAgent
agent = DocumentAgent()
result = agent.extract_fields('Jan Kowalski, PESEL: 85010212345, ID: ABS123456, born 1985-01-02, expires 2030-03-15', 'identity_card', 'PL')
print('Fields:', len(result))
for f in result:
    print(f['field_name'], ':', f['value'], f['confidence'])
