# 6. Deployment

## Where the code lives

This `fintrack/` folder is documentation only.
The actual implementation will live in a separate repo, suggested layout:

```
~/Documents/projects/fintrack/
├── apps/
│   ├── api/              # FastAPI service
│   └── web/              # React + Vite + TS
├── infra/
│   ├── docker-compose.yml
│   ├── Caddyfile
│   └── backups/          # bind-mounted, git-ignored
├── docs/                 # symlink or copy of this fintrack/docs (or just link)
└── README.md
```

A monorepo with `apps/api` + `apps/web` keeps the API and frontend versioned
together while remaining easy to extract later.

## Pi 4 baseline

Assumed setup (adjust to your actual Pi state):

- Raspberry Pi OS 64-bit (Bookworm) on the SD/SSD.
- Docker + Compose plugin installed (Immich already runs this way).
- The Pi has a static LAN IP and an mDNS name (e.g. `raspberry.local`).
- No public exposure; SSH only from LAN.

**Coexistence with Immich.** Run the financial app as a *separate Compose
project* (`docker compose -p fintrack ...`) so its lifecycle and networks are
independent. Don't merge them into one `docker-compose.yml`.

## v1 deployment: local network only

### docker-compose.yml (sketch)

```yaml
name: fintrack

services:
  api:
    build: ../apps/api
    restart: unless-stopped
    environment:
      - APP_ENV=prod
      - DATABASE_URL=sqlite:////data/fintrack.db
      - BASE_CURRENCY=EUR
      - ETH_WALLET_ADDRESS=${ETH_WALLET_ADDRESS}
      - ETHERSCAN_API_KEY=${ETHERSCAN_API_KEY}
      - SESSION_SECRET=${SESSION_SECRET}
      - INITIAL_PASSWORD=${INITIAL_PASSWORD}  # only used on first boot
    volumes:
      - fintrack-data:/data
      - ./backups:/backups
    expose: ["8000"]

  web:
    build: ../apps/web
    restart: unless-stopped
    expose: ["80"]

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports: ["8080:80"]              # pick a port that doesn't clash with Immich
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config

volumes:
  fintrack-data:
  caddy-data:
  caddy-config:
```

### Caddyfile (LAN only)

```caddyfile
:80 {
  handle /api/* {
    reverse_proxy api:8000
  }
  handle {
    reverse_proxy web:80
  }
}
```

### Backups

Nightly backup script (runs in a small `litestream` or `alpine` sidecar, or as
a host-side cron job hitting the volume):

```bash
#!/usr/bin/env bash
set -euo pipefail
ts=$(date -u +%Y%m%dT%H%M%SZ)
sqlite3 /data/fintrack.db ".backup '/backups/fintrack-${ts}.db'"
gzip /backups/fintrack-${ts}.db
find /backups -name 'fintrack-*.db.gz' -mtime +30 -delete
```

**Test the restore.** A backup you haven't restored is not a backup. Once a
quarter, copy a backup onto a fresh container and verify the dashboard still
loads.

## Future remote-access options

Listed cheapest-to-setup first. Pick one when v1 is stable; you don't need any
of these to start.

### Option A — Tailscale (recommended)

- Install the Tailscale daemon on the Pi.
- Add your phone, laptop, etc. to the same tailnet.
- The app stays on `:8080` (or whatever) and you reach it via the Pi's
  Tailscale IP / MagicDNS name (e.g. `https://raspberry.tail-xxxx.ts.net:8080`).
- **Pros:** zero port forwarding, end-to-end encrypted, works through CGNAT,
  free for personal use, MFA via your existing identity provider.
- **Cons:** dependency on Tailscale's coordination service (not data plane).

### Option B — Cloudflare Tunnel

- Run `cloudflared` on the Pi, point it at `caddy:80`.
- Cloudflare gives you a public hostname (free `*.trycloudflare.com` or use a
  domain you own).
- Add Cloudflare Access in front for SSO/MFA before traffic hits the tunnel.
- **Pros:** real public URL without exposing your home IP; great for sharing
  read-only views with someone if you ever change your mind.
- **Cons:** traffic goes through Cloudflare; not appropriate if you want to
  keep finance data off third-party networks.

### Option C — WireGuard (DIY VPN)

- Stand up your own WireGuard endpoint on the Pi or a cheap VPS.
- Same usage shape as Tailscale, but you manage keys, peers, and a public IP.
- **Pros:** fully self-hosted, no third-party.
- **Cons:** real ops burden — key rotation, NAT traversal, mobile config.

### Option D — Port-forward + DDNS + public TLS (not recommended)

- Forward 443 to the Pi, set up DuckDNS, put Caddy in TLS mode with
  Let's Encrypt.
- **Don't do this** for a finance app unless you've added 2FA, fail2ban,
  rate limits, and have a strong reason to need a public URL.

## When to bring AWS into the picture

Optional, only because you flagged AWS as a learning goal. Reasonable
"learning hooks" that match this app:

| AWS service | Use | Why useful |
|---|---|---|
| S3 + lifecycle to Glacier | Off-site encrypted DB backups | IAM, S3, lifecycle rules, KMS — covers a lot of cloud fundamentals cheaply |
| CloudWatch Logs (via OTEL or `cloudwatch` agent) | Ship Pi container logs to AWS | Centralized log viewing without standing up Loki/ELK |
| Route 53 + ACM | Domain + cert if you ever go public | Real DNS practice |
| Lambda + EventBridge | Daily "is the Pi alive?" healthcheck pings | Serverless basics |

Do these one at a time, only when the v1 app itself is stable. Don't let AWS
yak-shaving block you from shipping the local-only version.

## CI/CD

Split across two phases:

**Phase 1 — Basic CI (do this early):**
- `ruff` + `mypy` + `pytest` for the API on every push and PR.
- Frontend job (`eslint` + `tsc` + `vitest`) added at the end of Phase 2.
- Workflow file: `.github/workflows/ci.yml`. Full config in
  [`09-developer-roadmap.md`](09-developer-roadmap.md) Step 1.8.

**Phase 6 — CD (after v1 is stable):**
1. **Build images:** push to GHCR for `linux/arm64` using QEMU.
2. **Deploy:** SSH to Pi, `docker compose pull && docker compose up -d`.

Don't set up CD until manual deploys become genuinely annoying.
