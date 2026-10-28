"""Deterministic query constraints; reject ambiguity instead of ignoring it."""
import re
from datetime import date, timedelta
from decimal import Decimal


def query_transactions(records, text, today=None):
    today = today or date.today()
    text = text.lower()
    rows = list(records)
    count = 20
    match = re.search(r'(?:last|latest|recent|पिछले|கடைசி)\s*(-?\d+|one|two|three|four|five|ten)\b(?!\s*(?:days?|weeks?|months?))', text)
    if match:
        token = match[1]
        count = int(token) if token.lstrip('-').isdigit() else {'one':1,'two':2,'three':3,'four':4,'five':5,'ten':10}[token]
        if not 1 <= count <= 100:
            raise ValueError('Please request between 1 and 100 transactions.')
    if re.search(r'\b(?:not|except|excluding)\b', text):
        raise ValueError('Please specify the status or transaction type you want to include.')
    for values, field in [(('pending','failed','reversed','completed'), 'status'), (('credit','debit'), 'type')]:
        selected = [v for v in values if re.search(r'\b'+v+r's?\b', text)]
        if selected:
            rows = [r for r in rows if r[field] in selected]
    ref = re.search(r'\btxn-\d+\b', text)
    if ref:
        rows = [r for r in rows if r['reference'].lower() == ref[0]]
    dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', text)
    start = end = None
    if dates:
        try:
            parsed = [date.fromisoformat(d) for d in dates]
        except ValueError:
            raise ValueError('Invalid date. Please use a valid YYYY-MM-DD date.')
        if len(parsed) > 2:
            raise ValueError('Please provide one date or a start and end date.')
        if len(parsed) == 2:
            start, end = parsed
            if start > end:
                raise ValueError('The start date must be before the end date.')
        elif 'before' in text:
            end = parsed[0] - timedelta(days=1)
        elif 'after' in text:
            start = parsed[0] + timedelta(days=1)
        else:
            start = end = parsed[0]
    elif 'yesterday' in text:
        start = end = today - timedelta(days=1)
    elif 'today' in text:
        start = end = today
    elif (period := re.search(r'last\s+(\d+)\s+days?\b', text)):
        days = int(period[1])
        if not 1 <= days <= 3650:
            raise ValueError('Please specify between 1 and 3650 days.')
        start, end = today - timedelta(days=days-1), today
    elif re.search(r'\b(?:week|month|year|since|between|before|after)\b|\d{1,2}/\d{1,2}', text):
        raise ValueError('Please provide the date range as YYYY-MM-DD to YYYY-MM-DD.')
    if start:
        rows = [r for r in rows if date.fromisoformat(r['date']) >= start]
    if end:
        rows = [r for r in rows if date.fromisoformat(r['date']) <= end]
    amount_pattern = r'(at least|at most|above|over|below|under|greater than|less than|exactly)\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)\s*(lakh|lac|crore|k)?\b'
    for op, value, unit in re.findall(amount_pattern, text):
        limit = Decimal(value.replace(',', '')) * {'':1, 'k':1000, 'lakh':100000, 'lac':100000, 'crore':10000000}[unit]
        compare = {'at least': lambda a:a>=limit, 'at most':lambda a:a<=limit,
                   'above':lambda a:a>limit, 'over':lambda a:a>limit, 'greater than':lambda a:a>limit,
                   'below':lambda a:a<limit, 'under':lambda a:a<limit, 'less than':lambda a:a<limit,
                   'exactly':lambda a:a==limit}[op]
        rows = [r for r in rows if compare(Decimal(str(r['amount'])))]
    order = 'newest first'
    if re.search(r'\b(?:highest|largest|biggest)\b', text):
        rows.sort(key=lambda r: Decimal(str(r['amount'])), reverse=True)
        order = 'highest amount first'
    elif re.search(r'\b(?:lowest|smallest)\b', text):
        rows.sort(key=lambda r: Decimal(str(r['amount'])))
        order = 'lowest amount first'
    else:
        rows.sort(key=lambda r:r['date'], reverse='oldest' not in text)
        if 'oldest' in text: order = 'oldest first'
    return rows[:count], order
