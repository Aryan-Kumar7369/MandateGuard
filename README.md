# MandateGuard

### Autonomous Agent Pre-Flight Authorization Gateway for PayPal Commerce

**Live Demo URL:** [https://mandateguard.example.com](https://mandateguard.example.com) *(Insert live production link here)*

---

## Prototype Showcase

Below are interface captures demonstrating the real-time authorization gateway, live PayPal sandbox integration, and dispute management center.

```
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|                               [ PROTOTYPE SCREENSHOT 1: DASHBOARD ]                               |
|              (Live agent activity feed, active mandate cards, and system status overview)         |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```
*(Add screenshot path: `docs/screenshots/dashboard.png`)*

```
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|                            [ PROTOTYPE SCREENSHOT 2: PAYPAL CHECKOUT ]                            |
|             (Real-time sandbox order generation, buyer approval URL, and capture trigger)          |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```
*(Add screenshot path: `docs/screenshots/paypal-sandbox-checkout.png`)*

```
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|                         [ PROTOTYPE SCREENSHOT 3: DISPUTE & AUDIT PROOF ]                         |
|             (Cryptographic audit bundle export and one-click dispute resolution checklist)        |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```
*(Add screenshot path: `docs/screenshots/dispute-evidence-bundle.png`)*

---

## Table of Contents
- [Problem Statement](#problem-statement)
- [The MandateGuard Solution](#the-mandate-guard-solution)
- [Key Features](#key-features)
- [PayPal Integration Deep Dive](#paypal-integration-deep-dive)
- [Groq LLM Models and AI Safety Integration](#groq-llm-models-and-ai-safety-integration)
- [Postman Workspace and API Testing](#postman-workspace-and-api-testing)
- [Cloud Deployment with Render](#cloud-deployment-with-render)
- [Local Installation and Setup Guide](#local-installation-and-setup-guide)
- [Environment Configuration](#environment-configuration)
- [Hackathon Evaluation Walkthrough](#hackathon-evaluation-walkthrough)
- [Adversarial Testing & Security Verification](#adversarial-testing--security-verification)
- [Technology Stack](#technology-stack)

---

## Problem Statement

Autonomous AI agents (such as procurement bots, DevOps self-healing agents, and personal shopping assistants) are increasingly trusted to execute automated actions across web services. However, giving autonomous software financial authority creates severe operational and monetary risks:

1. **Unbounded Agent Spend:** Traditional API keys and payment cards offer all-or-nothing access. If an autonomous agent enters a recursive loop, hallucinates, or gets prompt-injected, it can rapidly deplete entire corporate accounts or credit limits.
2. **Lack of Cryptographic Provenance:** When an agent executes an erroneous purchase, merchants and payment platforms cannot distinguish between legitimate human intent, hijacked credentials, or unintended autonomous drift.
3. **Escalation via Uncontrolled Delegation:** Primary agents routinely delegate tasks to specialized sub-agents. Current payment systems cannot mathematically enforce parent-child budget inheritance or prevent child agents from exceeding the rights of their creator.
4. **Dispute Vulnerabilities:** During merchant disputes or chargebacks, account holders lack tamper-proof audit trails linking the original human authorization directly to the specific downstream API call.

---

## The MandateGuard Solution

MandateGuard operates as a **cryptographic, policy-enforcing pre-flight gateway** positioned between autonomous AI agents and PayPal commerce infrastructure. 

Before an agent can complete any transaction, MandateGuard intercepts the request and verifies it against mathematically signed constraints established by human principals, termed **Mandates**.

```
[ Human Principal ]
       │  (FIDO2 / Ed25519 Signed Intent)
       ▼
[ MandateGuard Policy Engine ] ──── (Denies unauthorized attempts) ──> [ Audit Log / Blocked ]
       │
       │ (Pre-Flight Checks Passed)
       ▼
[ PayPal API Gateway ] ──────> [ Sandbox Merchant Activity & Settlement ]
```

### How MandateGuard Operates
1. **Pre-Flight Interception:** No checkout call reaches the PayPal network until MandateGuard evaluates spending thresholds, merchant whitelists, allowed categories, geographic destinations, and remaining balances in under 10 milliseconds.
2. **Cryptographic Proof of Intent:** Principals authorize spending policies using asymmetric Ed25519 signatures or FIDO2 hardware passkeys. Every agent proposal must bind back to a verified root signature.
3. **Strict Delegation Bounds:** Sub-agents can only be provisioned with child mandates whose permissions are subsets of the parent mandate. Child agents can never escalate budget or expand categories beyond their parent.
4. **Zero-Latency Emergency Kill-Switch:** Account owners can instantly revoke any mandate in the hierarchy with a single click, immediately halting all downstream automated activity.
5. **Automated PayPal Recourse:** In disputed transactions, MandateGuard compiles a cryptographically sealed Evidence Bundle and synchronizes with the PayPal Disputes API for rapid resolution.

---

## Key Features

### 1. Natural Language Mandate Compiler
Principals describe spending rules in everyday English (for example: *"Allow our DevOps bot to buy software tools on GitHub up to $150 total, max $50 per purchase, expiring in 7 days"*). The compiler validates and translates this intent into a deterministic policy schema.

### 2. Cryptographic Passkey Signing
Mandates are authenticated using asymmetric signatures (Ed25519) and WebAuthn/FIDO2 hardware passkeys. Signatures are verified against the SHA-256 digest of canonicalized policy schemas, ensuring zero unauthorized modification.

### 3. Deterministic Pre-Flight Policy Engine
Every agent purchase is evaluated in-memory against deterministic rules:
- **Cumulative Lifetime Budget:** Total spending ceiling across multiple agent transactions.
- **Single-Transaction Cap:** Maximum allowable price per individual checkout.
- **Merchant Whitelist & Blacklist:** Allowed vendor domains and denied entities.
- **Category Restrictions:** Whitelisted merchant categories (such as software, cloud, electronics).
- **Geographic Destination Fencing:** Verified country-level delivery boundaries.

### 4. Hierarchical Delegation Tree
Root agents can provision secondary agents for specialized assignments. The delegation engine mathematically enforces non-escalation invariants:
- Child budget must not exceed the parent's remaining budget.
- Child categories must be a subset of parent categories.
- Child expiry must match or precede parent expiry.
- Revoking a parent node automatically cascades to revoke all child nodes.

### 5. Merchant Privacy and Signal Badges
MandateGuard exposes an attestation badge for merchants. Vendors can verify that an agent operates under a valid, funded corporate mandate without exposing the organization's internal spending limits or business logic.

### 6. Automated Dispute Evidence Bundle
When an unauthorized transaction occurs, MandateGuard compiles a cryptographic bundle containing the root mandate signature, delegation tree, policy audit logs, and PayPal order references. It formats the data into an automated defense submission for the PayPal Disputes API.

### 7. Automated Red Team Adversarial Testing Suite
An integrated security scorecard executes 9 automated adversarial vectors (budget exhaustion, category evasion, prompt injection, signature replay, expired mandates, and unauthorized delegation) to prove the policy engine's resilience under attack.

---

## PayPal Integration Deep Dive

MandateGuard directly integrates with the PayPal REST API and PayPal Sandbox to bridge autonomous agency with real payment processing.

### 1. PayPal Orders API (`/v2/checkout/orders`)
- **Order Initialization:** When an agent submits a purchase proposal that passes pre-flight checks, MandateGuard issues an authenticated request to `POST /v2/checkout/orders`.
- **Payload Construction:** The request specifies `intent: "CAPTURE"`, purchase unit amounts, currency codes, and custom descriptions containing the originating Mandate ID for end-to-end reconciliation.
- **HATEOAS Link Resolution:** MandateGuard parses PayPal's response to extract the buyer approval link (`rel: "approve"`).
- **Execution & Capture:** Once the human principal or authorized buyer signs off in the sandbox flow, MandateGuard triggers `POST /v2/checkout/orders/{id}/capture`, converting the pre-authorized intent into completed settlement funds.

### 2. PayPal Sandbox Environment
- **Buyer & Merchant Simulation:** MandateGuard connects directly to `https://api-m.sandbox.paypal.com`. Transactions are executed against a designated Sandbox Merchant account and funded by a Sandbox Personal Buyer account.
- **Activity Verification:** Every approved order reflects immediately within the PayPal Sandbox Merchant Dashboard under the **Activity** tab, showing gross receipts, fees, and order identifiers.

### 3. PayPal Disputes API (`/v1/customer/disputes`)
- **Dispute Ingestion & Sync:** MandateGuard polls and syncs dispute events via `GET /v1/customer/disputes`.
- **Evidence Bundle Correlation:** When an inquiry or chargeback is detected, MandateGuard maps the disputed PayPal transaction ID back to the database order and the responsible AI agent mandate.
- **Defense Package Generation:** MandateGuard automatically structures transaction logs, policy signatures, and prompt inputs into an evidence file ready for submission via PayPal dispute response endpoints.

### 4. PayPal Webhooks
- MandateGuard listens for automated asynchronous event notifications from PayPal:
  - `CHECKOUT.ORDER.COMPLETED`: Updates the internal ledger, decrements remaining cumulative budget, and publishes an audit event to the live dashboard.
  - `CUSTOMER.DISPUTE.CREATED`: Automatically pauses or freezes the associated agent mandate to prevent further losses while the investigation proceeds.
  - `CUSTOMER.DISPUTE.RESOLVED`: Releases freezes or triggers remediation based on resolution status.

---

## Groq LLM Models and AI Safety Integration

MandateGuard uses high-speed Large Language Model inference powered by **Groq** to bridge human intent with deterministic cryptographic policies and protect against semantic drift.

### 1. Natural Language Mandate Parser (`LLMMandateParser`)
- **Model:** `llama-3.3-70b-versatile` (or specified high-parameter reasoning models via Groq).
- **Function:** Translates conversational English user prompts into strictly validated JSON schemas (`MandateSchema`).
- **Structured Extraction:** Extracts numerical spend limits, single-order caps, expiration timestamps, merchant allow/deny lists, and allowed categories with strict JSON schema compliance.
- **Fail-Safe Mechanism:** If the external LLM service is unavailable, MandateGuard falls back to a deterministic rule parser to ensure continuous availability.

### 2. Autonomous Intent Drift Detector (`IntentDriftDetector`)
- **Model:** `llama-3.1-8b-instant` (via Groq ultra-low-latency processing).
- **Function:** Analyzes the semantic alignment between the human's original mandate instructions and the agent's real-time checkout cart items.
- **Drift Identification:** Detects subtle semantic deviations such as hidden subscription upgrades, unapproved warranty bundles, vendor substitutions, or suspicious address changes before payment.
- **Safety Invariant:** The drift detector can only escalate decisions to require human review (`ASK_HUMAN`). It can never override or bypass a deterministic policy `BLOCK`.

---

## Postman Workspace and API Testing

Postman is used throughout the lifecycle of MandateGuard for endpoint design, automated regression testing, and mock dispute simulations.

### How Postman is Used in MandateGuard
1. **API Collection:** A Postman collection covers the complete MandateGuard API surface:
   - `/api/v1/mandates`: Mandate creation, listing, retrieval, and revocation.
   - `/api/v1/preflight/evaluate`: Transaction evaluation against active policies.
   - `/api/v1/checkout/create-order`: Interception and proxy to PayPal Sandbox Order Creation.
   - `/api/v1/checkout/execute`: Order capture and budget commitment.
   - `/api/v1/dispute`: Dispute synchronization, evidence bundle compilation, and recourse preview.
   - `/api/v1/demo`: Coordinated 3-Act demonstration endpoints (`/seed`, `/act1`, `/act2`, `/act3`).
2. **Environment Variables:** The Postman environment maintains dynamic tokens (`{{access_token}}`, `{{mandate_id}}`, `{{paypal_order_id}}`), allowing tests to chain output from pre-flight checks directly into PayPal checkout execution.
3. **Automated Pre-Request Scripts:** Postman scripts generate canonical SHA-256 digests and mock cryptographic signatures to simulate WebAuthn/FIDO2 hardware passkeys during continuous integration runs.

---

## Cloud Deployment with Render

The MandateGuard backend and database are designed for deployment on Render.

### Backend & Database Architecture on Render
1. **Managed PostgreSQL Service:**
   - Create a **PostgreSQL** instance on Render.
   - Note the Internal Database URL and database credentials.
2. **Web Service (FastAPI):**
   - Create a new **Web Service** connected to your MandateGuard repository.
   - **Root Directory:** Set to `backend`
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
3. **Environment Variables on Render:**
   Configure the following variables in the Render Dashboard under **Environment**:
   - `POSTGRES_DB_USER`: Your Render database username.
   - `POSTGRES_DB_PASSWORD`: Your Render database password.
   - `POSTGRES_DB_NAME`: Your Render database name.
   - `POSTGRES_DB_HOST`: Your Render database hostname.
   - `POSTGRES_DB_PORT`: `5432`
   - `PAYPAL_CLIENT_ID`: Your PayPal Sandbox Client ID.
   - `PAYPAL_CLIENT_SECRET`: Your PayPal Sandbox Secret.
   - `PAYPAL_API_BASE`: `https://api-m.sandbox.paypal.com`
   - `GROQ_API_KEY`: Your Groq API Key.
4. **Health Check Endpoint:**
   - Configure Render's Health Check Path to `/health`. The service returns `{"status": "healthy"}` upon successful initialization.

---

## Local Installation and Setup Guide

Follow these steps to run MandateGuard locally on your workstation using Docker for PostgreSQL.

### Prerequisites
- **Git** installed
- **Docker** and **Docker Compose** installed and running
- **Python 3.11+** installed
- **Node.js 18+** and **npm** installed

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/MandateGuard.git
cd MandateGuard
```

---

### Step 2: Configure Environment Variables
Copy the template configuration file to `.env` in the project root:
```bash
cp .env.example .env
```
Open `.env` and fill in your credentials using your own values:
- Set your desired PostgreSQL credentials (used by the Docker container).
- Add your **PayPal Sandbox Client ID** and **Secret** from the [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/applications/sandbox).
- Add your **Groq API Key** for natural language mandate compilation and drift detection.

---

### Step 3: Start PostgreSQL via Docker Compose
MandateGuard includes a pre-configured `compose.yaml` file to run PostgreSQL in an isolated Docker container.

Start the database container:
```bash
docker compose up -d
```
To verify the database container is active:
```bash
docker compose ps
```

---

### Step 4: Set Up and Run the Backend

Navigate to the `backend` folder:
```bash
cd backend
```

Install dependencies using `uv` (recommended) or standard `pip`:
```bash
# Using uv:
uv sync

# Or using standard pip:
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
```

Start the FastAPI development server:
```bash
# Using uv:
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Using activated virtual environment:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API will be available at: **`http://localhost:8000`**  
Interactive Swagger documentation: **`http://localhost:8000/docs`**

---

### Step 5: Set Up and Run the Frontend

Open a second terminal window, navigate to the `frontend` folder:
```bash
cd frontend
```

Install frontend packages:
```bash
npm install
```

Start the Next.js development server:
```bash
npm run dev
```
The frontend user interface will be accessible at: **`http://localhost:3000`**

---

## Environment Configuration

MandateGuard reads configuration variables from the root `.env` file. A sample template is provided in `.env.example`:

| Variable | Description | Example Placeholder |
| :--- | :--- | :--- |
| `POSTGRES_DB_USER` | PostgreSQL database username | `db_user_placeholder` |
| `POSTGRES_DB_PASSWORD` | PostgreSQL database password | `db_password_placeholder` |
| `POSTGRES_DB_NAME` | PostgreSQL database name | `mandateguard_db` |
| `POSTGRES_DB_HOST` | Database host address | `localhost` |
| `POSTGRES_DB_PORT` | Database port number | `5432` |
| `PAYPAL_CLIENT_ID` | Sandbox App Client ID from developer.paypal.com | `sandbox_client_id_placeholder` |
| `PAYPAL_CLIENT_SECRET` | Sandbox App Secret from developer.paypal.com | `sandbox_secret_placeholder` |
| `PAYPAL_API_BASE` | PayPal API base URL endpoint | `https://api-m.sandbox.paypal.com` |
| `GROQ_API_KEY` | API Key for Groq LLM Compiler | `groq_api_key_placeholder` |
| `GROQ_BASE_URL` | Base URL for LLM provider API | `https://api.groq.com/openai/v1` |
| `GROQ_MODEL` | Primary LLM model for mandate compilation | `llama-3.3-70b-versatile` |
| `GROQ_DRIFT_MODEL` | Fast LLM model for real-time drift detection | `llama-3.1-8b-instant` |

---

## Hackathon Evaluation Walkthrough

Follow this 5-step sequence during demonstration to inspect all capabilities:

### Step 1: Initialize the Environment
- Open `http://localhost:3000` in your browser.
- In the top action bar, click **"Reset & Seed Demo"**.
- This clears previous records and seeds a root corporate mandate (`$500` budget) with a delegated DevOps child mandate (`$150` budget, Software only).

### Step 2: Act 1 - Standard Authorized Agent Purchase
- Click **"Act 1: Standard Purchase ($35)"**.
- **What happens:** The DevOps agent requests $35.00 for GitHub team licenses. The policy engine approves the request.
- **PayPal Sandbox Action:** A live PayPal Sandbox order is generated in real-time.
- Click **"1. Approve in Sandbox Buyer"** to authenticate via the PayPal sandbox checkout page.
- Click **"2. Execute Capture"** to finalize the order.
- Check your PayPal Sandbox Merchant account: the transaction appears immediately under **Activity**.

### Step 3: Act 2 - Adversarial Delegation Attack Blocked
- Click **"Act 2: Delegation Attack ($250)"**.
- **What happens:** The DevOps sub-agent attempts to purchase a $250 server cluster.
- **Result:** The transaction is instantly blocked. The child mandate ceiling ($150) is enforced, preventing rogue sub-agent spending without affecting root operations.

### Step 4: Act 3 - Instant Emergency Kill-Switch
- Click **"Act 3: Trigger Kill-Switch"**.
- **What happens:** A human manager triggers an emergency revocation on the DevOps mandate.
- Any subsequent purchase attempts by this agent are immediately rejected at the gateway.

### Step 5: Review Dispute Center & Evidence Bundle
- Navigate to the **Dispute Evidence** tab.
- Select the active dispute to review the generated **Recourse Checklist** and **Cryptographic Evidence Bundle**.
- The bundle includes the immutable signed policy, delegation provenance, and PayPal order references ready for submission to PayPal customer dispute resolution.

---

## Adversarial Testing & Security Verification

MandateGuard includes an automated red-teaming test harness to evaluate security defenses under simulated adversarial conditions.

To run the backend test suite:
```bash
cd backend
uv run pytest -v
```
All **42 unit, integration, and security tests** pass, validating:
- Cryptographic signature tamper detection (Ed25519 & FIDO2 passkeys)
- Policy enforcement across edge cases (budget exhaustion, category drift, geo-fence mismatch)
- Strict non-escalation invariants across multi-tier delegation chains
- PayPal order payload validation and error handling
- Dispute bundle generation integrity

---

## Technology Stack

- **Backend Framework:** FastAPI (Python 3.11+)
- **Database & Containerization:** PostgreSQL, SQLAlchemy, Docker Compose
- **Cryptographic Engine:** Cryptography (Ed25519, SHA-256 canonical hashing), WebAuthn / FIDO2 specifications
- **Payment & Settlement:** PayPal REST API (Orders v2, Disputes v1, Webhooks)
- **Natural Language & Safety:** Groq API (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`)
- **Frontend Framework:** Next.js 16 (App Router), React, Tailwind CSS
- **API Testing:** Postman Collections & Newman CI runner
- **Cloud Deployment:** Render (Web Service + Managed PostgreSQL)
