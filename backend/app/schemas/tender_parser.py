from pydantic import BaseModel, Field

class TenderSection(BaseModel):
    title: str
    content: str

class TenderParseResponseData(BaseModel):
    file_name: str
    project_name: str = ""
    tender_company: str = ""
    deadline: str = ""
    qualification_requirements: list[str] = Field(default_factory=list)
    technical_requirements: list[str] = Field(default_factory=list)
    business_requirements: list[str] = Field(default_factory=list)
    scoring_rules: list[str] = Field(default_factory=list)
    sections: list[TenderSection] = Field(default_factory=list)
