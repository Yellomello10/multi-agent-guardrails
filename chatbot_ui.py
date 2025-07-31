import streamlit as st
import requests
import json

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000/invoke"

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Guardrails Chatbot", page_icon="🛡️")

st.title("🛡️ Multi-Agent Chatbot")
st.caption("This chatbot uses a router to delegate your request to a specialized agent.")

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Ask me to research a topic or write something. You can also upload an image."}
    ]

# --- UI Rendering ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- User Input Handling ---
# --- MODIFICATION: Replace URL input with a file uploader ---
col1, col2 = st.columns([3, 2])
with col1:
    prompt_input = st.text_input("Your message:", key="prompt_input", placeholder="e.g., What is this image about?")
with col2:
    uploaded_file = st.file_uploader("Upload an image (optional)", type=["png", "jpg", "jpeg"])

if st.button("Send", use_container_width=True):
    if prompt_input:
        # Display the user's prompt
        st.session_state.messages.append({"role": "user", "content": prompt_input})
        with st.chat_message("user"):
            st.markdown(prompt_input)
            # Display the uploaded image in the chat if it exists
            if uploaded_file:
                st.image(uploaded_file, width=200)

        # --- Backend Communication ---
        with st.spinner("Thinking..."):
            try:
                # --- MODIFICATION: Prepare data and files for multipart/form-data request ---
                files = None
                if uploaded_file:
                    files = {
                        "image": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                    }
                
                # The prompt is now sent in the 'data' part of the request
                response = requests.post(
                    BACKEND_URL, 
                    data={"prompt": prompt_input}, 
                    files=files, 
                    timeout=30
                )
                
                assistant_response_content = "Sorry, I encountered an error."

                if response.status_code == 200:
                    response_data = response.json()
                    action = response_data.get("agent_action", {})
                    agent_used = response_data.get("routed_to", "Unknown Agent")
                    
                    assistant_response_content = f"✅ **Request routed to `{agent_used}` and approved.**\n\n"
                    assistant_response_content += f"**Proposed Action:** `{action.get('tool')}`\n"
                    assistant_response_content += "```json\n"
                    assistant_response_content += json.dumps(action.get('parameters', {}), indent=2)
                    assistant_response_content += "\n```"
                else:
                    error_details = response.json().get("detail", "An unknown error occurred.")
                    assistant_response_content = f"❌ **Request Blocked:** {error_details}"

            except requests.exceptions.RequestException as e:
                assistant_response_content = f"**Error:** Could not connect to the backend. Please ensure it's running. \n\nDetails: {e}"
        
        st.session_state.messages.append({"role": "assistant", "content": assistant_response_content})
        with st.chat_message("assistant"):
            st.markdown(assistant_response_content, unsafe_allow_html=True)

        # Clear input fields by rerunning the script
        st.rerun()
