# 4. Data model

## Overview

The model is intentionally small. Five core tables cover every v1 use case:

```
Account ──┬──< Transaction
          └──< BalanceSnapshot

Category ──< CategorizationRule
Category ──< Transaction (via category_id)

NetWorthSnapshot  (denormalized, daily roll-up)
```

Plus an `import_run` table to audit CSV uploads.

## Entities

### `Account`
A logical financial account: a bank account, a credit card, a crypto wallet, etc.

| Field          | Type     | Notes                                                   |
| -------------- | -------- | ------------------------------------------------------- |
| `id`           | int PK   |                                                         |
| `name`         | str      | "ING Checking", "Revolut", "ETH Wallet 0xabc..."        |
| `kind`         | enum     | `checking`, `savings`, `credit_card`, `crypto`, `cash`, `investment` |
| `institution`  | str      | "ING", "Revolut", "Etherscan"                           |
| `currency`     | str (3)  | ISO code for fiat (`EUR`/`USD`/...). For crypto: `ETH`. |
| `external_ref` | str?     | For crypto: wallet address. Null for banks.             |
| `is_active`    | bool     | Hide closed accounts without losing history             |
| `created_at`   | datetime |                                                         |

**Note on investment accounts.** `kind='investment'` covers brokerage and fund accounts. Balance is tracked via `BalanceSnapshot` (entered manually or imported). Transactions represent cash deposits/withdrawals; individual positions and P&L are out of scope for v1.

**Note on the ETH account.** It lives in the same `Account` table with
`kind='crypto'` and `currency='ETH'`. Its native balance is in ETH, but its
contribution to **net worth** is computed as `balance_eth × eth_price_in_fiat`
at query time, using the most recent cached price.

### `Transaction`
A single posted transaction on an account.

| Field             | Type           | Notes                                                    |
| ----------------- | -------------- | -------------------------------------------------------- |
| `id`              | int PK         |                                                          |
| `account_id`      | FK Account     |                                                          |
| `posted_at`       | date           | The date the bank shows                                  |
| `amount`          | Decimal(18, 2) | Negative = outflow, positive = inflow                    |
| `currency`        | str(3)         | Almost always == account.currency, but stored for safety |
| `description`     | str            | Raw memo from the bank                                   |
| `merchant`        | str?           | Optional cleaned-up merchant name                        |
| `category_id`     | FK Category?   | Null until categorized                                   |
| `category_source` | enum           | `rule`, `manual`, `none`                                 |
| `external_id`     | str?           | The bank's own transaction ID if present in the CSV      |
| `import_run_id`   | FK ImportRun?  | Null for manually entered                                |
| `notes`           | text?          | Free-form user note                                      |
| `created_at`      | datetime       |                                                          |

**Deduplication.** On import, we hash `(account_id, posted_at, amount, description)`
and reject rows whose hash already exists. If the bank provides a stable
`external_id`, we prefer that.

### `BalanceSnapshot`
Periodic balance reading for an account — captured manually for some banks
(when CSV doesn't include running balance) and automatically for the ETH wallet.

| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `account_id` | FK Account | |
| `as_of` | datetime | When this balance was true |
| `balance` | Decimal(28, 8) | Wide enough for ETH |
| `source` | enum | `manual`, `csv`, `etherscan`, `derived` |
| `created_at` | datetime | |

`derived` snapshots are computed from prior snapshot + transactions in between,
so the dashboard can show a continuous balance line even when raw snapshots are
sparse.

### `Category`
Hierarchical-ish but flat in v1.

| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `name` | str unique | "Groceries", "Rent", "Transport / Fuel", ... |
| `parent_id` | FK Category? | For future grouping ("Food" → "Groceries", "Restaurants") |
| `color` | str(7) | Hex for charts |
| `is_income` | bool | True for salary/refunds; affects sign treatment in summaries |

A small seed list is created on first run (Groceries, Restaurants, Transport,
Rent/Mortgage, Utilities, Subscriptions, Income, Transfers, Other).

### `CategorizationRule`
Plain-text matching rules executed top-to-bottom on a transaction's description.

| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `priority` | int | Lower = evaluated first |
| `match_field` | enum | `description`, `merchant` |
| `match_kind` | enum | `contains`, `regex`, `equals` |
| `pattern` | str | The needle |
| `category_id` | FK Category | |
| `account_id` | FK Account? | Optional — restrict to one account |
| `is_active` | bool | |

Rules are evaluated in order; first match wins. Manual category overrides
*always* beat rule matches and are never overwritten on re-run.

### `NetWorthSnapshot`
Daily denormalized total for trend charts. Cheap to query, expensive to
recompute on the fly across a long range.

| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `as_of` | date unique | One row per calendar day |
| `total_fiat` | Decimal(18, 2) | Sum of all account balances in the user's base currency |
| `breakdown_json` | JSON | `{account_id: balance_in_base_currency, ...}` for stacked charts |
| `eth_price_used` | Decimal(18, 2)? | Audit trail for the conversion |

Recomputed nightly by the `snapshot_net_worth` job; old snapshots are immutable.

### `ImportRun`
Audit record for each CSV upload.

| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `account_id` | FK Account | |
| `filename` | str | |
| `file_hash` | str | Reject duplicate uploads of the same file |
| `row_count` | int | |
| `inserted_count` | int | |
| `skipped_count` | int | duplicates skipped |
| `started_at` | datetime | |
| `finished_at` | datetime | |
| `status` | enum | `success`, `partial`, `failed` |
| `error_log_json` | JSON? | Per-row errors for debugging |

## Currency handling (v1)

- A single `BASE_CURRENCY` env var (e.g. `EUR`).
- Fiat accounts are all in that currency — no FX needed.
- ETH balances are converted to base at query time using the most recent
  cached price. Historical net worth uses the price as of the snapshot date.
- **No multi-fiat support in v1.** The schema doesn't fight you if you add it
  later (currency is on every Account/Transaction), but the dashboards assume
  one fiat.

## ETH-specific handling

- The ETH account stores `external_ref` = wallet address.
- `BalanceSnapshot` rows are inserted by the `fetch_eth_balance` job (every 6 h).
- The ETH "transactions" view shows on-chain transfers fetched from Etherscan
  on demand — **not** stored in the `Transaction` table for v1, to avoid
  conflating on-chain noise with categorized spending.
- If you later want per-transaction history of the wallet, add a separate
  `crypto_transfer` table with its own model rather than overloading `Transaction`.

## Why not store more?

Skipped on purpose:
- **Budgets table** — deferred to v2 per the [roadmap](07-roadmap.md).
- **Tags table** — categorization covers v1; tags are a v2+ idea.
- **Recurring detection table** — derive it from transaction history when needed.
- **Attachments table (receipts)** — out of scope.
