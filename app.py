import os
import hmac
import streamlit as st
from openai import OpenAI

title=os.getenv("TITLE", "LLM Platform Chat")

st.set_page_config(
    page_icon=":robot_face:",
    page_title=title,
    layout="centered",
    initial_sidebar_state="collapsed"
)

client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:8080/v1/"),
    api_key=os.getenv("OPENAI_API_KEY", "-"))

def check_password():    
    password = os.getenv("PASSWORD")

    if not password:
        return True
    
    if st.session_state.get("password_correct", False):
        return True
        
    # if hmac.compare_digest(str(cookies["password"] or ""), password):
    #     st.session_state["password_correct"] = True
    #     return True
    
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], password):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            
            # cookies["password"] = password
            # cookies.save()
        else:
            st.session_state["password_correct"] = False

    st.text_input("Password", type="password", on_change=password_entered, key="password")
    
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")

    return False

if not check_password():
    st.stop()

@st.cache_resource
def get_models():
    models = [m for m in sorted(client.models.list(), key=lambda m: m.id)
        if all(x not in m.id for x in ["embed", "tts", "whisper", "dall-e", "flux"])]
    
    default = os.environ.get('MODEL')
    
    if default:
        list = [m.id for m in models]
        
        if default in list:
            index = list.index(default)
            models.insert(0, models.pop(index))
    
    return models

def clear_chat_history():
    st.session_state.messages = []

with st.sidebar:
    st.title(title)
    
    st.selectbox("Model", get_models(), key="model", placeholder="Select model", format_func=lambda m: m.id, index=0)
    st.text_area("System Prompt", "", key="system")
    
    st.button('Clear chat history', on_click=clear_chat_history)


if "messages" not in st.session_state:
    clear_chat_history()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Message " + title):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        messages = []

        if st.session_state.system:
            messages.append({"role": "system", "content": st.session_state.system})
        
        for m in st.session_state.messages:
            messages.append({"role": m["role"], "content": m["content"]})

        stream = client.chat.completions.create(
            model=st.session_state.model.id,
            messages=messages,
            stream=True,
        )

        response = st.write_stream(stream)
    
    st.session_state.messages.append({"role": "assistant", "content": response})