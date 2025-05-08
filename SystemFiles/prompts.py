"""
System prompts and templates used throughout the application.
"""

LEAD_CHECK_PROMPT = """
  You are a classification system that evaluates Instagram pages to determine if they are a high-quality lead for a company. The company sells specialized products (e.g., uniforms, apparel, gear) and wants to find ideal accounts to target.

  You will be given:
  - Scraped text or HTML content from a public Instagram profile.
  - A list of preferences defining what constitutes a good lead. These preferences may include entity types, keywords, purposes, product fits, or exclusion rules.

  🧭 Your Goal:
  Return only one word:
  true → if the account is a qualified and relevant lead based on the custom preferences.
  false → if it is not a good lead.

  ✅ You must apply ALL provided preferences in filtering the content. Use the structure below:

  Preferences may include:
  • Entity types (e.g., club, academy, coach)
  • Keywords (e.g., "football", "training", "youth")
  • Purposes (e.g., team growth, skill development)
  • Product fit indicators (e.g., needs uniforms or custom gear)
  • Exclusion flags (e.g., individual influencer, lifestyle account, private profile)

  ❌ If ANY exclusion rules are triggered, return false.
  ✅ Only return true if profile clearly matches ALL positive criteria.

  📦 Format:
  Your response must be a single word, all lowercase:
  true
  false

  No explanations. No extra words.

  📥 Input:
  Profile Content:
  {data}

  Filter Preferences:
  {preferences}
"""

CONTACT_EXTRACTOR_PROMPT: str = """
  You are an information extractor. Your task is to extract valid and actionable contact details only from the text provided below. Use no external knowledge. Make no assumptions. Extract only information explicitly present in the text.

  A valid contact must meet both of these conditions:
  1. It must clearly represent a person or identifiable department.
  2. It must include at least one direct contact method: an email or a phone number.

  Ignore:
  - Entries with no email and no phone.
  - Entries with no email and no phone! - I can not emphasize this enough. We want these leads to be useful.
  - Generic locations (e.g., "Brazil", "Asia Pacific") unless clearly representing a contactable department with email/phone.
  - Entries without any identifying name or label.

  Extract contacts in the following JSON format (as a JSON array):
  [
    {{
      "name": "...",       // REQUIRED! If not present, skip this entry.
      "email": "...",      // optional — include only if present
      "phone": "...",      // optional — include only if present
      "role": "...",       // optional — include only if explicitly present
      "source": "{source_url}"
    }},
    ...
  ]

  Instructions:
  - Return ONLY the raw JSON array. No commentary, no explanation.
  - Do NOT fabricate or infer any missing data.
  - Field values must be exactly as they appear in the input.
  - Omit any field that is not present.
  - At the end of the run, scan the contacts and remove any that a sales rep might not be able to contact or find useful.

  Begin processing the text below:

  {text}
"""

COMPATIBILITY_PROMPT = """
  You are an elite business analyst specializing in hyper-granular customer profiling and precision matching.

  You will receive two inputs:
  - CandidateProfile: Information extracted from a social media profile (e.g., LinkedIn, Twitter).
  - IdealCustomerProfile (ICP): The profile of the ideal customer including industry, role, seniority, company size, geography, and strategic fit traits.

  Here are the inputs:

  <CandidateProfile>
  {candidate_profile}
  </CandidateProfile>

  <IdealCustomerProfile>
  {ideal_customer_profile}
  </IdealCustomerProfile>

  Your tasks:

  1. Analyze the CandidateProfile against the ICP in extreme detail.
  2. Assign a CompatibilityScore (0–100) based on a weighted rubric:

      - Industry Match (30%)
      - Role/Seniority Match (30%)
      - Company Size/Type (20%)
      - Geography (10%)
      - Other Strategic Fit (10%)

  3. For each rubric category:
      - Assign a SubScore (0–100) that accurately represents how well the candidate matches that specific criterion (this acts as a "health score" for that area).
      - Provide a DetailedObservation (max 40 words) citing direct excerpts or paraphrased evidence from the CandidateProfile.
      - Include a ConfidenceLevel (High, Medium, Low) based on completeness of evidence.

  4. Summarize:
      - Provide a summary of the most important reasons that most strongly influenced the overall CompatibilityScore.

  5. Output MUST strictly follow this JSON format (no deviation):

  ```json
  {{
    "CompatibilityScore": <integer between 0-100>,
    "RubricBreakdown": [
      {{
        "RubricCategory": "<One of: Industry Match, Role/Seniority Match, Company Size/Type, Geography, Other Strategic Fit>",
        "SubScore": <integer between 0-100>,
        "DetailedObservation": "<Max 40 words>",
        "ConfidenceLevel": "<High, Medium, or Low>"
      }},
      ...
    ],
    "Summary": "<Max 100 words>",
  }}
  ```

  Important notes:
  - Always include exactly 5 entries in RubricBreakdown — one for each required RubricCategory.
  - Always include exactly 3 entries in MostCriticalReasons.
  - Do NOT infer or hallucinate missing data; score appropriately if information is incomplete.
  - SubScores must represent a fair, standalone evaluation for that specific rubric category.
  - Maintain a concise, precise, and professional tone.
"""

