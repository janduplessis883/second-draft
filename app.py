import streamlit as st
from groq import Groq
import re

# Initialize the Groq client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Streamlit app configuration
st.set_page_config(page_title="Second-Draft", page_icon=":material/stylus_fountain_pen:", layout="centered")
st.logo("header.png", size="medium")
st.image("draft.gif")

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
mode = st.sidebar.radio("Select Mode:", ["Email Rewriter", "Complaint Responder"], index=0)
model = st.sidebar.selectbox("Model", MODEL_OPTIONS, index=2)

if mode == "Complaint Responder":
    tone = st.sidebar.radio("Select the tone of the email:", ("Formal", "Casual", "Neutral"), index=0, disabled=True)
else:
    tone = st.sidebar.radio("Select the tone of the email:", ("Formal", "Casual", "Neutral"), index=1)
st.sidebar.divider()
human = st.sidebar.checkbox("Apply human writing style", value=True)

explain_changes = False
if mode == "Complaint Responder":
    explain_changes = st.sidebar.checkbox("Explain changes", value=False, disabled=True)
elif mode == "Email Rewriter":
    explain_changes = st.sidebar.checkbox("Explain changes", value=True)

date = st.date_input("Select today's date:", value='today', format='DD-MM-YYYY')

email = st.text_area("Paste email:", height=250, placeholder="Paste your email here...")
complaint_specific_response = ""
if mode == "Complaint Responder":
    complaint_specific_response = st.text_area("Complaint Response:", height=200, placeholder="If responding to a complaint, specify any particular points to address here...")

HUMAN_WRITING_GUIDELINES = """
Revise your writing to read naturally, like something a thoughtful human would write. Focus on clarity, flow, and tone. Apply the following rules:
⸻
1. Punctuation
	•	Avoid em-dashes: Replace with periods or coordinating conjunctions (e.g., "and," "but").
	•	Limit semicolons: Only use when mimicking intentional pause or hesitation. Favor shorter, punchier sentences.
	•	Use colons sparingly: Only before clear, necessary lists or to emphasize contrast.
	•	Remove ellipses: Only allow when mimicking natural speech patterns or hesitation in casual dialogue.
⸻
2. Language & Word Choice
	•	Cut hedging phrases: Eliminate or rewrite around "however," "it's worth noting," "in conclusion," etc. Be direct.
	•	Ditch formality: Replace stiff words like "utilize," "ascertain," "therein" with simple alternatives like "use," "find out," "there."
	•	Use contractions in informal writing: Say "don't" instead of "do not" unless the tone is highly formal.
	•	Rephrase repetitive terms: If a word shows up more than once in close proximity, swap in a synonym or restructure the sentence.
⸻
3. Style & Tone
	•	Vary sentence lengths: Mix short and mid-length sentences. Avoid overly long, complex structures.
	•	Allow minor imperfections: Fragments, unfinished thoughts, or casual transitions are okay in conversational or informal text.
	•	Preserve the core message: Don't rewrite meaning—just improve delivery.
	•	Match the tone to the audience. This email should have a {tone} tone.
	•	Avoid filler: Cut empty phrases or redundant transitions. Get to the point.
⸻
4. Flow & Readability
	•	Break up dense text: Use paragraph breaks to improve scanability and highlight key ideas.
	•	Highlight key actions or facts: Don't bury important information under layers of explanation.
	•	Avoid robotic structure: Vary sentence openings. Use natural rhythms.
⸻
Before and After Example
	•	Before:
"The results — though preliminary — suggest success; however, it's worth noting limitations."
	•	After:
"The preliminary results suggest success. But there are still some limitations to address."

Use British English spelling.
"""
EXPLAIN_PROMPT = "After you have re-written the email, write a paragraph explaining the changes you have made and why you made them."
NO_EXPLAIN_PROMPT = "No need to explain the changes you made."

submit = st.button("Rewrite Email", type="primary")

base_prompt = ""
if mode == "Email Rewriter":
    base_prompt = "Rewrite the following email to improve clarity, grammar, and professional tone. Keep the message concise, preserve all key details, and avoid adding new information. If any sentences are ambiguous, rephrase them for precision."
elif mode == "Complaint Responder":
    base_prompt = f"""
        Goal: Generate a formal, comprehensive, and professional email response from an NHS Practice Manager to any patient complaint, adhering strictly to the NHS complaints procedure and MDU best-practice guidance (March 14, 2025).

Output Requirement: The response must be a stand-alone, complete, and formatted email.

Context and Placeholders (Use these exactly):

Surgery Name: SURGERY NAME

Surgery Address: [SURGERY NAME AND ADDRESS]

Surgery Email: [SURGERY EMAIL]

Telephone Number: [TELEPHONE NUMBER]

Date: Current date

Patient Salutation: Dear TITLE PATIENT, (Use 'TITLE PATIENT' as the name placeholder if unknown)

Practice Manager Name: PRACTICE MANAGER NAME

Practice Manager Email: PRACTICE MANAGER EMAIL

Practice Manager Role: Practice Manager

Instructions and Structure:

The final output must be a single, cohesive email text, formatted into professional paragraphs, covering all required elements in the order below:

1. Header and Contact Information

Start with the surgery's full contact block: Address, Email, Telephone, and Date.

Follow with the salutation: Dear TITLE PATIENT,

2. Opening and Introduction

Acknowledgement (1–2 sentences): Acknowledge receipt of the complaint (mentioning the date received, if possible). Express sympathy or regret for the need to complain. Confirm the purpose is to formally address the concerns.

Introduction: State your name (PRACTICE MANAGER NAME) and your exact role (Practice Manager) at the surgery.

Investigation: State that you have fully investigated the points raised, referencing the clinical and administrative records as necessary.

Tone: Empathetic, professional, and in the first person ("I").

3. Factual Chronology (If Applicable)

If the complaint relates to a specific interaction (e.g., appointment, phone call, visit), provide a concise, factual summary of the events using the information provided in the "Practice Manager's Factual Context/Explanations" input.

If memory-based, state: "per my usual practice". If referencing notes, quote them or state: "The contemporaneous notes record..."

4. Point-by-Point Response and Apology

Systematically address every specific concern identified in the "Patient Complaint Email Text" input.

For each concern:

Quote or clearly paraphrase the patient's specific issue.

Provide a direct, factual answer, explanation, or resolution using the information from the "Practice Manager's Factual Context/Explanations" input.

Reflect on the impact of the event on the patient.

Apology (Where Appropriate): Embed a sincere apology for any distress, inconvenience, or identified service shortfall.

Crucial Legal Note: State that the expression of regret for distress or inconvenience is not an admission of negligence or liability, but a genuine expression of sympathy (referencing the principle of the Compensation Act 2006 without naming the Act).

Avoid: "I am sorry you feel..."

5. Actions, Learning, and Review

Detail any specific actions taken or planned to remedy the patient's immediate issue and prevent recurrence (the "learning points").

Highlight any existing good practice that was upheld or confirmed during the review.

6. Confidentiality Note (If Third-Party Complaint)

If the complaint involves a third party (e.g., a relative, neighbour, or friend), include a paragraph stating that, due to patient confidentiality, the surgery cannot discuss or act on the care of the third party based on the complainant's information, and the patient themselves must contact the surgery. Omit this section if the complaint only concerns the patient themselves.

7. Offer to Meet

Offer an opportunity to meet or speak further: "I would be happy to meet you to discuss this further if you feel any of your concerns remain unresolved."

8. Sign-off and Escalation

Sign-off: Use a professional closing (e.g., "Very best wishes").

Escalation Text (Must be quoted verbatim): Include the full required text detailing the Parliamentary and Health Service Ombudsman (PHSO) as the next recourse, including the website and phone number.

Signature Block: Include [PRACTICE MANAGER NAME], Practice Manager, [SURGERY NAME], and [PRACTICE MANAGER EMAIL].

Style and Format Rules:

Maximum length: Two pages (concise yet thorough).

Use British English (UK) spelling.

Address the patient as "you" throughout.

Use plain English; spell out all medical terms the first time (then abbreviate if common).

Do not use any internal dividers (e.g., '---') within the email body. Do not use <h1>, <h2> or <h3> in your response only use **bold** to empheize content.

Maintain professionalism; do not criticise colleagues.

Ensure the final email flows well as a single, formal letter.

        """


# Apply mode-specific logic
if mode == "Email Rewriter":
    if human:
        base_prompt += f" {HUMAN_WRITING_GUIDELINES}"
    else:
        base_prompt += f" This email should have a {tone} tone."
elif mode == "Complaint Responder":
    # Complaint responses should always be formal and professional
    base_prompt += " This response should be formal, professional, and follow NHS complaint handling standards."

if explain_changes:
    base_prompt += f" \n{EXPLAIN_PROMPT}"
else:
    base_prompt += f" \n{NO_EXPLAIN_PROMPT}"

prompt = ""
if mode == "Email Rewriter":
    prompt = f"{base_prompt} Here is the email: \n<email>\n{email}\n</email>"
elif mode == "Complaint Responder":
    prompt = f"{base_prompt} Patient Complaint Email Text: <email>\n{email}\n</email> Practice Manager's Factual Context/Explanations: <context>\n{complaint_specific_response}\n</context>"

if submit:
    with st.spinner("Shining your email...", show_time=True):
        response = ask_groq(prompt, model=model)
        st.write("Your revised email:")
        with st.container(border=True):
            # extract reasoning separately if you still want to make it optional
            if response:
                match = re.search(r"<think>(.*?)</think>", response, flags=re.DOTALL)
                reasoning = match.group(1).strip() if match else None
                visible_text = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
            else:
                reasoning = None
                visible_text = ""
            if reasoning:
                with st.expander("Show hidden reasoning", icon=":material/neurology:"):
                    st.markdown(f"{reasoning}")
            st.markdown(visible_text)
            st.toast("Email Spun !!", icon=":material/check_circle:", duration=5)
