from unittest.mock import Mock
from backend.services.conversation import ConversationService
from backend.services.asr_service import ASRService
from test_asr_service import wav_bytes


def test_last_three_transactions():
    result = ConversationService().process_message('last 3 transactions', 'en')
    assert len(result['transactions']) == 3
    assert '3 matching' in result['reply']
    dates = [t['date'] for t in result['transactions']]
    assert dates == sorted(dates, reverse=True)


def test_filter_before_limit():
    result = ConversationService().process_message('last 3 pending transactions', 'en')
    assert len(result['transactions']) == 3
    assert all(t['status'] == 'pending' for t in result['transactions'])


def test_repetitive_speech_rejected():
    service = ASRService()
    service._whisper_pipe = Mock(return_value={'text': 'E ' * 150})
    result = service.transcribe_audio_bytes(wav_bytes(), 'auto')
    assert result['transcript'] == ''
    assert result['status'] == 'no_speech'


def test_thanks_is_not_banking_fallback():
    result = ConversationService().process_message('Thank you.', 'en')
    assert result['intent'] == 'greeting'
