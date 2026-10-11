"""`PersonRef` lookups over the HR export (the corpus's `employees` table)."""

from __future__ import annotations

from .errors import NotFound
from .models import PersonRef


class People:
    def __init__(self, staff: list[dict[str, str]]) -> None:
        self._by_id = {r["employee_id"]: r for r in staff}
        self._staff = staff

    def _ref(self, r: dict[str, str]) -> PersonRef:
        return PersonRef(
            id=r["employee_id"], name=r["full_name"], title=r["title"], function=r["department"]
        )

    def ref(self, emp_id: str) -> PersonRef:
        if emp_id not in self._by_id:
            raise NotFound(f"employee {emp_id}")
        return self._ref(self._by_id[emp_id])

    def by_email(self, email: str) -> PersonRef | None:
        want = email.strip().lower()
        return next((self._ref(r) for r in self._staff if r["email"].lower() == want), None)

    def by_name(self, name: str) -> PersonRef | None:
        """The one employee with this full name; None if there is none; ValueError if several."""
        want = name.strip().lower()
        found = [r for r in self._staff if r["full_name"].lower() == want]
        if len(found) > 1:
            raise ValueError(f"the name {name!r} is not unique")
        return self._ref(found[0]) if found else None

    def function_of(self, emp_id: str) -> str:
        return self.ref(emp_id).function
