import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
from quiz_feature import quiz_mode  # Import the quiz_mode function

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
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
    system_instruction="You're an expert instructor. Your job is to make the students understand every detail in every lesson you teach,your students are total beginners and most of them don't understand english so please explain the lessons in the user's input language if they user asks in arabic explain in arabic. use the storytelling princples to explain"
)

# Translations dictionary
translations = {
    "English": {
        "title": "AI Lecture Explanation Chatbot",
        "select_subject": "Select Subject",
        "select_lesson": "Select Lesson",
        "select_language": "Select Language",
        "select_mode": "Select Mode",
        "chat": "Chat",
        "quiz": "Quiz",
        "ask_about_lecture": "Ask about the lecture",
        "generating_response": "Generating response...",
        "loading_quiz": "Loading quiz..."
    },
    "Arabic": {
        "title": "روبوت شرح المحاضرات بالذكاء الاصطناعي",
        "select_subject": "اختر المادة",
        "select_lesson": "اختر الدرس",
        "select_language": "اختر اللغة",
        "select_mode": "اختر الوضع",
        "chat": "دردشة",
        "quiz": "اختبار",
        "ask_about_lecture": "اسأل عن المحاضرة",
        "generating_response": "جاري إنشاء الرد...",
        "loading_quiz": "جاري تحميل الاختبار..."
    }
}


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

def get_response(model, prompt, context, language):
    full_prompt = f"{context}\n\nHuman: {prompt}\n\nAI: Please respond in {language}."
    response = model.generate_content(full_prompt)
    return response.text



def set_rtl_css():
    st.markdown("""
    <style>
        .stApp {
            direction: rtl;
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", initial_sidebar_state="expanded")

    # Initialize session state
    if 'language' not in st.session_state:
        st.session_state.language = "English"

    # Global language toggle
    language_options = ["English", "Arabic"]
    selected_language = st.sidebar.selectbox(
        "Select Language / اختر اللغة",
        language_options,
        index=language_options.index(st.session_state.language)
    )

    # Update language if changed
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        st.experimental_rerun()

    # Set RTL for Arabic
    if st.session_state.language == "Arabic":
        set_rtl_css()

    t = translations[st.session_state.language]  # Get translations for the current language

    st.title(t["title"])

    # Sidebar for subject and lesson selection
    subjects = get_subjects()
    subject = st.sidebar.selectbox(t["select_subject"], subjects)
    
    lessons = get_lessons(subject)
    lesson = st.sidebar.selectbox(t["select_lesson"], lessons)

    # Load lecture content
    lecture_content = load_lecture_content(subject, lesson)

    # Add mode selection
    mode = st.sidebar.radio(t["select_mode"], [t["chat"], t["quiz"]])

    if mode == t["chat"]:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        context = f"The current lecture is about {subject}, {lesson}. Here's the content of the lecture:\n\n{lecture_content}\n\nPlease summarize and explain aspects of this lecture based on the student's questions."

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input(t["ask_about_lecture"]):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.spinner(t["generating_response"]):
                response = get_response(model, prompt, context, st.session_state.language)

            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

    else:
        # Quiz mode
        with st.spinner(t["loading_quiz"]):
            quiz_mode(model, lecture_content, st.session_state.language)

if __name__ == "__main__":
    main()
# It should respond with the user input language
# The user should understand the lecture with the minmum amount of input (prompt)
# 