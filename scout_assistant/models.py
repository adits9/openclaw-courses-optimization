from dataclasses import asdict, dataclass
from typing import Dict, List, Optional


@dataclass
class ParsedRequest:
    company: str
    university: Optional[str]
    role: Optional[str]
    count: int
    raw_message: str


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


@dataclass
class RecruiterLead:
    name: str
    title: str
    company: str
    source_url: str
    linkedin_url: Optional[str] = None
    public_email: Optional[str] = None
    confidence: str = "low"
    confidence_reason: str = "Insufficient signal"
    match_reason: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SessionState:
    leads: List[RecruiterLead]
    parsed_request: Optional[ParsedRequest] = None

