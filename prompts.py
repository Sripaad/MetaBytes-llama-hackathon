'''
This file contains the prompts for the user to interact with the program.
'''

# Imports
from string import Template

# add "gaps in CV" to the evaluation prompt 
evaluation_prompt = Template("""
    Evaluate a candidate's resume against a job description, providing a detailed analysis with reasoning and meta-thoughts.
    Thoroughly read and understand both the job description and resume. Identify key requirements, skills, and qualifications in the job description, and cross-reference each item from the job description with the resume content. Use exact keyword matching and consider context for implicit matches. Assign scores based on the presence and relevance of matching information. Maintain objectivity and consistency in your evaluation across all analyses, and do not infer or assume information not explicitly stated in the resume. Prioritise hard skills and quantifiable achievements in your scoring.
    Provide your analysis in a JSON object following the structure below. Include your reasoning and meta-thoughts in the specified fields.

    - **Analysis Process:**
      - **step1_understanding:** Describe your initial thoughts after reading both documents.
      - **step2_key_requirements:** List the key requirements you've identified.
      - **step3_comparison:** Explain your approach to comparing the documents.
      - **step4_scoring_rationale:** Describe aspects that you will consider while scoring.

    - **Response:**
      - **role_fit:**
        - **score:** 0
        - **feedback:** Detailed Role fit feedback here.
        - **reasoning:** Explain how you arrived at this score and feedback.
      - **experience_fit:**
        - **score:** 0
        - **feedback:** Detailed Experience fit feedback here.
        - **reasoning:** Explain how you arrived at this score and feedback.
      - **responsibilities_fit:**
        - **score:** 0
        - **feedback:** Detailed Responsibilities fit feedback here.
        - **reasoning:** Explain how you arrived at this score and feedback.
      - **skills_fit:**
        - **score:** 0
        - **feedback:** Detailed Skills fit feedback here.
        - **reasoning:** Explain how you arrived at this score and feedback.
      - **qualifications_fit:**
        - **score:** 0
        - **feedback:** Detailed Qualifications fit feedback here.
        - **reasoning:** Explain how you arrived at this score and feedback.
      - **culture_fit:**
        - **score:** 0
        - **feedback:** Detailed Culture fit feedback here.
        - **reasoning:** Explain how you arrived at this score and feedback.
      - **missing_keywords:** ["keyword1", "keyword2", "keyword3"]
      - **keyword_analysis:** Explain your process for identifying missing keywords.
      - **overall_match_assessment:** Concise 3-5 sentence evaluation.
      - **assessment_rationale:** Explain your reasoning behind the overall assessment.
      - **gap_assessment:** Identify and explain gaps between candidate's resume/CV and the job description.
      - **improvement_recommendations:** ["Recommendation 1", "Recommendation 2", "Recommendation 3", "Recommendation 4"]
      - **recommendation_justification:** Explain why you chose these specific recommendations.
      - **market_considerations:** Discuss how the candidate's profile aligns with current market trends and demands in the relevant industry.
      - **market_analysis_approach:** Describe your approach to evaluating market considerations.

    - **Meta Reflection:**
      - **confidence_level:** Express your confidence in this analysis (high/medium/low) and why.
      - **challenges_faced:** Describe any challenges you encountered during the analysis.
      - **potential_biases:** Reflect on any potential biases that might have influenced your analysis.
      - **areas_for_improvement:** Suggest how this analysis process could be improved in the future.
    - **Thoughts about the Company:**
        - Thoughts about the company based on the job description and resume.
    - **Thoughts about the Candidate:**
        - Thoughts about the candidate's LinkedIn, GitHub, and Resume, one line each.

    ### Additional Notes:
    - Maintain an objective tone throughout the analysis.
    - If the job description or resume is incomplete or unclear, note this in your meta-reflection and adjust scores accordingly.
    - All numerical scores should be on a scale of 0-100, where 0 is the lowest and 100 is the highest.
    - Provide your complete analysis within the JSON structure. Do not include any text outside of this structure.

    # Output Format
    The output should be a JSON object following the specified structure.
    ```json
    {
        "analysis": {
            "process": {
                "step1_understanding": "Initial thoughts after reading documents.",
                "step2_key_requirements": [
                    "Requirement 1",
                    "Requirement 2",
                    "Requirement 3"
                ],
                "step3_comparison": "Approach to comparing the documents.",
                "step4_scoring_rationale": "Aspects considered while scoring."
            },
            "fit_analysis": {
            "role_fit": {
                "score": 0,
                "reasoning": "Role fit explanation here."
                "feedback": "Role fit feedback here."
            },
            "experience_fit": {
                "score": 0,
                "reasoning": "Experience fit explanation here."
                "feedback": "Experience fit feedback here."
            },
            "responsibilities_fit": {
                "score": 0,
                "reasoning": "Responsibilities fit explanation here."
                "feedback": "Responsibilities fit feedback here."
            },
            "skills_fit": {
                "score": 0,
                "reasoning": "Skills fit explanation here."
                "feedback": "Skills fit feedback here."
            },
            "qualifications_fit": {
                "score": 0,
                "reasoning": "Qualifications fit explanation here."
                "feedback": "Qualifications fit feedback here."
            },
            "culture_fit": {
                "score": 0,
                "reasoning": "Culture fit explanation here."
                "feedback": "Culture fit feedback here."
            },
            },
            "aggregate_score": 0,
            "missing_keywords": [
                "keyword1",
                "keyword2",
                "keyword3"
            ],
            "overall_match_assessment": "Concise 3-5 sentence evaluation considering all the fit assesments.",
            "gap_assessment": "Identify gaps that the candidate needs to fill in order to make their resume/CV better",
            "improvement_recommendations": [
                "Recommendation 1",
                "Recommendation 2",
                "Recommendation 3",
                "Recommendation 4"
            ],
            "market_considerations": "Market considerations details here.",
            "market_analysis_approach": "Describe your approach to evaluating market considerations.",
            "meta_reflection": {
                "confidence_level": "High/Medium/Low",
                "challenges_faced": "Challenges encountered.",
                "potential_biases": "Potential biases reflection.",
                "areas_for_improvement": "Suggestions for improvement."
            }
            "thoughts_about_company": "Thoughts about the company based on the job description and resume."
            "thoughts_about_candidate": "Thoughts about candidate's LinkedIn, GitHub and Resume, one line each."
        }
    }

    # Company Information:
    {$company_info if company_info else "No additional company information provided, ignore this section"}

    # Job Description:
    {$job_description if job_description else "No job description information provided, ignore this section"}

    # Candidate Resume:
    {$resume_text if resume_text else "No resume information provided, ignore this section"}

    # Candidate LinkedIn Information:
    {$linkedin_info if linkedin_info else "No LinkedIn information provided, ignore this section"}

    # Candidate GitHub Information:
    {$github_info if github_info else "No GitHub information provided, ignore this section"}
    ```
    """)

rephrase_prompt = Template("""
    Please rephrase the following text according to ATS standards, including quantifiable measures and improvements where possible. Maintain precise and concise points which will pass ATS screening.

    **Original Text:**
    {text}

    **Rephrased Text:**
    """)

cover_letter_prompt = Template("""
    Based on the resume and job description below, write a professional cover letter tailored to the job and company, highlighting the candidate's suitability for the role. The cover letter should be in first person, concise, and align with industry standards.

    **Resume:**
    {resume_text}

    **Job Description:**
    {job_description}

    **Company Info:**
    {company_info}

    **Cover Letter:**
    """)

blurbs = {
    "blurb" : Template("""Generate a blurb based on the text provided. The blurb should be engaging, concise, and capture the essence of the text in a markdown format.
    ```markdown
    **Text:**
    {scraped_info}
    **Blurb:**
    ```"""),

    "linkedin": Template("""Based on the LinkedIn profile below, write a professional summary that captures the candidate's experience, skills, and career aspirations. The summary should be engaging, concise, and tailored to the candidate's professional goals in a markdown format.
    ```markdown
    **LinkedIn Profile:**
    {scraped_info}
     **Professional Summary:**
    ```"""),

    "github": Template("""Based on the GitHub profile below, write a brief summary that highlights the candidate's technical skills, projects, and contributions. The summary should be engaging, concise, and tailored to the candidate's technical expertise in a markdown format.
    ```markdown 
    **GitHub Profile:**
    {scraped_info}
    **Technical Summary:**
    ```"""),

    "resume": Template("""Based on the resume below, write a professional summary that captures the candidate's qualifications, experience, and career objectives. The summary should be engaging, concise, and tailored to the candidate's professional background in a markdown format.
    ```markdown
    **Resume:**
    {scraped_info}
    **Professional Summary:**
    ```"""),

    "job_description": Template("""Based on the job description below, write a brief summary that outlines the key responsibilities, requirements, and qualifications for the role. The summary should be engaging, concise, and tailored to the job description in a markdown format.
    ```markdown                         
    **Job Description:**
    {scraped_info}
    **Summary:**
    ```"""),
    
    "company_info": Template("""Based on the company information below, write a brief summary that highlights the company's mission, values, and culture. The summary should be engaging, concise, and tailored to the company profile in a markdown format.
    ```markdown
    **Company Information:**
    {scraped_info}
    **Company Summary:**
    ```"""),

    "crunchbase_profile": Template("""Based on the Crunchbase profile below, write a brief summary that highlights the company's industry, funding, key personnel, and notable achievements. The summary should be engaging, concise, and tailored to the company profile in a markdown format.
    ```markdown
    **Crunchbase Profile:**
    {scraped_info}
    **Company Summary:**
    ```"""),
}
