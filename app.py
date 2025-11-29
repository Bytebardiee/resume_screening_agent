import streamlit as st
import pypdf
import os
import pandas as pd
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure page settings
st.set_page_config(page_title="Resume Screening Agent", layout="wide")

# Initialize Session State
if "results" not in st.session_state:
    st.session_state.results = []

def extract_text_from_pdf(file):
    try:
        pdf_reader = pypdf.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading {file.name}: {e}")
        return None

def analyze_resume(resume_text, job_description, api_key):
    genai.configure(api_key=api_key)
    
    # List of models to try in order of preference
    models_to_try = [
        'gemini-2.0-flash-lite',
        'gemini-flash-latest',
        'gemini-pro-latest',
        'models/gemini-2.0-flash-lite',
        'models/gemini-flash-latest'
    ]
    
    prompt = f"""
    You are an expert HR Assistant. Your task is to evaluate a candidate's resume against a given Job Description (JD).
    
    Job Description:
    {job_description}
    
    Resume Text:
    {resume_text}
    
    Analyze the resume and provide a structured JSON response with the following fields:
    - "candidate_name": Extract the candidate's name.
    - "score": A score from 0 to 100 based on how well they match the JD.
    - "match_reason": A brief summary (1-2 sentences) explaining the score.
    - "missing_keywords": A list of critical skills or keywords missing from the resume.
    
    Output ONLY valid JSON. Do not include markdown formatting like ```json.
    """

    last_error = None
    
    for model_name in models_to_try:
        try:
            # st.info(f"Trying model: {model_name}...") 
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            content = response.text.strip()
            
            # Clean up if the model adds markdown code blocks
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
                
            return json.loads(content)
        except Exception as e:
            last_error = e
            st.warning(f"Model {model_name} failed: {e}")
            continue

    st.error(f"All models failed. Please check your API Key and Quota. Last error: {last_error}")
    return None

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Check for API Key in env or allow user input
    env_api_key = os.getenv("GOOGLE_API_KEY")
    if env_api_key and env_api_key != "your_api_key_here":
        api_key = env_api_key
        st.success("API Key loaded from environment")
    else:
        api_key = st.text_input("Enter Google Gemini API Key", type="password")
        if not api_key:
            st.warning("Please enter your API Key to proceed.")
            st.markdown("[Get a Gemini API Key](https://aistudio.google.com/app/apikey)")

# Main Content
st.title("📄 AI Resume Screening Agent")
st.markdown("Upload resumes and a job description to rank candidates instantly.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Job Description")
    job_description = st.text_area("Paste the Job Description here", height=300, placeholder="e.g. We are looking for a Senior Python Developer with experience in...")

with col2:
    st.subheader("2. Upload Resumes")
    uploaded_files = st.file_uploader("Upload PDF Resumes", type=["pdf"], accept_multiple_files=True)

if st.button("Analyze Resumes", type="primary"):
    if not api_key:
        st.error("Please provide an API Key.")
    elif not job_description:
        st.error("Please provide a Job Description.")
    elif not uploaded_files:
        st.error("Please upload at least one resume.")
    else:
        st.session_state.results = [] # Clear previous results
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Analyzing {file.name}...")
            text = extract_text_from_pdf(file)
            if text:
                analysis = analyze_resume(text, job_description, api_key)
                if analysis:
                    analysis['filename'] = file.name
                    st.session_state.results.append(analysis)
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("Analysis Complete!")
        progress_bar.empty()

# Display Results
if st.session_state.results:
    st.divider()
    st.subheader("📊 Analysis Results")
    
    # Convert to DataFrame for sorting/display
    df = pd.DataFrame(st.session_state.results)
    
    # Reorder columns
    cols = ['candidate_name', 'score', 'match_reason', 'missing_keywords', 'filename']
    # Handle cases where extraction might have failed for some fields
    available_cols = [c for c in cols if c in df.columns]
    df = df[available_cols]
    
    # Sort by score descending
    if 'score' in df.columns:
        df = df.sort_values(by='score', ascending=False)
    
    # Display summary table
    st.dataframe(
        df.style.background_gradient(subset=['score'], cmap="RdYlGn"),
        column_config={
            "score": st.column_config.ProgressColumn(
                "Match Score",
                help="The match score between 0 and 100",
                format="%d",
                min_value=0,
                max_value=100,
            ),
        },
        use_container_width=True
    )
    
    # Detailed View
    st.subheader("📝 Detailed Breakdown")
    for index, row in df.iterrows():
        with st.expander(f"{row.get('candidate_name', 'Unknown')} - Score: {row.get('score', 0)}"):
            st.write(f"**Filename:** {row.get('filename')}")
            st.write(f"**Match Reason:** {row.get('match_reason')}")
            if 'missing_keywords' in row and row['missing_keywords']:
                st.write(f"**Missing Keywords:** {', '.join(row['missing_keywords'])}")
