# 5. Features (v1 / MVP)

The MVP is "Core + categories" from the planning Q&A. Each feature below has
acceptance criteria you can use as a checklist when implementing.

## F1 — Account management

**What:** CRUD for `Account` rows so you can register your 4 banks + 1 ETH
wallet up front.

**Screens:** `/accounts` list + a modal/drawer for create/edit.

**Acceptance:**
- [ ] Create an account with name, kind, institution, currency.
- [ ] For `kind=crypto`, the form requires a wallet address and validates it
      against the `0x[a-fA-F0-9]{40}` pattern.
- [ ] Soft-delete (set `is_active=false`) — never hard-delete, so historical
      transactions stay valid.

## F2 — CSV import

**What:** Per-bank CSV adapters that normalize into the canonical `Transaction`
shape. Upload happens from the UI; backend autodetects format from headers.

**Why per-bank adapters:** every bank exports a different schema, separator,
date format, and amount sign convention. A registry of adapters keyed by a
detection function keeps the rest of the code clean.

**Acceptance:**
- [ ] Upload a CSV from each of the 4 banks → adapter detected, parsed, stored.
- [ ] Re-uploading the same file is a no-op (file hash dedupe).
- [ ] Re-uploading a *different* file with overlapping rows correctly skips
      duplicates (transaction-level dedupe).
- [ ] Import summary shows: total rows, inserted, skipped, errors.
- [ ] Per-row errors are kept in `import_run.error_log_json` and visible in
      the import detail view.

**Adapter pattern (sketch):**

```python
class BankAdapter(Protocol):
    name: str
    def detect(self, headers: list[str], sample_rows: list[dict]) -> bool: ...
    def parse(self, file: BinaryIO) -> Iterator[ParsedTransaction]: ...
```

Adapters live in `app/imports/adapters/<bank_name>.py` and self-register via
an entry-point list. Add a new bank = add one file + one test fixture CSV.

## F3 — Manual transaction & balance entry

**What:** Forms to add a transaction or a balance snapshot when the bank doesn't
provide a CSV (or for one-off corrections like cash spending).

**Acceptance:**
- [ ] Add a transaction: account, date, amount, description, optional category.
- [ ] Add a balance snapshot: account, as-of datetime, balance.
- [ ] Edit any field of any transaction; edits set `category_source='manual'`
      so re-running rules won't overwrite.
- [ ] Delete a transaction (soft-delete with a `deleted_at` field, so net worth
      history stays consistent — or hard delete if you accept history shifts;
      pick one and document the choice in the implementation repo).

## F4 — Rule-based categorization

**What:** A simple rule engine that runs after every import and on demand.

**Acceptance:**
- [ ] Manage rules in a `/categories` (or `/rules`) UI: priority, match field,
      match kind, pattern, target category.
- [ ] "Re-run rules" button: applies rules to all transactions whose
      `category_source != 'manual'`.
- [ ] On import, every new transaction is categorized in one pass.
- [ ] If no rule matches, the category stays null and the transaction shows up
      in an "Uncategorized" filter at the top of the transactions view.

**Rule examples (seed list):**

| Pattern | Category |
|---|---|
| contains "MERCADONA" | Groceries |
| contains "RENFE" or "ALSA" | Transport |
| regex `^NÓMINA\b` | Income |
| contains "NETFLIX", "SPOTIFY", "ICLOUD" | Subscriptions |
| contains "TRANSFERENCIA" between own accounts | Transfers (excluded from spend) |

## F5 — Dashboard

**What:** Single landing page that answers "where am I, financially?" at a glance.

**Sections:**

1. **Net worth tile.** Big number + delta vs. last month. Sourced from the most
   recent `NetWorthSnapshot`.
2. **12-month net worth trend chart.** Stacked area by account from the daily
   snapshots, with ETH shown in its own band.
3. **Current month spending tile.** Sum of negative transactions in
   non-`is_income`, non-`Transfers` categories.
4. **Top 5 categories this month** as a horizontal bar chart, with a "see all"
   link to the monthly summary.
5. **Recent transactions** (last 10) with account, amount, category.

**Acceptance:**
- [ ] Loads in < 500 ms on the Pi for a year of data.
- [ ] All numbers tie out to the underlying `Transaction` / `BalanceSnapshot`
      data when you drill down.

## F6 — Monthly summary

**What:** `/months/:yyyy-mm` view: one row per category with totals, plus a
drill-down to the transactions that made up each row.

**Acceptance:**
- [ ] Pick any month with data → see income vs. spending totals.
- [ ] Category rows sorted by spend, with % of total.
- [ ] Click a category → list of its transactions for that month, sortable by
      amount and date.
- [ ] Transfers between own accounts are excluded by default; toggle to show.

## F7 — Transactions browser

**What:** `/transactions` table with filters: account, date range, category,
amount range, free-text on description.

**Acceptance:**
- [ ] Pagination or virtualized scrolling — don't render 5,000 DOM rows.
- [ ] Bulk actions: assign category to selected, mark as transfer.
- [ ] Export filtered view back to CSV (round-tripping is satisfying and
      occasionally useful).

## F8 — Auth (single user)

**What:** Login screen, session cookie, logout, password change.

**Acceptance:**
- [ ] Initial password set via env var on first run, then changeable in UI.
- [ ] Session cookie is `HttpOnly`, `SameSite=Lax`, `Secure` when behind HTTPS.
- [ ] Brute-force protection: rate-limit `/api/auth/login` (e.g. 5/min/IP).

## Explicitly deferred (post-MVP)

| Feature | Where it goes |
|---|---|
| Budgets & alerts | v2 — see [roadmap](07-roadmap.md) |
| Recurring transaction detection | v2 |
| In-app generative AI (chat / insights) | v3+ when revisited |
| Bank API integration (Plaid/GoCardless/Tink) | v3+ |
| Multi-currency fiat | only if needed |
| Multi-user / sharing | not planned |
| Receipts / attachments | not planned |
