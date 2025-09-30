import streamlit as st
from groq import Groq
import re

# Initialize the Groq client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Streamlit app configuration
st.set_page_config(page_title="Second-Draft", page_icon=":material/stylus_fountain_pen:", layout="centered")
st.logo("header.png", size="medium")
st.image('header2.png')

# Simple function to get a response from Groq
def ask_groq(prompt: str, model: str = "meta-llama/llama-4-scout-17b-16e-instruct"):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
    )

    try:
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error getting response from Groq: {e}")
        return "Error: Could not get a response from Groq."

MODEL_OPTIONS = ["moonshotai/kimi-k2-instruct-0905", "meta-llama/llama-4-maverick-17b-128e-instruct", "qwen/qwen3-32b", "openai/gpt-oss-120b"]

st.sidebar.header("Settings")
model = st.sidebar.selectbox("Model", MODEL_OPTIONS, index=2)
tone = st.sidebar.radio("Select the tone of the email:", ("Formal", "Casual", "Neutral"), index=1)
st.sidebar.divider()
human = st.sidebar.checkbox("Apply human writing style", value=True)
explain_changes = st.sidebar.checkbox("Explain changes", value=True)

email = st.text_area("", height=300, placeholder="Paste your email here...", label_visibility="collapsed")

html_content = """<BR><BR><BR><img alt="Static Badge" src="https://img.shields.io/badge/github-janduplessis883-%234a83c0">"""
st.sidebar.html(html_content)

HUMAN_WRITING_GUIDELINES = """
Revise your writing to read naturally, like something a thoughtful human would write. Focus on clarity, flow, and tone. Apply the following rules:
⸻
1. Punctuation
	•	Avoid em-dashes: Replace with periods or coordinating conjunctions (e.g., “and,” “but”).
	•	Limit semicolons: Only use when mimicking intentional pause or hesitation. Favor shorter, punchier sentences.
	•	Use colons sparingly: Only before clear, necessary lists or to emphasize contrast.
	•	Remove ellipses: Only allow when mimicking natural speech patterns or hesitation in casual dialogue.
⸻
2. Language & Word Choice
	•	Cut hedging phrases: Eliminate or rewrite around “however,” “it’s worth noting,” “in conclusion,” etc. Be direct.
	•	Ditch formality: Replace stiff words like “utilize,” “ascertain,” “therein” with simple alternatives like “use,” “find out,” “there.”
	•	Use contractions in informal writing: Say “don’t” instead of “do not” unless the tone is highly formal.
	•	Rephrase repetitive terms: If a word shows up more than once in close proximity, swap in a synonym or restructure the sentence.
⸻
3. Style & Tone
	•	Vary sentence lengths: Mix short and mid-length sentences. Avoid overly long, complex structures.
	•	Allow minor imperfections: Fragments, unfinished thoughts, or casual transitions are okay in conversational or informal text.
	•	Preserve the core message: Don’t rewrite meaning—just improve delivery.
	•	Match the tone to the audience, this email should have a {tone} tone.
	•	Avoid filler: Cut empty phrases or redundant transitions. Get to the point.
⸻
4. Flow & Readability
	•	Break up dense text: Use paragraph breaks to improve scanability and highlight key ideas.
	•	Highlight key actions or facts: Don’t bury important information under layers of explanation.
	•	Avoid robotic structure: Vary sentence openings. Use natural rhythms.
⸻
Before and After Example
	•	Before:
“The results — though preliminary — suggest success; however, it’s worth noting limitations.”
	•	After:
“The preliminary results suggest success. But there are still some limitations to address.”
Let me summarize:
Please revise the following text to sound more natural, clear, and human.

Apply these specific rules:

Punctuation & Flow

Avoid em-dashes (—) and ellipses (...).

Limit semicolons (;) and colons (:). Favor shorter, punchier sentences.

Use paragraph breaks to improve readability.

Vary sentence length and openings.

Language & Tone

Cut hedging and formal phrases (e.g., "however," "in conclusion," "utilize," "ascertain"). Be direct.

Use contractions (e.g., "don't," "it's") unless the tone is highly formal.

Rephrase terms that repeat in close proximity.

Match the tone to the audience. This email should have a conversational tone.

Core Goal

Preserve the original meaning but significantly improve the clarity, flow, and tone. Get to the point.
Use British English spelling.
"""
EXPLAIN_PROMPT = "After you have re-written the email, write a paragraph explaining your the changed you have made and why you made them."
NO_EXPLAIN_PROMPT = "No need to explain the changes you made."

submit = st.button("Rewrite Email", type="primary")

base_prompt = "Rewrite the following email to improve clarity, grammar, and professional tone. Keep the message concise, preserve all key details, and avoid adding new information. If any sentences are ambiguous, rephrase them for precision."

if human:
    base_prompt += f" {HUMAN_WRITING_GUIDELINES}"
else:
    base_prompt += f" This email should have a {tone} tone."

if explain_changes:
    base_prompt += f" \n{EXPLAIN_PROMPT}"
else:
    base_prompt += f" \n{NO_EXPLAIN_PROMPT}"

prompt = f"{base_prompt} Here is the email: \n<email>\n{email}\n</email>"

if submit:
    with st.spinner("Shining your email...", show_time=True):
        response = ask_groq(prompt, model=model)
        st.write("Your revised email:")
        with st.container(border=True):
            # extract reasoning separately if you still want to make it optional
            match = re.search(r"<think>(.*?)</think>", response, flags=re.DOTALL)
            reasoning = match.group(1).strip() if match else None
            visible_text = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
            if reasoning:
                with st.expander("Show hidden reasoning", icon=":material/neurology:"):
                    st.markdown(f"{reasoning}")
            st.markdown(visible_text)
            st.toast("Email Spun !!", icon=":material/check_circle:", duration=5)
