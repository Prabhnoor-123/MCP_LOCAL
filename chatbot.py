import streamlit as st
import openai
import asyncio
from fastmcp import Client
from config import settings
import json

# Azure OpenAI setup
client = openai.AzureOpenAI(
    api_key=settings.AZURE_OPENAI_KEY_LLM,
    api_version=settings.AZURE_OPENAI_API_VERSION_LLM,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
)

MCP_URL = "http://127.0.0.1:8000/mcp"

async def extract_result(response):
    for item in response:
        if hasattr(item, 'text'):
            try:
                parsed = json.loads(item.text)
                # If it's a dict with a message, return it
                if isinstance(parsed, dict) and "message" in parsed:
                    return parsed
                # If it's a list, return the list
                if isinstance(parsed, list):
                    return parsed
                # If it's a string that looks like a list, parse it
                if isinstance(parsed, str) and parsed.strip().startswith("["):
                    return json.loads(parsed)
            except Exception:
                continue
    return None

async def call_mcp_tool(tool, input_data={}):
    async with Client(MCP_URL) as client:
        response = await client.call_tool(tool, input_data)
        return await extract_result(response)

st.title("📝 Registration Chatbot")

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

if st.button("🔄 Restart Chat"):
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
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM Error: {e}"

# Bot messages
if st.session_state.step == 0:
    bot_msg = ask_llm("Greet the user and ask for their name.")
    st.session_state.messages.append(("bot", bot_msg))
    st.session_state.step = 1

# Display chat messages
for sender, msg in st.session_state.messages:
    if sender == "bot":
        st.markdown(f"**🤖 Bot:** {msg}")
    else:
        st.markdown(f"**🧑 You:** {msg}")

# Step 1: Ask for name
if st.session_state.step == 1:
    name = st.text_input("Your name:", key="name_input")
    if name:
        st.session_state.name = name
        st.session_state.messages.append(("user", name))
        bot_msg = ask_llm(f"The user's name is {name}. Ask for their email.")
        st.session_state.messages.append(("bot", bot_msg))
        st.session_state.step = 2
        st.rerun()

# Step 2: Ask for email
elif st.session_state.step == 2:
    email = st.text_input("Your email:", key="email_input").strip().replace("'", "")
    if email:
        st.session_state.email = email
        st.session_state.messages.append(("user", email))
        bot_msg = ask_llm(f"The user's email is {email}. Ask for their date of birth in YYYY-MM-DD format.")
        st.session_state.messages.append(("bot", bot_msg))
        st.session_state.step = 3
        st.rerun()

# Step 3: Ask for DOB and register
elif st.session_state.step == 3:
    dob = st.text_input("Your date of birth (YYYY-MM-DD):", key="dob_input")
    if dob:
        st.session_state.dob = dob
        st.session_state.messages.append(("user", dob))

        registration_data = {
            "reg": {
                "name": st.session_state.name,
                "email": st.session_state.email,
                "dob": st.session_state.dob
            }
        }

        async def register_user():
            try:
                async with Client(MCP_URL) as mcp_client:
                    result = await mcp_client.call_tool("register_user", registration_data)
                st.write("DEBUG MCP result:", result)  # Show result in Streamlit for debugging
                if isinstance(result, dict) and "registration successful" in result.get("message", "").lower():
                    msg = ask_llm("Thank the user for registering and confirm registration was successful.")
                    st.session_state.messages.append(("bot", msg))
                else:
                    st.session_state.messages.append(("bot", "❌ Registration failed."))
            except Exception as e:
                st.session_state.messages.append(("bot", f"❌ MCP Error: {e}"))

        asyncio.run(register_user())
        st.session_state.step = 4
        st.rerun()

# Step 4: Finished
elif st.session_state.step == 4:
    if st.button("✅ Register another user"):
        reset()

# Show all registrations
st.markdown("---")
st.header("📋 All Registrations")

if st.button("📂 Show all registrations"):
    async def get_all():
        try:
            async with Client(MCP_URL) as mcp_client:
                response = await mcp_client.call_tool("get_registrations", {})
            # response is likely a list of TextContent objects
            registrations = []
            for item in response:
                if hasattr(item, 'text'):
                    try:
                        parsed = json.loads(item.text)
                        if isinstance(parsed, list):
                            for row in parsed:
                                registrations.append({
                                    "Name": row.get("Name", ""),
                                    "Email": row.get("Email", ""),
                                    "DOB": row.get("DOB", "")
                                })
                    except Exception:
                        continue
            if registrations:
                st.table(registrations)
            else:
                st.info("No registrations found.")
        except Exception as e:
            st.error(f"Error fetching registrations: {e}")

    asyncio.run(get_all())