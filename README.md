# Second-Draft

A Streamlit workspace for complaint acknowledgements, final patient responses, and email rewriting.

## Run

Use Python 3.10 or newer and install `requirements.txt`, then run:

```sh
streamlit run app.py
```

For generation, create `.streamlit/secrets.toml` (ignored by Git):

```toml
GROQ_API_KEY = "your-key"
```

Prompt previews work without credentials. Choose **Groq** or **Free LLM API** in the sidebar. Generation sends the supplied text only to the selected provider when you click **Generate draft**. Groq models remain selectable; Free LLM API uses the model configured in secrets:

```toml
FREELLMAPI_BASE_URL = "https://your-provider.example/v1"
FREELLMAPI_API_KEY = "your-key"
FREELLMAPI_MODEL = "your-model-name"
```

Use the provider's OpenAI-compatible API base URL (including its version path where required), rather than the full `/chat/completions` URL. The existing Groq SDK supplies the compatible chat-completion request format and bearer authentication for both providers. No automatic fallback sends content to a different provider.

## Drafting

- Acknowledgements use the supplied practice prompt in `prompts/acknowledgement.txt`, inserting the letter date and original complaint.
- Final responses require complaint text and investigation findings. Add current practice-approved escalation wording before sending; the model is instructed not to invent it.
- Rewriting preserves meaning and supports a separate optional editorial note. Remove that note before sending.
- Each pathway retains its own inputs and edited draft during the session. Downloads contain the current edited text. Generation replaces the current pathway's draft only on a complete successful response.
- Data is not written to application storage or a shared cache. Session state is temporary, not a permanent record. Text sent to the selected provider is subject to your configured provider and organisational arrangements.
- Review every letter before sending. Practice details, including the telephone number, reproduce the user-supplied acknowledgement prompt exactly; verify them before operational use.

## Verify

```sh
python -m unittest discover -s tests
```

Tests cover prompt construction, validation, mode switching, prompt preview without secrets, generation success, and preserving edits after a provider failure. Provider calls are mocked in tests; live model output quality and account-specific model availability require separate review.
