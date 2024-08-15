from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import speech_recognition as sr
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Configure the Google Generative AI with your API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the model and start a chat
model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])

# File path for storing conversation history
HISTORY_FILE = "conversation_history.json"

# Function to save conversation history to a file
def save_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump(st.session_state.conversation, f)

# Function to load conversation history from a file
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

# Load the conversation history at the start
if "conversation" not in st.session_state:
    st.session_state.conversation = load_history()

# Function to get the Gemini response
def get_gemini_response(input_text):
    if input_text:
        response = chat.send_message(input_text, stream=True)
        response_text = ""
        for chunk in response:
            response_text += chunk.text
        return response_text
    return "No input provided."

# Function to summarize or truncate text
def summarize_text(text, max_length=100):
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

# Initialize the Streamlit app with a custom theme
st.set_page_config(
    page_title="Q&A Chatbot",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Header section with styling
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Gemini Q&A Chatbot</h1>", unsafe_allow_html=True)

# Initialize session state to hold recording state and other variables
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "recorded_text" not in st.session_state:
    st.session_state.recorded_text = ""
if "recorded_audio" not in st.session_state:
    st.session_state.recorded_audio = None

# Voice search feature
st.markdown("### Voice Search")

if not st.session_state.is_recording:
    if st.button("Click and Speak"):
        st.session_state.is_recording = True
        st.session_state.recorded_text = ""
        st.session_state.recorded_audio = None

if st.session_state.is_recording:
    st.write("Listening...")
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
        
        # Process the audio as soon as it stops
        try:
            # Recognize speech using Google Speech Recognition
            st.session_state.recorded_text = recognizer.recognize_google(audio)
            st.write(f"**You said:** {st.session_state.recorded_text}")

            # Automatically trigger the Gemini response
            input_text = st.session_state.recorded_text
            response_text = get_gemini_response(input_text)
            st.write(f"**Gemini Response:** {response_text}")

            # Save both the question and the response to the conversation history
            st.session_state.conversation.append({"user": input_text, "response": response_text})
            save_history()

        except sr.UnknownValueError:
            st.write("Google Speech Recognition could not understand the audio.")
        except sr.RequestError as e:
            st.write(f"Could not request results from Google Speech Recognition service; {e}")
        
        # Stop recording automatically after processing
        st.session_state.is_recording = False

# Input section with placeholder and styling
input_text = st.text_input("Ask me anything:", key="input", placeholder="Type your question here...")

# Submit button with a more prominent style
submit = st.button("Ask Gemini", help="Click to get a response from Gemini", key="submit")

# If submit button is clicked
if submit and input_text:
    response_text = get_gemini_response(input_text)
    st.session_state.conversation.append({"user": input_text, "response": response_text})
    save_history()

# Display the entire conversation, newest at the top
if len(st.session_state.conversation) > 0:
    st.subheader("Conversation:")
    for entry in reversed(st.session_state.conversation):
        st.markdown(f"**You:** {entry['user']}")
        st.markdown(f"**Gemini:** {entry['response']}")
        st.markdown("---")

# Advanced feature: Conversation history display in sidebar
if st.sidebar.checkbox("Show conversation history", value=True):
    st.sidebar.markdown("## Conversation History")
    for entry in reversed(st.session_state.conversation):
        summary_user = summarize_text(entry['user'])
        summary_response = summarize_text(entry['response'])
        st.sidebar.markdown(f"**You:** {summary_user}")
        st.sidebar.markdown(f"**Gemini:** {summary_response}")
        st.sidebar.markdown("---")

# Display the timestamp of the last query
if len(st.session_state.conversation) > 0:
    last_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.sidebar.markdown(f"**Last Query:** {last_time}")

# Advanced feature: Clear conversation history
if st.sidebar.button("Clear History"):
    # Clear the conversation history
    st.session_state.conversation.clear()
    save_history()
    # Reset the session state for a fresh start
    st.session_state.is_recording = False
    st.session_state.recorded_text = ""
    st.session_state.recorded_audio = None
