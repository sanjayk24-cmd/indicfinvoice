from backend.services.conversation import ConversationService


def test_bank_name_interrupts_pending_balance():
    service = ConversationService()
    first = service.process_message('What is my account balance?', 'en', 'profile-test')
    assert first['pending']
    answer = service.process_message('what is my bank name', 'en', 'profile-test')
    assert answer['intent'] == 'bank_name'
    assert 'MockBank' in answer['reply']
    assert answer['pending'] is None


def test_account_number_does_not_invent_data():
    service = ConversationService()
    answer = service.process_message('what is my account number', 'en')
    assert answer['intent'] == 'account_number'
    assert 'does not store' in answer['reply']


def test_dispute_is_not_transaction_history():
    service = ConversationService()
    answer = service.process_message('I want to dispute transaction TXN-9001', 'en')
    assert answer['action'] != 'show_transactions'
