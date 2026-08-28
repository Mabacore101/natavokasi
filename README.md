# Job Board Platform — Progress Notes

Internship (Kerja Praktik) project: a job-board platform connecting employers/agencies
with candidates for international job placements, with structured qualification
requirements (e.g. minimum language proficiency) that candidates can filter by.

**Status:** In progress, no hard deadline — continuing as a side project after
internship hours. Supervisor has confirmed the design (flowchart) and left all
implementation decisions up to me.

---

## Tech Stack

- **Backend:** Django
- **Frontend:** Server-rendered Django templates (plain HTML/CSS/JS, no separate
  frontend framework, no REST API layer)
- **Database:** SQLite (no external services — deployment not required)
- **Version control:** Git + GitHub

---

## Locked Scope Decisions (do not re-litigate)

- Keep **both** admin review gates as separate steps (account verification, then
  job legality review) — not combined, even though it costs more build time.
- Keep **full interactive qualification Q&A matching** at apply-time — not
  simplified to a basic review-and-confirm step.
- No deployment required — local dev only. Supervisor evaluates progress, not a
  finished live product.

---

## Data Model (implemented)

- **`User`** (custom, set as `AUTH_USER_MODEL` before first migrate) — `role`:
  admin / employer / candidate
- **`EmployerProfile`** (1:1 `User`) — `company_name`, `business_doc_note`,
  `verification_status` (pending / verified / rejected_suspended), `reviewed_by`,
  `reviewed_at`
- **`Job`** — `employer` (FK), `title`, `description`, `country`, `city`,
  `salary_min`, `salary_max`, `currency`, `quota`, `status` (draft /
  pending_review / revision_requested / live / closed_filled)
- **`JobQualification`** — `job` (FK), `category` (language / education /
  experience / age / certification), `label`, `min_value`, `min_value_label`
- **`Application`** — `candidate` (FK), `job` (FK), `status` (submitted /
  reviewed / accepted / rejected), `applied_at`. `unique_together
  ('candidate', 'job')`.
- **`ApplicationAnswer`** — `application` (FK), `qualification` (FK),
  `candidate_value`, `meets_requirement`. `unique_together ('application',
  'qualification')`.

## Django Admin (implemented)

- **`EmployerProfileAdmin`** — Gate 1 (account verification). List
  display/filter/search + `approve_employers` / `reject_employers` actions
  that set `verification_status`, `reviewed_by`, and `reviewed_at` together.
- **`JobAdmin`** — Gate 2 (job legality review). List display/filter/search +
  `approve_jobs` / `request_revision` actions, with `JobQualification` as a
  `TabularInline`.
- Confirmed only `role='admin'` accounts have `is_staff=True` (admin panel
  access is gated separately from the `role` field — keep these in sync).

---

## Next Up — Step 4: Candidate-facing flow (~1.5–2h)

- Browse/filter job listings by structured qualification (e.g. minimum
  language level)
- Job detail view
- Apply flow with interactive Q&A matching against `JobQualification`
  (populates `Application` + `ApplicationAnswer`)

## After That

- **Step 5:** Employer-facing flow — registration, dashboard, post-job form
  with structured qualifications, view own jobs/applicants (~1.5–2h)
- **Step 6:** Light template/styling pass
- **Step 7:** Seed demo data for an end-to-end walkthrough
- **Step 8:** Keep this README updated as progress continues

---

## Open / To Confirm

- `ApplicationAnswer.meets_requirement` — confirm this is computed once at
  submit-time and stored (not recomputed live on every view), to avoid stale
  data if `JobQualification.min_value` changes later.

## Resuming a Session

If picking this up in a new chat, paste this README for context, plus the
flowchart image if design details are needed.
