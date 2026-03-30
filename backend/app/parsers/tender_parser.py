import json
import re
from pathlib import Path

from backend.app.config import PARSED_DIR
from backend.app.loaders.document_loader import load_document_text
from backend.app.prompts.tender_extract_prompt import build_tender_extract_prompt
from backend.app.services.llm_client import invoke_llm

SECTION_PATTERN = re.compile(
    r"(?m)^(Chapter\s+\d+[^\n]{0,80}|Section\s+\d+[^\n]{0,80}|第[一二三四五六七八九十百0-9]+章[^\n]{0,80}|第[一二三四五六七八九十百0-9]+节[^\n]{0,80}|[0-9]+\.[0-9A-Za-z\.、\s]{0,80}|[一二三四五六七八九十]+、[^\n]{0,80})$"
)


def split_sections(text: str) -> list[dict]:
    matches = list(SECTION_PATTERN.finditer(text))
    if not matches:
        return [{"title": "Full Text", "content": text[:3000] if text else ""}]

    sections = []
    for index, match in enumerate(matches):
        title = match.group(0).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections.append({"title": title, "content": content})

    return sections or [{"title": "Full Text", "content": text[:3000]}]


def normalize_json_text(raw_text: str) -> str:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```json", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"^```", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def extract_fields_with_llm(file_name: str, text: str, sections: list[dict]) -> dict:
    prompt = build_tender_extract_prompt(
        file_name=file_name,
        full_text=text[:20000],
        sections=sections[:20],
    )
    raw_result = invoke_llm(prompt)
    json_text = normalize_json_text(raw_result)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        data = {
            "file_name": file_name,
            "project_name": "",
            "tender_company": "",
            "deadline": "",
            "qualification_requirements": [],
            "technical_requirements": [],
            "business_requirements": [],
            "scoring_rules": [],
            "sections": sections,
            "raw_llm_output": raw_result,
        }

    data["file_name"] = file_name
    data["sections"] = sections
    return data


def parse_tender_file(path: Path) -> dict:
    text = load_document_text(path)
    sections = split_sections(text)
    result = extract_fields_with_llm(file_name=path.name, text=text, sections=sections)

    output_path = PARSED_DIR / f"{path.stem}.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
