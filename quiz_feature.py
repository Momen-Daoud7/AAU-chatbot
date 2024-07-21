import streamlit as st
import google.generativeai as genai

# Translations dictionary for quiz mode
quiz_translations = {
    "English": {
        "quiz_mode": "Quiz Mode",
        "question": "Question",
        "of": "of",
        "your_answer": "Your answer:",
        "submit_answer": "Submit Answer",
        "next_question": "Next Question",
        "discuss_answer": "Discuss Answer",
        "discuss_here": "Discuss your answer here:",
        "your_question": "Your question about the answer:",
        "submit_question": "Submit Question",
        "generate_new": "Generate New Questions",
        "generating_questions": "Generating questions...",
        "evaluating_answer": "Evaluating your answer...",
        "generating_response": "Generating response...",
        "error_generating_questions": "An error occurred while generating questions. Please try again.",
        "no_questions_available": "No questions are available. Please generate new questions."
    },
    "Arabic": {
        "quiz_mode": "وضع الاختبار",
        "question": "السؤال",
        "of": "من",
        "your_answer": "إجابتك:",
        "submit_answer": "أرسل الإجابة",
        "next_question": "السؤال التالي",
        "discuss_answer": "ناقش الإجابة",
        "discuss_here": "ناقش إجابتك هنا:",
        "your_question": "سؤالك حول الإجابة:",
        "submit_question": "أرسل السؤال",
        "generate_new": "توليد أسئلة جديدة",
        "generating_questions": "جاري توليد الأسئلة...",
        "evaluating_answer": "جاري تقييم إجابتك...",
        "generating_response": "جاري إنشاء الرد...",
        "error_generating_questions": "حدث خطأ أثناء توليد الأسئلة. يرجى المحاولة مرة أخرى.",
        "no_questions_available": "لا توجد أسئلة متاحة. يرجى توليد أسئلة جديدة."
    }
}

def generate_question_bank(model, lecture_content, num_questions=5):
    prompt = f"""Based on the following lecture content, generate {num_questions} quiz questions:

    {lecture_content}

    For each question, format the output as:
    Question (English): [Your generated question in English here]
    Question (Arabic): [The same question translated to Arabic here]
    Answer: [The correct answer here]

    Separate each question with a line of dashes (---).
    """
    response = model.generate_content(prompt)
    questions = response.text.split('---')
    question_bank = []
    for q in questions:
        parts = q.strip().split("\n")
        if len(parts) == 3:  # Ensure we have all three parts
            question_bank.append({
                "question_en": parts[0].split(": ", 1)[1] if ": " in parts[0] else parts[0],
                "question_ar": parts[1].split(": ", 1)[1] if ": " in parts[1] else parts[1],
                "answer": parts[2].split(": ", 1)[1] if ": " in parts[2] else parts[2]
            })
    return question_bank

def evaluate_answer(model, question, correct_answer, user_answer, language):
    prompt = f"""Question: {question}
    Correct Answer: {correct_answer}
    User's Answer: {user_answer}

    Provide a detailed explanation of whether the user's answer is correct or incorrect, and why.
    Be encouraging and educational in your response.
    Respond in {language}.
    """
    response = model.generate_content(prompt)
    return response.text

def quiz_mode(model, lecture_content, language):
    t = quiz_translations[language]  # Get translations for the current language
    
    st.subheader(t["quiz_mode"])
    
    if "quiz_state" not in st.session_state or not st.session_state.quiz_state.get("question_bank"):
        with st.spinner(t["generating_questions"]):
            try:
                question_bank = generate_question_bank(model, lecture_content)
                if not question_bank:
                    st.error(t["error_generating_questions"])
                    return
                st.session_state.quiz_state = {
                    "question_bank": question_bank,
                    "current_question_index": 0,
                    "user_answer": "",
                    "evaluation": "",
                    "discussing": False
                }
            except Exception as e:
                st.error(f"{t['error_generating_questions']} Error: {str(e)}")
                return
    
    if not st.session_state.quiz_state["question_bank"]:
        st.warning(t["no_questions_available"])
        if st.button(t["generate_new"]):
            st.experimental_rerun()
        return

    current_q = st.session_state.quiz_state["question_bank"][st.session_state.quiz_state["current_question_index"]]
    
    # Localized question numbering
    if language == "English":
        question_number = f"{t['question']} {st.session_state.quiz_state['current_question_index'] + 1} {t['of']} {len(st.session_state.quiz_state['question_bank'])}"
    else:
        # Arabic numerals and right-to-left formatting
        arabic_numerals = ["٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"]
        current_num = ''.join(arabic_numerals[int(d)] for d in str(st.session_state.quiz_state['current_question_index'] + 1))
        total_num = ''.join(arabic_numerals[int(d)] for d in str(len(st.session_state.quiz_state['question_bank'])))
        question_number = f"{t['question']} {current_num} {t['of']} {total_num}"

    st.write(question_number)
    
    if language == "English":
        st.write(f"{t['question']}: {current_q['question_en']}")
    else:
        st.write(f"{t['question']}: {current_q['question_ar']}")

    user_answer = st.text_input(t["your_answer"], key="user_answer_input")
    
    if st.button(t["submit_answer"]):
        with st.spinner(t["evaluating_answer"]):
            evaluation = evaluate_answer(
                model, 
                current_q['question_en'] if language == "English" else current_q['question_ar'], 
                current_q['answer'], 
                user_answer,
                language
            )
        st.session_state.quiz_state.update({
            "user_answer": user_answer,
            "evaluation": evaluation
        })
    
    if st.session_state.quiz_state["evaluation"]:
        st.write(st.session_state.quiz_state["evaluation"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(t["next_question"]):
                next_index = (st.session_state.quiz_state["current_question_index"] + 1) % len(st.session_state.quiz_state["question_bank"])
                st.session_state.quiz_state.update({
                    "current_question_index": next_index,
                    "user_answer": "",
                    "evaluation": "",
                    "discussing": False
                })
                st.experimental_rerun()
        with col2:
            if st.button(t["discuss_answer"]):
                st.session_state.quiz_state["discussing"] = True
        with col3:
            if st.button(t["generate_new"]):
                st.session_state.quiz_state = {}  # Clear the quiz state
                st.experimental_rerun()
    
    if st.session_state.quiz_state["discussing"]:
        st.write(t["discuss_here"])
        discussion_input = st.text_input(t["your_question"])
        if st.button(t["submit_question"]):
            if discussion_input:
                with st.spinner(t["generating_response"]):
                    discussion_response = model.generate_content(f"Regarding the question '{current_q['question_en']}' and the answer '{current_q['answer']}', the user asks: {discussion_input}. Respond in {language}.")
                st.write(discussion_response.text)