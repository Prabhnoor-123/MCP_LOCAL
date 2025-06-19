import streamlit as st
import requests
import openai
from config import settings

# Azure OpenAI setup
client = openai.AzureOpenAI(
    api_key=settings.AZURE_OPENAI_KEY_LLM,
    api_version=settings.AZURE_OPENAI_API_VERSION_LLM,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
)

REGISTER_URL = settings.REGISTER_URL
LIST_URL = settings.LIST_URL

st.title("Registration Chatbot (Azure OpenAI)")

if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.name = ""
    st.session_state.email = ""
    st.session_state.dob = ""
    st.session_state.messages = []

def reset():
    st.session_state.step = 0
    st.session_state.name = ""
    st.session_state.email = ""
    st.session_state.dob = ""
    st.session_state.messages = []

if st.button("Restart Chat"):
    reset()

def ask_llm(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant for user registration."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=100
        )
        bot_reply = response.choices[0].message.content
    except Exception as e:
        return f"LLM Error: {e}"

# Chatbot logic
if st.session_state.step == 0:
    bot_msg = ask_llm("Greet the user and ask for their name.")
    st.session_state.messages.append(("bot", bot_msg))
    st.session_state.step = 1

for sender, msg in st.session_state.messages:
    if sender == "bot":
        st.markdown(f"**🤖 Bot:** {msg}")
    else:
        st.markdown(f"**🧑 You:** {msg}")

if st.session_state.step == 1:
    name = st.text_input("Your name:", key="name_input")
    if name:
        st.session_state.name = name
        st.session_state.messages.append(("user", name))
        bot_msg = ask_llm(f"The user's name is {name}. Ask for their email.")
        st.session_state.messages.append(("bot", bot_msg))
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    email = st.text_input("Your email:", key="email_input")
    if email:
        st.session_state.email = email
        st.session_state.messages.append(("user", email))
        bot_msg = ask_llm(f"The user's email is {email}. Ask for their date of birth in YYYY-MM-DD format.")
        st.session_state.messages.append(("bot", bot_msg))
        st.session_state.step = 3
        st.rerun()

elif st.session_state.step == 3:
    dob = st.text_input("Your date of birth (YYYY-MM-DD):", key="dob_input")
    if dob:
        st.session_state.dob = dob
        st.session_state.messages.append(("user", dob))
        # Send registration
        payload = {
            "name": st.session_state.name,
            "email": st.session_state.email,
            "dob": st.session_state.dob
        }
        try:
            response = requests.post(REGISTER_URL, json=payload)
            if response.status_code == 200:
                bot_msg = ask_llm("Thank the user for registering and confirm registration was successful.")
                st.session_state.messages.append(("bot", bot_msg))
            else:
                st.session_state.messages.append(("bot", "Registration failed."))
        except Exception as e:
            st.session_state.messages.append(("bot", f"Error: {e}"))
        st.session_state.step = 4
        st.rerun()

elif st.session_state.step == 4:
    if st.button("Register another user"):
        reset()

st.markdown("---")
st.header("All Registrations")
if st.button("Show all registrations"):
    try:
        registrations = requests.get(LIST_URL).json()
        if registrations:
            st.table(registrations)
        else:
            st.info("No registrations found.")
    except Exception as e:
        st.error(f"Error: {e}")