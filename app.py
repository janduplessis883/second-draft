import streamlit as st
from groq import Groq
import re

# Initialize the Groq client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Streamlit app configuration
st.set_page_config(page_title="Second-Draft", page_icon=":material/stylus_fountain_pen:", layout="centered")

st.header("Second-Draft :material/stylus_fountain_pen:")

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
mode = st.sidebar.radio("Select Mode:", ["Email Rewriter", "Acknowledge Complaint", "Outcome of Investigation"], index=0)
model = st.sidebar.selectbox("Model", MODEL_OPTIONS, index=3)
send_to_llm = st.sidebar.toggle("Send to LLM", value=True, help="When enabled, the prompt will be sent to the LLM for processing. When disabled, only the prompt will be displayed.")

if mode in ["Acknowledge Complaint", "Outcome of Investigation"]:
    tone = st.sidebar.radio("Select the tone of the email:", ("Formal", "Casual", "Neutral"), index=0, disabled=True)
else:
    tone = st.sidebar.radio("Select the tone of the email:", ("Formal", "Casual", "Neutral"), index=1)
st.sidebar.divider()
human = st.sidebar.checkbox("Apply human writing style", value=True)

explain_changes = False
if mode in ["Acknowledge Complaint", "Outcome of Investigation"]:
    explain_changes = st.sidebar.checkbox("Explain changes", value=False, disabled=True)
elif mode == "Email Rewriter":
    explain_changes = st.sidebar.checkbox("Explain changes", value=True)

date = st.date_input("Select today's date:", value='today', format='DD-MM-YYYY')

# Mode-specific inputs
if mode == "Acknowledge Complaint":
    email = st.text_area("Paste the complaint email:", height=250, placeholder="Paste the patient's complaint email here...")
    complaint_specific_response = ""
elif mode == "Outcome of Investigation":
    email = st.text_area("Paste the original complaint email:", height=200, placeholder="Paste the original complaint email here for context...")
    complaint_specific_response = st.text_area("Outcome of Investigation:", height=200, placeholder="Paste the outcome of your investigation here. Address all issues raised in the complaint...")
else:  # Email Rewriter
    email = st.text_area("Paste email:", height=250, placeholder="Paste your email here...")
    complaint_specific_response = ""

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

button_label = ":material/mail_asterisk: Rewrite Email" if send_to_llm else ":material/prompt_suggestion: Generate Prompt"
submit = st.button(button_label, type="primary")

base_prompt = ""
if mode == "Email Rewriter":
    base_prompt = "Rewrite the following email to improve clarity, grammar, and professional tone. Keep the message concise, preserve all key details, and avoid adding new information. If any sentences are ambiguous, rephrase them for precision."
elif mode == "Acknowledge Complaint":
    base_prompt = f"""
Goal: Generate a formal acknowledgement email from an NHS Practice Manager to a patient who has submitted a complaint.
Output Requirement: The response must be a stand-alone, complete, and formatted email.
Context and Placeholders (Use these exactly):

Surgery Name: Stanhope Mews Surgery
Surgery Address: 7 Stanhope Mews West, London, SW7 5RB
Surgery Email: stanhope.mews@nhs.net
Telephone Number: Tel: 020 7835 040

Date: Current date

Patient Salutation: Dear (Use 'TITLE PATIENT' as the name placeholder if not listed in the complaint)

Instructions and Structure:

The final output must be a single, cohesive acknowledgement email, formatted into professional paragraphs, covering all required elements in the order below:

1. Header and Contact Information
Start with the surgery's full contact block: Address, Email, Telephone, and Date.
Follow with the salutation: Dear TITLE PATIENT,

2. Acknowledgement of Receipt
Acknowledge receipt of the complaint with the date received (use the date provided or state "your recent complaint").
Express sincere apology for any inconvenience and distress caused by the issues raised.
Be empathetic and sincere in tone - avoid generic or dismissive language.

Some pointers regarding saying we are sorry:
Use First-Person Accountability: Avoid passive or "corporate" phrasing (e.g., "It is regretted that..."). Use "I" and "We" to take direct ownership. Use warm, natural language rather than stiff, defensive jargon.
Contextualize without Excusing: Explain the "why" behind the incident. If a task was difficult or a process is complex, mention it—not as an excuse, but to provide the user with a full picture of the event.
Simulate "Body Language" via Tone: Since this is text, your "posture" is your tone. Avoid sounding crowded or intimidating. Keep the focus on the recipient’s experience. Keep the message concise and focused rather than burying the apology in a "wall of text."
Initiate a Dialogue: Do not treat the email as a closing statement. Invite the recipient to ask questions, share their perspective, or request a meeting with a different staff member if they prefer
Prioritize Transparency: Operate under the principle that a sincere, timely apology reduces long-term friction. Do not omit an apology out of fear of "admitting fault"; focus on the human impact of what occurred.

3. Summary of Complaint (For Clarity)
Provide a brief, neutral summary of the key issues raised in the complaint to demonstrate understanding.
Keep this concise - 2-3 sentences maximum.

4. Investigation Process
Explain that you will be conducting a thorough internal investigation into the matters raised.
State that you will respond with the outcome of the investigation within 20 working days, as per the practice's complaints procedure.
Clarify that no further information is needed from the patient at this time.

5. Offer of Contact
State that if the patient has any questions or concerns in the meantime, they should not hesitate to contact you.

6. Sign-off
Sign-off: Use a professional closing (e.g., "Yours sincerely,").
Signature Block:
Practice Manager Name: Jan du Plessis
Practice Manager Email: jan.duplessis@nhs.net
Practice Manager Role: Practice Manager - Stanhope Mews Surgery

Style and Format Rules:
Keep the email concise - ideally one page.
Use British English (UK) spelling.
Address the patient as "you" throughout.
Use plain English and a warm, empathetic tone.
Do not use any internal dividers (e.g., '---') within the email body. Do not use <h1>, <h2> or <h3> in your response; only use **bold** to emphasize content if necessary.
Maintain professionalism and empathy throughout.
Ensure the final email flows well as a single, formal yet compassionate letter.
Use the Empathetic Resolution Framework when writing this email.
"""
elif mode == "Outcome of Investigation":
    base_prompt = f"""
Goal: Generate a formal, comprehensive, and professional email response from an NHS Practice Manager to a patient complaint, providing the outcome of the investigation and adhering strictly to the NHS complaints procedure and MDU best-practice guidance (March 14, 2025).
Output Requirement: The response must be a stand-alone, complete, and formatted email.
Context and Placeholders (Use these exactly):

Surgery Name: SURGERY NAME
Surgery Address: [SURGERY NAME AND ADDRESS
Surgery Email: [SURGERY EMAIL]
Telephone Number: [TELEPHONE NUMBER]

Date: Current date

Patient Salutation: Dear TITLE PATIENT, (Use 'TITLE PATIENT' as the name placeholder if unknown)

Practice Manager Name: Jan du Plessis
Practice Manager Email: jan.duplessis@nhs.net
Practice Manager Role: Practice Manager
Surgery: Stanhope Mews Surgery

Instructions and Structure:

The final output must be a single, cohesive email text, formatted into professional paragraphs, covering all required elements in the order below:

1. Header and Contact Information
Start with the surgery's full contact block: Stanhope Mews Surgery, 7 Stanhope Mews West, London, SW7 5RB, Tel: 020 7835 0400 and Date.
Follow with the salutation: Dear TITLE PATIENT,

2. Opening and Introduction
Acknowledgement (1–2 sentences): Acknowledge receipt of the complaint (mentioning the date received, if possible). Express sympathy or regret for the need to complain. Confirm the purpose is to formally address the concerns.
Investigation: State that you have fully investigated the points raised, referencing the clinical and administrative records as necessary.
Tone: Empathetic, professional, and in the first person ("I").

Some pointers regarding saying we are sorry:
Use First-Person Accountability: Avoid passive or "corporate" phrasing (e.g., "It is regretted that..."). Use "I" and "We" to take direct ownership. Use warm, natural language rather than stiff, defensive jargon.
Contextualize without Excusing: Explain the "why" behind the incident. If a task was difficult or a process is complex, mention it—not as an excuse, but to provide the user with a full picture of the event.
Simulate "Body Language" via Tone: Since this is text, your "posture" is your tone. Avoid sounding crowded or intimidating. Keep the focus on the recipient’s experience. Keep the message concise and focused rather than burying the apology in a "wall of text."
Initiate a Dialogue: Do not treat the email as a closing statement. Invite the recipient to ask questions, share their perspective, or request a meeting with a different staff member if they prefer
Prioritize Transparency: Operate under the principle that a sincere, timely apology reduces long-term friction. Do not omit an apology out of fear of "admitting fault"; focus on the human impact of what occurred.

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

Signature Block:
Sign-off: Use a professional closing (e.g., "Yours sincerely,").
Practice Manager Name: Jan du Plessis
Practice Manager Email: jan.duplessis@nhs.net
Practice Manager Role: Practice Manager - Stanhope Mews Surgery

Style and Format Rules:
Maximum length: Two pages (concise yet thorough).
Use British English (UK) spelling.
Address the patient as "you" throughout.
Use plain English; spell out all medical terms the first time (then abbreviate if common).
Do not use any internal dividers (e.g., '---') within the email body. Do not use <h1>, <h2> or <h3> in your response only use **bold** to empheize content.
Maintain professionalism; do not criticise colleagues.
Ensure the final email flows well as a single, formal letter.
DO NOT USE HEADINGS IN THE EMAIL, structure with paragraphs only.
Information about contacting the Ombudsman should be the last paragraph of the email folloed by Yours sincerely, Practice Manager's information.
Use the Empathetic Resolution Framework when writing this email.
"""


# Apply mode-specific logic
if mode == "Email Rewriter":
    if human:
        base_prompt += f" {HUMAN_WRITING_GUIDELINES}"
    else:
        base_prompt += f" This email should have a {tone} tone."
elif mode in ["Acknowledge Complaint", "Outcome of Investigation"]:
    # Complaint responses should always be formal and professional
    base_prompt += " This response should be formal, professional, and follow NHS complaint handling standards."

if explain_changes:
    base_prompt += f" \n{EXPLAIN_PROMPT}"
else:
    base_prompt += f" \n{NO_EXPLAIN_PROMPT}"

prompt = ""
if mode == "Email Rewriter":
    prompt = f"{base_prompt} Here is the email: \n<email>\n{email}\n</email>"
elif mode == "Acknowledge Complaint":
    prompt = f"{base_prompt} Patient Complaint Email Text: <email>\n{email}\n</email>"
elif mode == "Outcome of Investigation":
    prompt = f"{base_prompt} Patient Complaint Email Text: <email>\n{email}\n</email> Practice Manager's Factual Context/Explanations: <context>\n{complaint_specific_response}\n</context>"

if submit:
    with st.expander("View Full Prompt Sent to LLM", icon=":material/prompt_suggestion:", expanded=False):
        st.code(prompt, language="text", wrap_lines=True,)

    if send_to_llm:
        with st.spinner("Shining your email...", show_time=True):
            response = ask_groq(prompt, model=model)
            st.success("Your revised email is ready:")
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
                st.toast("Revised Email Ready.", icon="♥️", duration=5)
    else:
        st.info("LLM call skipped. Only prompt is displayed above.")
