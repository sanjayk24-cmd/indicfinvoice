"""Deterministic synthetic fixtures. Keeps the original C001-C003 test contracts."""
import json
from pathlib import Path
from datetime import date, timedelta

path = Path(__file__).resolve().parents[1] / 'mockbank' / 'db.json'
db = json.loads(path.read_text(encoding='utf-8'))
scenarios = ['salary account', 'zero balance', 'overdraft', 'high balance',
             'dormant account', 'frozen account', 'no loans', 'no claims',
             'no transactions', 'overdue loan', 'closed loan', 'pending payments']
names = ['Aarav Sharma', 'Meera Iyer', 'Kavya Raman', 'Arjun Patel', 'Priya Nair', 'Ravi Kumar']
for i in range(1, 25):
    cid = f'C{i:03}'
    scenario = scenarios[(i - 1) % len(scenarios)]
    if cid not in db:
        balance = {'zero balance': 0, 'overdraft': -2450.75, 'high balance': 12500000.99}.get(scenario, 52780.35)
        db[cid] = {'pin': f'{1000+i}', 'accounts': {'savings': {'balance': balance}},
                   'loans': {}, 'claims': {}, 'transactions': {}}
        if scenario != 'no loans':
            db[cid]['loans']['personal'] = {'due_date': '2026-09-15' if scenario == 'overdue loan' else '2026-11-15',
                'outstanding': 0 if scenario == 'closed loan' else 182450.50,
                'status': 'closed' if scenario == 'closed loan' else 'active', 'interest_rate': 10.75}
        if scenario != 'no claims':
            db[cid]['claims'][f'CLM-{1000+i}'] = {'status': ['approved', 'rejected', 'in_process'][i % 3], 'amount': 15000+i*500}
    cust = db[cid]
    if i > 3:
        cust['accounts']['savings']['balance'] = {'zero balance': 0, 'overdraft': -2450.75, 'high balance': 12500000.99}.get(scenario, 52780.35)
    cust['profile'] = {'name': names[(i-1) % len(names)] + f' (Demo {i})', 'scenario': scenario,
                       'bank_name': 'Indic Demo Bank', 'branch': ['Chennai', 'Pune', 'Lucknow'][i % 3],
                       'synthetic': True}
    for kind, account in cust['accounts'].items():
        account.update({'masked_account': f'XXXX {1000+i}', 'currency': 'INR',
                        'status': 'dormant' if scenario == 'dormant account' else 'frozen' if scenario == 'frozen account' else 'active'})
    if scenario != 'no transactions':
        for j in range(18):
            cust['transactions'][f'TXN-{i:03}{j:03}'] = {
                'amount': [1.0, 49.99, 2500.0, 75000.0, 125000.25, 0.50][j % 6],
                'date': str(date(2026, 10, 28) - timedelta(days=j)),
                'description': ['UPI · Groceries', 'NEFT · Salary', 'ATM · Cash withdrawal', 'IMPS · Rent', 'Card · Pharmacy', 'Refund · Online order'][j % 6],
                'type': 'credit' if j % 6 in (1, 5) else 'debit',
                'status': ['completed', 'pending', 'failed', 'reversed'][j % 4],
                'currency': 'INR'}
path.write_text(json.dumps(db, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{len(db)} synthetic customers; {sum(len(c["transactions"]) for c in db.values())} transactions')
