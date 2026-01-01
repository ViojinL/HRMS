from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from django.db import connection


@dataclass(frozen=True)
class UserScope:
    user_id: int
    is_superuser: bool
    is_staff: bool
    emp_pk: str | None
    org_id: str | None
    position: str
    org_name: str
    is_manager: bool
    is_hr: bool


def get_user_scope(*, user_id: int, is_superuser: bool, is_staff: bool) -> UserScope:
    """Resolve user -> employee/org scope using raw SQL (no ORM)."""

    emp_pk: str | None = None
    org_id: str | None = None
    position = ""
    org_name = ""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT emp.id, emp.org_id, COALESCE(emp.position, ''), COALESCE(org.org_name, '')
            FROM employee emp
            JOIN organization org ON emp.org_id = org.id
            WHERE emp.is_deleted = FALSE
              AND org.is_deleted = FALSE
              AND emp.user_id = %s
            LIMIT 1
            """,
            [user_id],
        )
        row = cursor.fetchone()
        if row:
            emp_pk, org_id, position, org_name = row

    is_manager = False
    is_hr = False
    if emp_pk:
        pos_upper = (position or "").upper()
        org_upper = (org_name or "").upper()
        is_hr = ("人力" in (org_name or "")) or ("HR" in pos_upper) or ("HR" in org_upper) or is_staff

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM organization org
                WHERE org.is_deleted = FALSE
                  AND org.manager_emp_id = %s
                LIMIT 1
                """,
                [emp_pk],
            )
            is_manager = cursor.fetchone() is not None

    return UserScope(
        user_id=user_id,
        is_superuser=is_superuser,
        is_staff=is_staff,
        emp_pk=emp_pk,
        org_id=org_id,
        position=position,
        org_name=org_name,
        is_manager=is_manager,
        is_hr=is_hr,
    )


def build_org_tree_cte(root_org_ids: Sequence[str]) -> tuple[str, list[Any]]:
    """Build a recursive CTE for organization subtree. Postgres-friendly."""

    if not root_org_ids:
        return (
            "WITH org_tree AS (SELECT NULL::varchar AS id WHERE FALSE)",
            [],
        )

    values_sql = ", ".join(["(%s)"] * len(root_org_ids))
    cte_sql = (
        "WITH RECURSIVE roots(id) AS (VALUES "
        + values_sql
        + ") , org_tree AS ("
        "SELECT id FROM roots "
        "UNION ALL "
        "SELECT o.id FROM organization o "
        "JOIN org_tree t ON o.parent_org_id = t.id "
        "WHERE o.is_deleted = FALSE"
        ")"
    )
    return cte_sql, list(root_org_ids)


def normalize_str(value: Any) -> str:
    return "" if value is None else str(value).strip()


def parse_iso_date(value: str | None) -> str | None:
    """Accept YYYY-MM-DD, return same string or None."""

    v = normalize_str(value)
    if not v:
        return None
    # Let DB parse; just basic sanity check for length.
    if len(v) != 10:
        return None
    return v


def parse_iso_datetime_local(value: str | None) -> str | None:
    """Accept datetime-local string (YYYY-MM-DDTHH:MM[:SS]) and return it as-is.

    We pass it into DB as timestamp; Django/psycopg2 will adapt string.
    """

    v = normalize_str(value)
    if not v:
        return None
    if "T" not in v and " " not in v:
        return None
    return v


def uniq(seq: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
