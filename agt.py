import os
import pdfplumber
import streamlit as st
from groq import Groq
from gtts import gTTS

# Initialize the Groq client with the API key from environment variable
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)
# Enable dark mode
st.markdown("<style>body {background-color: #212121;}</style>", unsafe_allow_html=True)

# Custom CSS to hide the Streamlit menu and footer
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
st.markdown(hide_menu_style, unsafe_allow_html=True)


# Function to generate and play text-to-speech audio
def generate_audio(audio_text, filename="audio.mp3"):
    try:
        tts = gTTS(text=audio_text, lang='en')
        tts.save(filename)
        return filename
    except Exception as e:
        st.sidebar.error(f"Failed to generate text-to-speech: {e}")
        return None

# Function to read the contents of the uploaded text file
def read_uploaded_text(file):
    return file.read().decode("utf-8")

# Function to read the contents of the uploaded PDF file
def read_uploaded_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Streamlit app
st.sidebar.image("pic2.PNG", width=120)
st.sidebar.markdown('<h2 style="color:#00FF00;">Double AGENT 2x</h2>', unsafe_allow_html=True)
st.sidebar.text("Select mode:")

# Creating a radio button in the sidebar
sidebar_option = st.sidebar.radio(
    "Choose an option",
    ('check 1 by 1', 'double 2 reply', 'compare a to b')
)

st.sidebar.write('You selected:', sidebar_option)

# Select model to start sidebar
model_option_1 = st.sidebar.selectbox(
    "Select a 1st LLM model",
    ('Model A - llama3-8b-8192', 'Model B - llama3-70b-8192')
)
st.sidebar.write('You selected 1st:', model_option_1)

model_option_2 = st.sidebar.selectbox(
    "Select a 2nd LLM model",
    ('Model A - llama3-8b-8192', 'Model B - llama3-70b-8192')
)
st.sidebar.write('You selected 2nd:', model_option_2)

# System prompt input in the sidebar
system_prompt = st.sidebar.text_area("Enter system prompt (optional):", value="System prompt default text", height=100)

# User role input in the sidebar
user_role = st.sidebar.text_area("Enter user role (optional):", value="User role default text", height=50)

# User prompt input in the sidebar
prompt = st.sidebar.text_area("Enter your prompt:", value="User prompt default text", height=150)

# File upload input in the sidebar
uploaded_file = st.sidebar.file_uploader("Upload a text or PDF file", type=["txt", "pdf"])

# Read the content of the uploaded file, if any
file_content = ""
if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        file_content = read_uploaded_pdf(uploaded_file)
    elif uploaded_file.type == "text/plain":
        file_content = read_uploaded_text(uploaded_file)

# Function to query Groq API
def query_groq(system_prompt, user_role, combined_prompt, model):
    try:
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })
        if user_role:
            messages.append({
                "role": "user",
                "content": user_role,
            })
        messages.append({
            "role": "user",
            "content": combined_prompt,
        })

        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Initialize session state variables
if 'reply_1_text' not in st.session_state:
    st.session_state.reply_1_text = ""
if 'reply_2_text' not in st.session_state:
    st.session_state.reply_2_text = ""
if 'comparison_analysis' not in st.session_state:
    st.session_state.comparison_analysis = []

# Button to submit the query
if st.sidebar.button("Submit"):
    if prompt or file_content:
        with st.spinner("Querying the chatbot..."):
            # Combine file content and user prompt
            combined_prompt = f"{file_content}\n{prompt}"
            
            # Mode selection logic
            if sidebar_option == 'check 1 by 1':
                # Generate two separate replies for the same prompt from different models
                reply_1 = query_groq(system_prompt, user_role, combined_prompt, model_option_1.split(' - ')[1])
                st.session_state.reply_1_text = reply_1
                
                reply_2 = query_groq(system_prompt, user_role, combined_prompt, model_option_2.split(' - ')[1])
                st.session_state.reply_2_text = reply_2

            elif sidebar_option == 'double 2 reply':
                # Use the first model to generate a reply
                reply_1 = query_groq(system_prompt, user_role, combined_prompt, model_option_1.split(' - ')[1])
                st.session_state.reply_1_text = reply_1
                
                # Use the second model to validate or enhance the first reply
                validation_prompt = f"Please review the following reply for accuracy and completeness and provide any necessary corrections or additional details:\n\n{reply_1}"
                reply_2 = query_groq(system_prompt, user_role, validation_prompt, model_option_2.split(' - ')[1])
                st.session_state.reply_2_text = reply_2

            elif sidebar_option == 'compare a to b':
                # Generate replies from both models for the same prompt
                reply_1 = query_groq(system_prompt, user_role, combined_prompt, model_option_1.split(' - ')[1])
                st.session_state.reply_1_text = reply_1
                
                reply_2 = query_groq(system_prompt, user_role, combined_prompt, model_option_2.split(' - ')[1])
                st.session_state.reply_2_text = reply_2

                # Provide a summary analysis of the comparisons
                differences = [line for line in reply_1.split('\n') if line not in reply_2.split('\n')]
                st.session_state.comparison_analysis = differences

    else:
        st.sidebar.warning("Please enter a prompt or upload a file.")

# Reset button
if st.sidebar.button("Reset"):
    st.session_state.reply_1_text = ""
    st.session_state.reply_2_text = ""
    st.session_state.comparison_analysis = []
    st.experimental_rerun()

# Main content
st.image("pic1.PNG", width=150)
st.markdown('<h1 style="color:#00FF00;">Double AGENT 2x </h1>', unsafe_allow_html=True)

st.write("Enter a system prompt (optional) and a user role (optional) in the sidebar, then click 'Submit' to get a response from the LLM.")
st.write("Alternatively, you can upload a text or PDF file to use its content as the prompt.")
st.write("Select to have 2 replies, one by one or 1st feed 2nd or 1st then 2nd then comparrsion analysis:")
st.success("built by DW v1 2x LLM- Text, PDF, A/B analysis of 2 models replies with text to speech")
st.write("Replies:")

# Display the stored replies
if st.session_state.reply_1_text:
    st.write("Response from Model 1:")
    st.info(st.session_state.reply_1_text)

if st.session_state.reply_2_text:
    st.write("Response from Model 2:")
    st.info(st.session_state.reply_2_text)

if st.session_state.comparison_analysis:
    st.write("Comparison Analysis:")
    st.write(st.session_state.comparison_analysis)

# Function to play audio
def play_audio(audio_file_path):
    try:
        with open(audio_file_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format='audio/mp3')
    except FileNotFoundError:
        st.error(f"Audio file not found: {audio_file_path}")
    except Exception as e:
        st.error(f"An error occurred while trying to play the audio: {e}")

# Creating options for audio playback
audio_option = st.sidebar.radio(
    "Choose an audio reply option",
    ('Default sound', 'Audio reply from Model 1', 'Audio reply from Model 2')
)

# Button to play the audio
if st.sidebar.button('Play Recorded Reply'):
    with st.spinner("Loading audio..."):
        if audio_option == 'Default sound':
            play_audio('snd.mp3')
        elif audio_option == 'Audio reply from Model 1':
            if st.session_state.reply_1_text:
                audio_file = generate_audio(st.session_state.reply_1_text, "audio_reply_model_1.mp3")
                if audio_file:
                    play_audio(audio_file)
            else:
                st.error("No reply from Model 1 to generate audio.")
        elif audio_option == 'Audio reply from Model 2':
            if st.session_state.reply_2_text:
                audio_file = generate_audio(st.session_state.reply_2_text, "audio_reply_model_2.mp3")
                if audio_file:
                    play_audio(audio_file)
            else:
                st.error("No reply from Model 2 to generate audio.")