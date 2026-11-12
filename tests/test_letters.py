import unittest
from datetime import date
from streamlit.testing.v1 import AppTest


class LetterTests(unittest.TestCase):
    def test_prompt_date_and_literal_complaint(self):
        from prompts import build_prompt
        prompt = build_prompt('Acknowledge complaint', date(2026, 11, 12), 'My appointment was cancelled.')
        self.assertIn('12 November 2026', prompt)
        self.assertIn('My appointment was cancelled.', prompt)
        self.assertNotIn('[Insert patient', prompt)

    def test_requires_findings_for_outcome(self):
        from prompts import build_prompt
        with self.assertRaises(ValueError):
            build_prompt('Final response', date.today(), 'Complaint', '  ')

    def test_preview_without_credentials_and_blank_validation(self):
        at = AppTest.from_file('../app.py').run()
        self.assertFalse(at.exception)
        at.button(key='preview').click().run()
        self.assertTrue(at.error)
        at.text_area(key='source').set_value('My appointment was cancelled.').run()
        at.button(key='preview').click().run()
        self.assertFalse(at.exception)
        self.assertTrue(at.code)

    def test_edited_draft_survives_workflow_switch(self):
        at = AppTest.from_file('../app.py').run()
        at.session_state['draft_Acknowledge complaint'] = 'A draft'
        at.run()
        at.text_area(key='draft_editor').set_value('My edited draft').run()
        at.radio(key='workflow').set_value('Email rewriter').run()
        at.radio(key='workflow').set_value('Acknowledge complaint').run()
        self.assertEqual(at.text_area(key='draft_editor').value, 'My edited draft')

class GenerationTests(unittest.TestCase):
    def test_success_then_failure_preserves_edited_draft(self):
        from unittest.mock import patch, MagicMock
        from groq import APIConnectionError
        import httpx
        result = MagicMock()
        result.choices[0].finish_reason = 'stop'
        result.choices[0].message.content = '<think>private analysis</think>Dear patient,\nA complete draft.'
        with patch('streamlit.secrets', {'GROQ_API_KEY': 'test-only'}), patch('groq.Groq') as factory:
            client = factory.return_value.__enter__.return_value
            client.chat.completions.create.return_value = result
            at = AppTest.from_file('../app.py').run()
            at.text_area(key='source').set_value('My appointment was cancelled.').run()
            at.button(key='generate').click().run()
            self.assertFalse(at.exception)
            self.assertNotIn('private analysis', at.text_area(key='draft_editor').value)
            at.text_area(key='draft_editor').set_value('My edited letter').run()
            client.chat.completions.create.side_effect = APIConnectionError(request=httpx.Request('POST', 'https://example.test'))
            at.button(key='generate').click().run()
            self.assertFalse(at.exception)
            self.assertTrue(at.error)
            self.assertFalse(at.success)
            self.assertEqual(at.text_area(key='draft_editor').value, 'My edited letter')

    def test_inputs_survive_switch_and_clear_is_scoped(self):
        at = AppTest.from_file('../app.py').run()
        at.text_area(key='source').set_value('Complaint A').run()
        at.radio(key='workflow').set_value('Final response').run()
        at.text_area(key='source').set_value('Complaint B').run()
        at.text_area(key='findings').set_value('Records reviewed; concern remains unresolved.').run()
        at.button(key='preview').click().run()
        self.assertFalse(at.exception)
        at.radio(key='workflow').set_value('Acknowledge complaint').run()
        self.assertEqual(at.text_area(key='source').value, 'Complaint A')
        next(b for b in at.button if b.label == 'Clear this pathway').click().run()
        self.assertEqual(at.text_area(key='source').value, '')
        at.radio(key='workflow').set_value('Final response').run()
        self.assertEqual(at.text_area(key='source').value, 'Complaint B')


class ProviderTests(unittest.TestCase):
    def test_free_provider_uses_configured_endpoint_key_and_model(self):
        from unittest.mock import patch, MagicMock
        config = {'GROQ_API_KEY': 'groq-test', 'FREELLMAPI_BASE_URL': 'https://example.test/v1',
                  'FREELLMAPI_API_KEY': 'free-test', 'FREELLMAPI_MODEL': 'free-model'}
        result = MagicMock()
        result.choices[0].finish_reason = 'stop'
        result.choices[0].message.content = 'Dear patient, thank you for writing.'
        with patch('streamlit.secrets', config), patch('groq.Groq') as factory:
            factory.return_value.__enter__.return_value.post.return_value = result
            at = AppTest.from_file('../app.py').run()
            at.selectbox(key='provider').select('Free LLM API').run()
            at.text_area(key='source').set_value('My appointment was cancelled.').run()
            at.button(key='generate').click().run()
            self.assertFalse(at.exception)
            self.assertTrue(at.success)
            self.assertEqual(factory.call_args.kwargs['base_url'], config['FREELLMAPI_BASE_URL'])
            self.assertEqual(factory.call_args.kwargs['api_key'], 'free-test')
            request = factory.return_value.__enter__.return_value.post.call_args
            self.assertEqual(request.args[0], '/chat/completions')
            self.assertEqual(request.kwargs['body']['model'], 'free-model')
            at.selectbox(key='provider').select('Groq').run()
            self.assertEqual(at.text_area(key='draft_editor').value, result.choices[0].message.content)

    def test_missing_free_config_does_not_call_provider(self):
        from unittest.mock import patch
        with patch('streamlit.secrets', {}), patch('groq.Groq') as factory:
            at = AppTest.from_file('../app.py').run()
            at.selectbox(key='provider').select('Free LLM API').run()
            at.text_area(key='source').set_value('My complaint').run()
            at.button(key='generate').click().run()
            self.assertFalse(at.exception)
            self.assertTrue(at.error)
            factory.assert_not_called()


if __name__ == '__main__':
    unittest.main()
