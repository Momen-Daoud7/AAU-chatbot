import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google Generative AI
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Set up generation config
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 18192,
}

# Initialize the model with the new configuration
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    system_instruction="You're a lecture summarizer assistant. Your job is to create high-quality summaries that represent the main ideas, quotes, analogies and key points from the lecture content, focusing on aspects relevant to the student's questions and learning goals."
)

def load_lecture_content(subject, lesson):
    file_path = os.path.join("lectures", subject, f"{lesson}.txt")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return f"Error: Lecture file for {subject}, {lesson} not found."
    except Exception as e:
        return f"Error loading lecture content: {str(e)}"

def get_subjects():
    return [d for d in os.listdir("lectures") if os.path.isdir(os.path.join("lectures", d))]

def get_lessons(subject):
    subject_dir = os.path.join("lectures", subject)
    return [f.split('.')[0] for f in os.listdir(subject_dir) if f.endswith('.txt')]

def get_response(message, context):
    prompt = f"{context}\n\nHuman: {message}\n\nAI:"
    response = model.generate_content(prompt)
    return response.text

def main():
    st.title("AI Lecture Explanation Chatbot")

    # Sidebar for subject and lesson selection
    subjects = get_subjects()
    subject = st.sidebar.selectbox("Select Subject", subjects)
    
    lessons = get_lessons(subject)
    lesson = st.sidebar.selectbox("Select Lesson", lessons)

    # Load lecture content
    lecture_content = load_lecture_content(subject, lesson)

    # Initialize chat history and context
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Set up the initial context with the lecture content
    context = f"The current lecture is about {subject}, {lesson}. Here's the content of the lecture:\n\n{lecture_content}\n\nPlease summarize and explain aspects of this lecture based on the student's questions."

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about the lecture"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate AI response
        response = get_response(prompt, context)

        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

if __name__ == "__main__":
    main()