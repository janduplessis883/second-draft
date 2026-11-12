"""Second-Draft: practice correspondence with session-only editable drafts."""
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import streamlit as st
from groq import Groq, APIConnectionError, APIStatusError, AuthenticationError, RateLimitError
from groq.types.chat import ChatCompletion
from prompts import WORKFLOWS, SYSTEM_PROMPT, build_prompt

st.set_page_config(page_title='Second-Draft', page_icon=':material/stylus_fountain_pen:', layout='centered')


def save_field(field, widget):
    st.session_state[f'{field}_{st.session_state.workflow}'] = st.session_state[widget]


def clear_current():
    mode = st.session_state.workflow
    for field, widget in [('source', 'source'), ('findings', 'findings'), ('draft', 'draft_editor'), ('escalation', 'escalation')]:
        st.session_state[f'{field}_{mode}'] = ''
        st.session_state[widget] = ''
    st.session_state.pop(f'prompt_{mode}', None)
    st.session_state.pop(f'generated_from_{mode}', None)


def secret(name):
    try:
        return str(st.secrets.get(name, '')).strip()
    except (FileNotFoundError, KeyError):
        return ''


st.session_state.setdefault('workflow', WORKFLOWS[0])
with st.sidebar:
    st.header('Letter workspace')
    mode = st.radio('Choose a pathway', WORKFLOWS, key='workflow')
    st.divider()
    provider = st.selectbox('Language model provider', ['Groq', 'Free LLM API'], key='provider')
    if provider == 'Groq':
        model = st.selectbox('Groq model', ['openai/gpt-oss-120b', 'qwen/qwen3-32b',
                             'moonshotai/kimi-k2-instruct-0905', 'meta-llama/llama-4-maverick-17b-128e-instruct'], key='model')
        st.caption('Availability depends on your Groq account. If a model is unavailable, select another.')
    else:
        model = secret('FREELLMAPI_MODEL')
        st.caption(f'Configured model: {model}' if model else 'Set FREELLMAPI_MODEL in secrets.toml.')
    st.button('Clear this pathway', on_click=clear_current, icon=':material/delete:')
    st.caption('Inputs and drafts are held in this browser session. Download anything you need to keep before closing it.')

# Restore per-pathway values before rendering shared widget keys.
if st.session_state.get('_previous_mode') != mode:
    for field, widget in [('source', 'source'), ('findings', 'findings'), ('draft', 'draft_editor'), ('escalation', 'escalation')]:
        st.session_state[widget] = st.session_state.get(f'{field}_{mode}', '')
    st.session_state['_previous_mode'] = mode

st.title('Second-Draft', anchor=False)
st.caption('Thoughtful correspondence for Stanhope Mews Surgery')
st.subheader(mode, anchor=False)
descriptions = {
    'Acknowledge complaint': 'Acknowledge concerns with empathy and explain what happens next.',
    'Final response': 'Respond to each concern using the evidence and findings from your investigation.',
    'Email rewriter': 'Improve clarity and tone while keeping your meaning and key details.',
}
st.write(descriptions[mode])
letter_date = st.date_input('Letter date', value=datetime.now(ZoneInfo('Europe/London')).date(), format='DD/MM/YYYY', key='letter_date')
if letter_date is None:
    st.error('Choose a letter date.')
    st.stop()

tone, explain = 'Professional', False
if mode == 'Email rewriter':
    tone = st.segmented_control('Tone', ['Professional', 'Warm', 'Neutral'], default='Professional', key='tone') or 'Professional'
    explain = st.checkbox('Include a separate editorial note', key='explain')
with st.container(border=True):
    st.text_area('Source email' if mode == 'Email rewriter' else 'Original patient complaint',
                 height=240, key='source', on_change=save_field, args=('source', 'source'),
                 placeholder='Paste the complete email here…')
    if mode == 'Final response':
        st.text_area('Investigation findings', height=220, key='findings', on_change=save_field,
                     args=('findings', 'findings'), placeholder='Address each concern. Include evidence, conclusions, unresolved points, apologies, actions, owners and timescales where known.')
        st.text_area('Practice-approved escalation wording (optional)', key='escalation',
                     on_change=save_field, args=('escalation', 'escalation'),
                     help='Paste the current wording from your complaints procedure. It will be included verbatim.')
        if not st.session_state.get('escalation', '').strip():
            st.caption('Escalation wording is not supplied. Add and verify it before sending a final response.')

st.caption(f'Generating a draft sends the source text to {provider}. Use only information approved for this service and remove unnecessary patient identifiers. Previewing a prompt makes no API call.')
with st.container(horizontal=True):
    generate = st.button('Generate draft', type='primary', icon=':material/edit_document:', key='generate')
    preview = st.button('Preview prompt', icon=':material/code:', key='preview')


current_prompt = None
try:
    current_prompt = build_prompt(mode, letter_date, st.session_state.source,
        st.session_state.get('findings', '') if mode == 'Final response' else '', tone, explain,
        st.session_state.get('escalation', '') if mode == 'Final response' else '')
except ValueError as error:
    if generate or preview:
        st.error(str(error))

if (generate or preview) and current_prompt:
    st.session_state[f'prompt_{mode}'] = current_prompt
    if generate:
        key_name = 'GROQ_API_KEY' if provider == 'Groq' else 'FREELLMAPI_API_KEY'
        key = secret(key_name)
        base_url = secret('FREELLMAPI_BASE_URL') if provider == 'Free LLM API' else ''
        missing = [name for name in ([key_name] if provider == 'Groq' else
                   [key_name, 'FREELLMAPI_BASE_URL', 'FREELLMAPI_MODEL']) if not secret(name)]
        if missing:
            st.error(f'Add {", ".join(missing)} to .streamlit/secrets.toml to generate drafts. Prompt preview is available without it.')
        else:
            try:
                with st.spinner('Drafting your letter…'):
                    # Both endpoints use the OpenAI chat/completions protocol.
                    with Groq(api_key=key, timeout=60.0, max_retries=0,
                              **({'base_url': base_url} if base_url else {})) as client:
                        messages = [
                            {'role': 'system', 'content': SYSTEM_PROMPT},
                            {'role': 'user', 'content': current_prompt},
                        ]
                        if provider == 'Free LLM API':
                            # Groq's convenience method adds its own /openai/v1 prefix.
                            # Use the configured API root directly for compatible providers.
                            result = client.post('/chat/completions',
                                body={'model': model, 'messages': messages}, cast_to=ChatCompletion)
                        else:
                            result = client.chat.completions.create(model=model, messages=messages)
                    if not result.choices or result.choices[0].finish_reason != 'stop':
                        raise ValueError('The model did not return a complete draft. Try again or choose another model.')
                    text = result.choices[0].message.content or ''
                    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
                    if not text or '<think>' in text:
                        raise ValueError('No complete letter was returned. Try again or choose another model.')
                    st.session_state[f'draft_{mode}'] = text
                    st.session_state.draft_editor = text
                    st.session_state[f'generated_from_{mode}'] = current_prompt
                    st.success('Draft ready to review.')
            except AuthenticationError:
                st.error(f'{provider} could not authenticate. Check the configured API key.')
            except RateLimitError:
                st.error(f'{provider} is temporarily rate limited. Wait and try again.')
            except APIConnectionError:
                st.error(f'Could not connect to {provider}. Check the connection and configured base URL, then try again.')
            except APIStatusError:
                st.error(f'{provider} could not complete this request. Check the configured model or try again.')
            except ValueError as error:
                st.error(str(error))

saved_prompt = st.session_state.get(f'prompt_{mode}')
if saved_prompt:
    with st.expander('Drafting prompt', expanded=preview):
        st.code(SYSTEM_PROMPT + '\n\n' + saved_prompt, language='text', wrap_lines=True)
        st.download_button('Download prompt', SYSTEM_PROMPT + '\n\n' + saved_prompt,
                           file_name='second-draft-prompt.txt', mime='text/plain', key='download_prompt')

if st.session_state.get(f'draft_{mode}'):
    st.divider()
    st.subheader('Review and edit', anchor=False)
    if st.session_state.get(f'generated_from_{mode}') != current_prompt:
        st.warning('The inputs or drafting settings have changed since this draft was created. Review it or generate a replacement.')
    st.caption('Check facts, patient details, dates, commitments and any escalation wording before sending. Generating again replaces this pathway’s draft.')
    edited = st.text_area('Editable draft', height=480, key='draft_editor', on_change=save_field, args=('draft', 'draft_editor'))
    st.download_button('Download edited letter', edited, file_name=f'{mode.lower().replace(" ", "-")}-{letter_date.isoformat()}.txt',
                       mime='text/plain', icon=':material/download:', key='download_letter')
    st.caption(f'{len(edited.split())} words · Select and copy the text above to paste it into your email client.')
