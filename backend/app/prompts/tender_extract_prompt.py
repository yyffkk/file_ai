import json


def build_tender_extract_prompt(file_name: str, full_text: str, sections: list[dict]) -> str:
    sections_text = json.dumps(sections, ensure_ascii=False, indent=2)
    return f"""You are a tender document extraction assistant.
Extract key fields from the tender document and return JSON only.
Do not return explanations or markdown code fences.

Return exactly this JSON structure:
{{
  "file_name": "{file_name}",
  "project_name": "",
  "tender_company": "",
  "deadline": "",
  "qualification_requirements": [],
  "technical_requirements": [],
  "business_requirements": [],
  "scoring_rules": [],
  "sections": []
}}

Field rules:
- project_name: project name
- tender_company: tender company / buyer
- deadline: bid deadline, empty string if not found
- qualification_requirements: array of strings
- technical_requirements: array of strings
- business_requirements: array of strings
- scoring_rules: array of strings
- sections: keep as an empty array, the program will fill it back later

If a field cannot be confirmed, use an empty string or empty array. Do not hallucinate.

File name:
{file_name}

Sections:
{sections_text}

Full text (may be truncated):
{full_text}
"""
