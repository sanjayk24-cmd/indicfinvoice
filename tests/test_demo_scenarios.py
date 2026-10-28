import pytest
from fastapi.testclient import TestClient
from backend.main import app
from mockbank.api import BANK_DB

client = TestClient(app)

def test_customer_catalog_excludes_pins():
    data = client.get('/demo/customers').json()
    assert len(data) == 24
    assert all(set(c) == {'id', 'name', 'scenario'} for c in data)

@pytest.mark.parametrize('message,lang', [('मेरा बचत खाते का बैलेंस', 'hi'), ('எனது சேமிப்பு கணக்கு இருப்பு', 'ta'), ('my savings balance', 'en')])
def test_auto_text_language(message, lang):
    response = client.post('/chat', json={'message': message, 'lang': 'auto', 'customer_id': 'C001'})
    assert response.status_code == 200
    assert response.json()['lang'] == lang

def test_real_customer_history_and_empty_history():
    for cid in ('C001', 'C009'):
        result = client.post('/chat', json={'message': 'Show my transactions', 'lang': 'auto', 'customer_id': cid}).json()
        assert len(result['transactions']) == min(20, len(BANK_DB[cid]['transactions']))

def test_edge_balances():
    assert BANK_DB['C014']['accounts']['savings']['balance'] == 0
    assert BANK_DB['C015']['accounts']['savings']['balance'] < 0
    assert BANK_DB['C016']['accounts']['savings']['balance'] > 10000000

def test_unknown_customer_does_not_return_someone_elses_account():
    assert client.get('/account/summary?customer_id=C999').status_code == 404
