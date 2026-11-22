    with st.chat_message("assistant"):
        with st.status("Thinking...", expanded=False) as status:
            try:
                response = generate_with_retry(
                    client,
                    contents,
                    types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.7,
                        max_output_tokens=1000,
                    ),
                    status,
                )
                status.update(label="Done", state="complete")
                reply = response.text
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                status.update(label="Failed", state="error")
                st.error(f"Error: {e}")
