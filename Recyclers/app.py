import os
import time
import streamlit as st
from google import genai
from google.genai import types, errors

st.set_page_config(page_title="My Chatbot", page_icon="🤖")
st.title("🤖 My Chatbot")

SYSTEM_PROMPT = "You are a helpful and friendly chatbot assistant."
MODELS = ["gemini-3.8-flash", "gemini-3.8-flash-lite"]  # primary, then fallback


def generate_with_retry(client, contents, config, status, retries=2):
    last_error = None
    for model in MODELS:
        for attempt in range(retries):
            try:
                status.update(label=f"Trying {model} (attempt {attempt + 1})...")
                return client.models.generate_content(
                    model=model, contents=contents, config=config
                )
            except errors.ServerError as e:  # 5xx, e.g. 503
                last_error = e
                if attempt < retries - 1:
                    time.sleep(2)
            except errors.ClientError as e:  # 4xx, e.g. 404 bad model, 429 rate limit
                last_error = e
                break  # retrying won't help; move to the next model
            except Exception as e:  # timeouts, network problems
                last_error = e
                break
    raise RuntimeError(f"All models failed. Last error: {last_error}")


# Key from sidebar, falling back to an environment variable if set
api_key = st.sidebar.text_input("Gemini API Key", type="password") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.warning("Please paste your Gemini API Key in the sidebar to start chatting.")
    st.stop()

client = genai.Client(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Gemini uses "model" instead of "assistant" for the bot's role
    contents = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"])],
        )
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = generate_with_retry(
                    client,
                    contents,
                    types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.7,
                        max_output_tokens=1000,
                    ),
                )
                reply = response.text
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Error: {e}")

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()
