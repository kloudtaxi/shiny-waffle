"""Background employees. None may hold VP Sales or CRO: the truth has exactly one of each."""

from __future__ import annotations

from datetime import date
from typing import Literal

from polyfactory import Use
from pydantic import BaseModel

from northstar.factories._base import SeededFactory

Title = Literal[
    "Enterprise Account Executive",
    "Sales Engineer",
    "Sales Operations Analyst",
    "Customer Success Manager",
    "Financial Analyst",
    "Accounts Receivable Specialist",
]
Location = Literal["Chicago, IL", "Milwaukee, WI", "Indianapolis, IN", "Remote"]

DEPARTMENT_OF: dict[str, str] = {
    "Enterprise Account Executive": "Sales",
    "Sales Engineer": "Sales",
    "Sales Operations Analyst": "Sales",
    "Customer Success Manager": "Sales",
    "Financial Analyst": "Finance",
    "Accounts Receivable Specialist": "Finance",
}
# Background staff hang off the truth's managers so the org chart stays one tree.
MANAGER_OF_DEPARTMENT = {"Sales": "EMP-200", "Finance": "EMP-402"}
ROLE_OF_TITLE = {"Enterprise Account Executive": "ENTERPRISE_AE"}


class BgEmployee(BaseModel):
    id: str
    name: str
    title: Title
    department: str
    manager: str
    location: Location
    hire_date: date

    @property
    def role(self) -> str | None:
        return ROLE_OF_TITLE.get(self.title)


class EmployeeFactory(SeededFactory[BgEmployee]):
    name = Use(lambda: EmployeeFactory.fake().name_nonbinary())
    hire_date = Use(lambda: EmployeeFactory.date_in_window(date(2015, 1, 1), date(2024, 12, 31)))
    department = Use(lambda: "")
    manager = Use(lambda: "")
