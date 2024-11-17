import asyncio
import json
import logging
import re
import pandas as pd
import time

import streamlit as st
from docx import Document # pip install python-docx
from PyPDF2 import PdfReader # pip install PyPDF2
import plotly.graph_objects as go
import groq
from crawl4ai import AsyncWebCrawler
from prompts import evaluation_prompt, rephrase_prompt, cover_letter_prompt, blurbs

def setup_logger():
    logger = logging.getLogger('re_sift_app')
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # File handler
        file_handler = logging.FileHandler('app.log', mode='a')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger

# Initialize logger
logger = setup_logger()
logger.debug("Initializing groq client.")
client = groq.Groq(api_key=st.secrets["GROQ_API_KEY"])

def extract_text_from_pdf(pdf_file):
    logger.debug("Extracting text from PDF file.")
    reader = PdfReader(pdf_file)
    text = ""
    for page_number, page in enumerate(reader.pages):
        logger.debug(f"Extracting text from page {page_number + 1}.")
        extracted = page.extract_text()
        if extracted:
            text += extracted
        else:
            logger.warning(f"No text found on page {page_number + 1}.")
    logger.debug("Finished extracting text from PDF.")
    return text

def extract_text_from_docx(docx_file):
    logger.debug("Extracting text from DOCX file.")
    doc = Document(docx_file)
    text = ""
    for i, para in enumerate(doc.paragraphs):
        logger.debug(f"Extracting text from paragraph {i + 1}.")
        text += para.text + "\n"
    logger.debug("Finished extracting text from DOCX.")
    return text

async def generate_blurb(text, context="blurb"):
    """
    Generates a blurb about the text for the analysis in markdown format.
    """
    logger.debug("Starting blurb generation.")
    custom_prompt = blurbs[context].substitute(scraped_info=text)
    try:
        logger.debug(f"Sending request for blurb generation - {context}")
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an expert in analysing long content and generating insightful blubs from it."},
                {"role": "user", "content": custom_prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        logger.debug("Received response from API.")
        blurb = response.choices[0].message.content.strip()
        logger.debug(f"Successfully generated {context} blurb.")
        return blurb
    except Exception as e:
        logger.error(f"Error during cover letter generation: {e}")
        st.error(f"Error during cover letter generation: {e}")
        return None
    
def get_blurb(text, context="blurb"):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    blurb = loop.run_until_complete(generate_blurb(text, context))
    loop.close()
    return blurb

@st.cache_data
def get_blurb_cached(text, context="blurb"):
    return get_blurb(text, context)

async def scrape_company_info(company_website_url):
    """
    scrapes company information from the company's website.
    generates a blurb about the company for the analysis in markdown format.
    """
    if not company_website_url.startswith('https') or company_website_url.startswith('www'):
        company_website_url = 'https://' + company_website_url

    async with AsyncWebCrawler(verbose=True) as crawler:
        company_result = await crawler.arun(url=company_website_url, bypass_cache=True)
        company_info = company_result.markdown  # You can also use .text or .cleaned_html
        return company_info

async def scrape_crunchbase_info(company_name):
    """
    scrapes company information from Crunchbase.
    generates a blurb about the company for the analysis in markdown format.
    """
    crunchbase_url = f"https://www.crunchbase.com/organization/{company_name.replace(' ', '-').lower()}"
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=crunchbase_url, bypass_cache=True)
        crunchbase_info = result.markdown  # or .text or .cleaned_html
        return crunchbase_info

async def scrape_linkedin(linkedin_url):
    """
    scrapes LinkedIn information from the LinkedIn profile URL.
    generates a blurb about the LinkedIn profile for the analysis in markdown format.
    """
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=linkedin_url, bypass_cache=True)
        linkedin_info = result.markdown  # or .text or .cleaned_html
        return linkedin_info

async def scrape_github(github_url):
    """
    scrapes GitHub information from the GitHub profile URL.
    generates a blurb about the GitHub profile for the analysis in markdown format.
    """
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=github_url, bypass_cache=True)
        github_info = result.markdown  # or .text or .cleaned_html
        return github_info

def get_scraped_data(company_name, company_website_url, linkedin_url, github_url):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = []
    if company_name:
        tasks.append(scrape_company_info(company_website_url))
        tasks.append(scrape_crunchbase_info(company_name))
    if linkedin_url:
        tasks.append(scrape_linkedin(linkedin_url))
    if github_url:
        tasks.append(scrape_github(github_url))
    results = loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()
    return results

def get_scraped_company_data(company_name, company_website_url):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = []
    if company_name:
        tasks.append(scrape_company_info(company_website_url))
        tasks.append(scrape_crunchbase_info(company_name))
    results = loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()
    return results

@st.cache_data
def analyze_documents(resume_text, job_description, company_info="", crunchbase_info="", linkedin_info="", github_info=""):
    logger.debug("Starting document analysis.")
    custom_prompt = evaluation_prompt.substitute(
        resume_text=resume_text,
        job_description=job_description,
        company_info=company_info,
        crunchbase_info=crunchbase_info,
        linkedin_info=linkedin_info,
        github_info=github_info
    )
    st.write(custom_prompt)
    logger.debug("Custom prompt generated for document analysis: \n" + custom_prompt + "\n")
    try:
        logger.debug("Sending request to  API for document analysis.")
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are an expert resume analyzer capable of generating detailed and insightful analysis."},
                {"role": "user", "content": custom_prompt}
            ],
            temperature=0.7,
            max_tokens=8192,
        )
        logger.debug("Received response from API.")
        analysis_text = response.choices[0].message.content.strip()
        logger.debug("Extracting JSON from the response.")

        try:
            try:
                extract_json = re.search(r'```json(.*?)```', analysis_text, re.DOTALL).group(1)
            except:
                extract_json = re.search(r'```(.*?)```', analysis_text, re.DOTALL).group(1)
            analysis_json = json.loads(extract_json)
            logger.debug("Successfully parsed JSON from the response.")
            return analysis_json
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding failed: {e}")
            return {"error": "Invalid JSON response from the analysis. Please check the prompt and try again.", "raw_response": analysis_text}
        except AttributeError as e:
            logger.error(f"JSON extraction failed: {e}")
            return {"error": "Could not find JSON in the response. Please check the prompt and try again.", "raw_response": analysis_text}
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        st.error(f"Error during analysis: {e}")
        return None

@st.cache_data
def rephrase_text(text):
    logger.debug("Starting text rephrasing.")
    custom_prompt = rephrase_prompt.substitute(text)

    try:
        logger.debug("Sending request to API for text rephrasing.")
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an expert resume writer."},
                {"role": "user", "content": custom_prompt}
            ],
            temperature=0.7,
            max_tokens=768,
        )
        logger.debug("Received response from  API.")
        rephrased = response.choices[0].message.content.strip()
        logger.debug("Successfully rephrased text.")
        return rephrased
    except Exception as e:
        logger.error(f"Error during rephrasing: {e}")
        st.error(f"Error during rephrasing: {e}")
        return None

def generate_cover_letter(resume_text, job_description, company_info=""):
    logger.debug("Starting cover letter generation.")
    custom_prompt = cover_letter_prompt.substitute(resume_text=resume_text, job_description=job_description, company_info=company_info)

    try:
        logger.debug("Sending request to API for cover letter generation.")
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an expert resume and cover letter writer."},
                {"role": "user", "content": custom_prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        logger.debug("Received response from  API.")
        cover_letter = response.choices[0].message.content.strip()
        logger.debug("Successfully generated cover letter.")
        return cover_letter
    except Exception as e:
        logger.error(f"Error during cover letter generation: {e}")
        st.error(f"Error during cover letter generation: {e}")
        return None

def display_resume(file):
    logger.debug(f"Displaying resume content from file: {file.name}")
    file_type = file.name.split('.')[-1].lower()
    if file_type == 'pdf':
        resume_text = extract_text_from_pdf(file)
    elif file_type == 'docx':
        resume_text = extract_text_from_docx(file)
    else:
        logger.error("Unsupported file type for resume display.")
        st.error("Unsupported file type. Please upload a PDF or DOCX file.")
        return
    st.text_area("Parsed Resume Content", resume_text, height=400)


def create_dummy_profiles():
    data = {
        "Name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "Role": ["Data Scientist", "Backend Developer", "Frontend Developer", "AI Engineer", "DevOps Engineer"],
        "Experience (years)": [5, 3, 4, 6, 7],
        "Responsibilities Fit": [85, 75, 80, 90, 70],
        "Qualifications Fit": [90, 80, 85, 95, 75],
        "Skills Fit": [80, 70, 75, 85, 65],
        "Role Fit": [90, 65, 80, 88, 78],
        "Culture Fit": [70, 85, 65, 75, 80],
        "Overall Score": [0, 0, 0, 0, 0],  # Placeholder for recalculated score
    }
    return pd.DataFrame(data)

def recalculate_scores(profiles, job_description):
    # Example weights for different segments
    weights = {
        "Responsibilities Fit": 0.3,
        "Qualifications Fit": 0.2,
        "Skills Fit": 0.25,
        "Role Fit": 0.15,
        "Culture Fit": 0.1,
        "Experience (years)": 0.15,
    }
    
    # Dummy logic: Adjust segment scores slightly based on job description length
    job_length_factor = min(len(job_description) / 100, 1.0)
    profiles["Skills Fit"] = profiles["Skills Fit"] * (1 + 0.1 * job_length_factor)
    profiles["Role Fit"] = profiles["Role Fit"] * (1 + 0.05 * job_length_factor)
    profiles["Culture Fit"] = profiles["Culture Fit"] * (1 - 0.05 * job_length_factor)
    
    # Recalculate overall score
    profiles["Overall Score"] = (
        profiles["Skills Fit"] * weights["Skills Fit"] +
        profiles["Role Fit"] * weights["Role Fit"] +
        profiles["Culture Fit"] * weights["Culture Fit"]
    )
    
    # Normalize scores to a 0-100 range
    profiles["Overall Score"] = profiles["Overall Score"] / profiles["Overall Score"].max() * 100
    return profiles

logger.debug("Setting up Streamlit page configuration.")
st.set_page_config(page_title="Re-Sift", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Resume Analyzer", "ATS Templates", "Find My Candidate"]) #"Magic Write",

if page == "Resume Analyzer":
    logger.debug("User selected 'Resume Analyzer' page.")
    st.title("📄🔍 Re-Sift")
    st.write("Welcome to Re-Sift, a Resume Evaluation System! \nUpload your resume and enter the job description and relevant info to get a detailed evaluation of your resume's match with the job requirements.")

    # Primary Inputs
    st.subheader("Primary Information")
    job_description = st.text_area("Job Description:", height=200)
    resume = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

    # Additional Details within an Expander
    with st.expander("Additional Details (Optional)", expanded=False):
        st.subheader("Additional Information")
        company_name = st.text_input("Company Name:")
        company_website_url = st.text_input("Company Website URL:")
        linkedin_url = st.text_input("LinkedIn URL:")
        github_url = st.text_input("GitHub URL:")

    # Display Resume Content
    if resume:
        logger.debug(f"Resume uploaded: {resume.name}")
        st.write("### Uploaded Resume:")
        display_resume(resume)

    # Initialize Session State Variables
    if 'analysis' not in st.session_state:
        st.session_state.analysis = None
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = None
    if 'job_description' not in st.session_state:
        st.session_state.job_description = None
    if 'company_info' not in st.session_state:
        st.session_state.company_info = ""

    # Run Analysis Button
    if st.button("Run Analysis"):
        logger.debug("Run Analysis button clicked.")
        if job_description and resume:
            logger.debug("Job description and resume are provided. Starting analysis.")
            with st.spinner("Extracting User Information..."):
                st.write("Extracting User Information...")
                if company_name or company_website_url or linkedin_url or github_url:
                    scraped_data = get_scraped_data(company_name, company_website_url, linkedin_url, github_url)
                
                # Generate blurbs from scraped data
                if company_name:
                    company_info = get_blurb(scraped_data[0], context="company_info")
                    crunchbase_info = get_blurb(scraped_data[1], context="crunchbase_profile")
                else:
                    company_info = ""
                    crunchbase_info = ""

                if linkedin_url:
                    linkedin_info = get_blurb(scraped_data[2], context="linkedin")
                else:
                    linkedin_info = ""

                if github_url:
                    github_info = get_blurb(scraped_data[3], context="github")
                else:
                    github_info = ""
                
                st.write("Blurb generation completed successfully.")

            with st.spinner("Analyzing..."):
                resume.seek(0)  # Reset the file pointer to the start
                file_type = resume.name.split('.')[-1].lower()
                if file_type == 'pdf':
                    resume_text = extract_text_from_pdf(resume)
                elif file_type == 'docx':
                    resume_text = extract_text_from_docx(resume)
                else:
                    logger.error("Unsupported file type during analysis.")
                    st.error("Unsupported file type.")
                    resume_text = ""

                if resume_text:
                    logger.debug("Resume text extracted successfully. Proceeding with analysis.")
                    st.session_state.resume_text = resume_text
                    st.session_state.job_description = job_description
                    st.session_state.company_info = company_info

                    analysis = analyze_documents(
                        resume_text, 
                        job_description, 
                        company_info[:256], 
                        crunchbase_info[:256], 
                        linkedin_info[:256], 
                        github_info[:256]
                    )
                    st.session_state.analysis = analysis

                if st.session_state.analysis:
                    analysis = st.session_state.analysis
                    if "error" in analysis:
                        logger.error("Error in analysis response.")
                        st.error(analysis["error"])
                        st.text_area("Raw Response:", analysis.get("raw_response", ""), height=300)
                    else:
                        logger.debug("Analysis completed successfully. Displaying results.")
        else:
            logger.error("Job description or resume not provided.")
            st.error("Please enter the job description and upload a resume.")

    # Display Analysis Results
    if st.session_state.analysis and "error" not in st.session_state.analysis:
        analysis = st.session_state.analysis
        response = analysis.get("analysis", {})
        fit_categories = ["role_fit", "experience_fit", "responsibilities_fit",
                          "skills_fit", "qualifications_fit", "culture_fit"]

        total_score = 0
        num_categories = 0

        st.markdown("### Detailed Scores and Feedback")

        for category in fit_categories:
            fits = response.get("fit_analysis", {})
            fit_data = fits.get(category, {})
            score = fit_data.get("score", 0)
            feedback = fit_data.get("feedback", "No feedback provided.")
            reasoning = fit_data.get("reasoning", "No reasoning provided.")
            st.write(f"**{category.replace('_', ' ').title()}:** {score}/100")
            st.progress(score)
            st.write(f"*Feedback:* {feedback}\n")
            st.write(f"*Reasoning:* {reasoning}\n")

            total_score += score
            num_categories += 1

        # Calculate overall score
        if num_categories > 0:
            overall_score = total_score / num_categories
        else:
            overall_score = 0

        # Display overall score graphically
        st.markdown("### Overall Match Assessment")
        st.write(f"**Overall Score:** {overall_score:.2f}/100")

        # Create a gauge chart for the overall score
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=overall_score,
            title={'text': "Overall Match Score"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': 'lightcoral'},
                    {'range': [50, 75], 'color': 'gold'},
                    {'range': [75, 100], 'color': 'lightgreen'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': overall_score}
            }
        ))

        st.plotly_chart(fig)

        # Display overall assessment text
        overall_assessment = response.get("overall_match_assessment", "")
        if overall_assessment:
            st.write("**Assessment Details:**")
            st.write(overall_assessment)
        # Display meta_reflection
        meta_reflection = response.get("meta_reflection", "")
        if meta_reflection:
            st.write("**Assessment Considerations:**")
            st.write(meta_reflection)
        # Display missing keywords
        missing_keywords = response.get("missing_keywords", [])
        if missing_keywords:
            st.write("**Missing Keywords:**")
            st.write(", ".join(missing_keywords))

        # Display thoughts about the company and candidate
        thoughts_about_company = response.get("thoughts_about_company", "")
        thoughts_about_candidate = response.get("thoughts_about_candidate", "")
        if thoughts_about_company:
            st.write("**Thoughts about the Company:**")
            st.write(thoughts_about_company)
        if thoughts_about_candidate:
            st.write("**Thoughts about the Candidate:**")
            st.write(thoughts_about_candidate)

        st.success("Analysis Complete!")
        st.json(analysis)

        # Add a button to generate cover letter
        if "hellp" in st.session_state:
            logger.debug("Generate Cover Letter button clicked.")
            with st.spinner("Generating Cover Letter..."):
                # check if the session_state contains the necessary data
                if st.session_state.resume_text and st.session_state.job_description and st.session_state.company_info:
                    cover_letter = generate_cover_letter(
                        st.session_state.resume_text,
                        st.session_state.job_description,
                        st.session_state.company_info
                    )
                if cover_letter:
                    logger.debug("Cover letter generated successfully. Displaying result.")
                    st.markdown("### Generated Cover Letter")
                    st.write(cover_letter)
                    st.success("Cover Letter Generated!")
                else:
                    logger.error("Failed to generate cover letter.")
                    st.error("Failed to generate cover letter.")

# elif page == "Magic Write":
#     logger.debug("User selected 'Magic Write' page.")
#     st.title("🔮 Magic Write")
#     st.write("Enter lines from your resume to rephrase them according to ATS standards with quantifiable measures.")

#     text_to_rephrase = st.text_area("Text to Rephrase:")

#     if st.button("Rephrase"):
#         logger.debug("Rephrase button clicked.")
#         if text_to_rephrase:
#             logger.debug("Text to rephrase is provided. Starting rephrasing.")
#             with st.spinner("Rephrasing..."):
#                 rephrased_text = rephrase_text(text_to_rephrase)

#                 if rephrased_text:
#                     logger.debug("Rephrasing completed successfully. Displaying results.")
#                     st.markdown("### Rephrased Text:")
#                     st.write(rephrased_text)
#                     st.success("Rephrasing Complete!")
#                 else:
#                     logger.error("Rephrasing failed.")
#                     st.error("Failed to rephrase the text.")
#         else:
#             logger.error("No text provided to rephrase.")
#             st.error("Please enter the text you want to rephrase.")

elif page == "ATS Templates":
    logger.debug("User selected 'ATS Templates' page.")
    st.title("📄📝 Free ATS Resume Templates")
    st.write("Download free ATS-friendly resume templates. Click on a template to download it.")

    templates = {
        "Sample 1": "https://docs.google.com/document/d/1NWFIz-EZ1ZztZSdXfrrcdffSzG-uermd/export?format=docx",
        "Sample 2": "https://docs.google.com/document/d/1xO7hvK-RQSb0mjXRn24ri3AiDrXx6qt8/export?format=docx",
        "Sample 3": "https://docs.google.com/document/d/1fAukvT0lWXns3VexbZjwXyCAZGw2YptO/export?format=docx",
        "Sample 4": "https://docs.google.com/document/d/1htdoqTPDnG-T0OpTtj8wUOIfX9PfvqhS/export?format=docx",
        "Sample 5": "https://docs.google.com/document/d/1uTINCs71c4lL1Gcb8DQlyFYVqzOPidoS/export?format=docx",
        "Sample 6": "https://docs.google.com/document/d/1KO9OuhY7l6dn2c5xynpCOIgbx5LWsfb0/export?format=docx"
    }

    cols = st.columns(3)
    for index, (template_name, template_link) in enumerate(templates.items()):
        logger.debug(f"Displaying template: {template_name}")
        col = cols[index % 3]
        doc_id = template_link.split('/')[5]
        col.markdown(f"""
            <div style="text-align:center; margin-bottom: 20px;">
                <iframe src="https://docs.google.com/document/d/{doc_id}/preview" width="100%" height="200px" style="border: none;"></iframe>
                <br>
                <a href="{template_link}" target="_blank">Download {template_name}</a>
            </div>
        """, unsafe_allow_html=True)

elif page == "Find My Candidate":
    logger.debug("User selected 'Find My Candidate' page.")
    st.title("🔍 Find My Candidate")
    st.write("Enter the job description and company information to re-rank the profiles based on segment-specific scores and find the best candidate for your job opening.")

    job_description = st.text_area("Job Description:", placeholder="Enter job description here...")
    company_name = st.text_input("Company Name:")
    company_website_url = st.text_input("Company Website URL:")
    profiles = create_dummy_profiles()
    if st.button("Find Candidates"):
        logger.debug("Find Candidates button clicked.")
        if job_description.strip() and company_website_url and company_name:
            logger.debug("Job description provided. Starting candidate search.")
            with st.spinner("Extracting Company Information..."):
                company_info = get_scraped_company_data(company_name, company_website_url)
                st.write("Company Profile Extracted Successfully.")

            with st.spinner("Analyzing..."):
                time.sleep(2)
                profiles = recalculate_scores(profiles, job_description)
                profiles = profiles.sort_values(by="Overall Score", ascending=False)
                st.success("Profiles re-ranked based on the new job description.")
        else:
            logger.error("Job description or company name not provided.")
            st.error("Please enter the job description and company name.")
    st.markdown("### Top Candidates")
    st.dataframe(profiles, use_container_width=True)
