from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TenderData:
    source: str
    title: str
    country: str
    description: str
    posting_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    url: Optional[str] = None
    external_id: Optional[str] = None

    def __post_init__(self) -> None:
        self.source = self.source.strip() if self.source else ""
        self.title = self.title.strip() if self.title else ""
        self.country = self.country.strip() if self.country else ""
        self.description = self.description.strip() if self.description else ""
        self.url = self.url.strip() if self.url else None
        self.external_id = self.external_id.strip() if self.external_id else None

    def validate(self) -> list[str]:
        errors: list[str] = []

        if not self.source:
            errors.append("TenderData.source is required.")
        if not self.title:
            errors.append("TenderData.title is required.")
        if not self.country:
            errors.append("TenderData.country is required.")
        if not self.description:
            errors.append("TenderData.description is required.")

        if self.posting_date and self.deadline and self.deadline < self.posting_date:
            errors.append("TenderData.deadline cannot be earlier than posting_date.")

        if self.url and not (self.url.startswith("http://") or self.url.startswith("https://")):
            errors.append("TenderData.url must start with http:// or https://.")

        return errors


@dataclass
class CompanyProfileInput:
    name: str
    description: str = ""
    sectors: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    max_budget: Optional[float] = None

    def __post_init__(self) -> None:
        self.name = self.name.strip() if self.name else ""
        self.description = self.description.strip() if self.description else ""
        self.sectors = [s.strip() for s in self.sectors if isinstance(s, str) and s.strip()]
        self.keywords = [k.strip() for k in self.keywords if isinstance(k, str) and k.strip()]
        self.locations = [loc.strip() for loc in self.locations if isinstance(loc, str) and loc.strip()]

    def validate(self) -> list[str]:
        errors: list[str] = []

        if not self.name:
            errors.append("CompanyProfileInput.name is required.")

        if self.max_budget is not None and self.max_budget < 0:
            errors.append("CompanyProfileInput.max_budget cannot be negative.")

        return errors


@dataclass
class ProposalInput:
    tender: TenderData
    company_profile: CompanyProfileInput

    def validate(self) -> list[str]:
        return self.tender.validate() + self.company_profile.validate()

    @property
    def is_valid(self) -> bool:
        return len(self.validate()) == 0
