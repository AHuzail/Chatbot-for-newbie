import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
from duckduckgo_search import DDGS
import logging


st.set_page_config(page_title="Gemini Career Chatbot", page_icon=":mortar_board:")


logging.basicConfig(level=logging.ERROR)


st.markdown(
    """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f0f8ff; /* Light background */
        }
        .stApp {
            background-color: #f0f8ff;
        }
        .stChatInputContainer textarea {
            border: 2px solid #90CAF9 !important; /* Light blue border */
            border-radius: 12px;
            padding: 14px;
            font-size: 16px;
            line-height: 1.5;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); /* Subtle shadow */
            transition: border-color 0.3s ease;
        }
        .stChatInputContainer textarea:focus {
            border-color: #64B5F6 !important; /* Deeper blue on focus */
        }
        .stChatMessage {
            border-radius: 15px;
            padding: 14px 22px;
            margin-bottom: 12px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease-in-out;
        }
        .stChatMessage:hover {
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
        }
        .stChatMessage[data-streamlit=true] {
            background-color: #BBDEFB; /* Light blue for user */
            color: #263238; /* Darker text for better contrast */
            text-align: right;
            margin-left: 25%;
        }
        .stChatMessage[data-streamlit=false] {
            background-color: #E8F5E9; /* Light green for assistant */
            color: #263238; /* Darker text for better contrast */
            text-align: left;
            margin-right: 25%;
            border: 1px solid #eee; /* Add a subtle border */
        }
        .sidebar .sidebar-content {
            background-color: #B2DFDB; /* Light teal sidebar */
            color: #263238; /* Darker text for better contrast */
            padding-top: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #1A237E; /* Indigo for main title */
            font-weight: bold;
            margin-bottom: 25px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.05);
        }
        h2 {
            color: #00796B; /* Teal for section titles */
            margin-top: 30px;
            margin-bottom: 18px;
        }
        .st-emotion-cache-1y4p8pa { /* Streamlit main content area */
            padding-top: 30px;
            padding-bottom: 30px;
        }
        /* New stylistic elements */
        .decoration-line {
            border-bottom: 2px solid #4FC3F7; /* Lighter blue line */
            margin: 20px 0;
        }
        .info-box {
            background-color: #FFFDE7; /* Light yellow */
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
            color: #5D4037; /* Brownish text color */
        }
    </style>
    """,
    unsafe_allow_html=True,
)

load_dotenv()

# --- Sidebar ---
with st.sidebar:
    st.title("🎓 Career Guide")
    st.markdown("Powered by **Google Gemini**")
    st.markdown("Your AI career advisor. Get personalized guidance.")
    st.markdown("---")

# --- Initialize Gemini Client ---
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# --- Initialize chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Main App Content ---
st.title("Gemini Career Chatbot")

# Decorative Line
st.markdown("<div class='decoration-line'></div>", unsafe_allow_html=True)

# Informational Box
st.markdown(
    """
    <div class='info-box'>
        <p>Welcome! I'm here to help you explore exciting career paths in technology. Ask me about anything. Let's discover your ideal career together!</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Display chat messages from history on app rerun ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input ---
if prompt := st.chat_input("What career paths are you curious about?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Tool Handling & Gemini Response ---
    bot_response = ""
    tool_output = None

    if "search for" in prompt.lower() or "look up" in prompt.lower():
        search_query = prompt.lower().replace("search for", "").replace("look up", "").strip()
        with st.spinner(f"Searching the web for: {search_query}"):
            try:
                search_results = DDGS().text(search_query, max_results=3)
                if search_results:
                    tool_output = "Search Results:\n"
                    for i, result in enumerate(search_results):
                        tool_output += f"{i+1}. [{result['title']}]({result['href']})\n   {result['body']}\n"
                else:
                    tool_output = "No relevant search results found."
            except Exception as e:
                tool_output = f"Error during web search: {e}"
                st.error(tool_output)
                logging.error(f"DuckDuckGo search error: {e}")

    # --- Construct Prompt for Gemini, Including History ---
    full_prompt = "You are a friendly and encouraging career advisor...\n\n"  # System prompt
    for msg in st.session_state.messages:
        full_prompt += f"{msg['role']}: {msg['content']}\n"

    if tool_output:
        full_prompt += f"\nTool Output:\n{tool_output}\n"
        full_prompt += "Using the information from the tool output, answer the original query as a career advisor."

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # Corrected Gemini API call
            response = model.generate_content(
                [
                    {"role": "user", "parts": [full_prompt]},  # All context in user prompt
                ],
                stream=True
            )

            for chunk in response:
                full_response += chunk.text
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            bot_response = full_response

        except Exception as e:
            st.error(f"An error occurred: {e}")
            logging.error(f"Gemini API error: {e}")
            bot_response = "Sorry, I encountered an error."
            message_placeholder.markdown(bot_response)

    st.session_state.messages.append({"role": "assistant", "content": bot_response})
