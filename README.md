Business Decisions & Assumptions


KPI Status
Status is manually set by the user (they choose On Track / At Risk / Off Track)
System provides a suggested status based on math (the suggested_status property) but does not auto-apply it — user has final say
Thresholds for suggestion: ≥90% of target = On Track, 70–89% = At Risk, <70% = Off Track
These thresholds are arbitrary and can be changed per business need


Overall Project Status (kpi_summary)
Worst case wins — if even one KPI is Off Track, the whole project is Off Track
If no Off Track but any At Risk → project is At Risk
All On Track → project is On Track
Project with zero KPIs has status "No KPIs" — not counted as healthy or unhealthy


KPI Design (Flexibility)
KPIs are not hardcoded — each project can have any number of KPIs with any name
Each KPI has a unit field (%, $, score, units, etc.) — free text, not an enum — so it works for any measurement type
actual_value defaults to 0 on creation — assumption: new KPIs start with no progress recorded


Data Integrity
Deleting a Project cascades — all its KPIs are deleted automatically
KPIs cannot exist without a parent Project (no orphan KPIs)
target_value and actual_value must be ≥ 0 (enforced by MinValueValidator)


Ownership
owner is a plain text field (no user authentication system) — assumption: MVP scope, auth can be added later
No multi-tenancy — all users see all projects


Progress Calculation
progress_percent caps at 100% even if actual exceeds target — avoids confusing >100% display
Stored as decimal, not integer — allows values like 87.5%