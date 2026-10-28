from datetime import date
import pytest
from fastapi.testclient import TestClient
from mockbank.api import app
from backend.services.transaction_query import query_transactions

ROWS = [dict(reference=f'TXN-{i}', date=f'2026-10-{20+i}', amount=amount,
             status=status, type=kind) for i, (amount, status, kind) in enumerate([
                 (0.50, 'completed', 'debit'), (1000, 'pending', 'credit'),
                 (1000.01, 'completed', 'debit'), (100000, 'failed', 'debit')])]

@pytest.mark.parametrize('query,refs', [
    ('transactions above 1,000', ['TXN-3','TXN-2']),
    ('transactions at least 1,000', ['TXN-3','TXN-2','TXN-1']),
    ('transactions exactly 0.50', ['TXN-0']),
    ('transactions at least 1 lakh', ['TXN-3']),
    ('completed debit transactions above 1000', ['TXN-2']),
    ('pending or failed transactions', ['TXN-3','TXN-1']),
    ('transactions from 2026-10-21 to 2026-10-22', ['TXN-2','TXN-1']),
    ('transactions before 2026-10-21', ['TXN-0']),
    ('transactions after 2026-10-22', ['TXN-3']),
    ('transactions yesterday', ['TXN-2']),
    ('transactions last 2 days', ['TXN-3','TXN-2']),
    ('oldest transactions', ['TXN-0','TXN-1','TXN-2','TXN-3']),
    ('lowest transactions', ['TXN-0','TXN-1','TXN-2','TXN-3']),
    ('transaction TXN-2', ['TXN-2']),
    ('transactions exactly 999', []),
])
def test_combined_query_semantics(query, refs):
    rows, _ = query_transactions(ROWS, query, date(2026,10,23))
    assert [r['reference'] for r in rows] == refs

@pytest.mark.parametrize('query', ['last 0 transactions', 'last -3 transactions',
    'last 101 transactions', 'transactions on 2026-02-30',
    'transactions 2026-10-23 to 2026-10-01', 'transactions last month',
    'transactions except failed', 'transactions last 0 days'])
def test_ambiguous_or_invalid_query_asks(query):
    with pytest.raises(ValueError):
        query_transactions(ROWS, query)

@pytest.mark.parametrize('amount,day', [(-1,'2026-10-24'), (0,'2026-10-24'),
    ('NaN','2026-10-24'), ('Infinity','2026-10-24'), (1500.001,'2026-10-24'),
    (1501,'2026-10-24'), (1500,'2026-02-30'), (1500,'2026-10-25')])
def test_dispute_invalid_money_and_date(amount, day):
    response = TestClient(app).post('/dispute', json={'customer_id':'C001',
        'transaction_ref':'TXN-9001', 'amount':amount, 'date':day, 'pin':'1234'})
    assert response.status_code == 400

def test_dispute_retry_is_idempotent():
    client = TestClient(app)
    payload = dict(customer_id='C001', transaction_ref='TXN-9001', amount=1500,
                   date='2026-10-24', pin='1234')
    assert client.post('/dispute', json=payload).json() == client.post('/dispute', json=payload).json()
