# Data Governance & Pipeline Reliability Specification

This document details the architectural rules, data contracts, and operational guardrails governing data ingestion, transformation, and structural validation within the AI Tender  platform.

The goal of this framework is to transition the platform from an MVP script into a reliable, production-ready system. It establishes explicit validation gates to eliminate corrupted writes, guarantees zero duplicate API costs through deterministic keys, and ensures absolute pipeline idempotency.

---

## 1. Data Contracts (Canonical Schema)

To decouple our processing pipeline from varying, unpredictable layout structures found across separate web sources, all scraped data must pass through a strict translation and validation gate before hitting our application memory or database storage layers.

### 1.1 Structural Mapping & Validation Strategy

The system uses dynamic mapping dictionaries to normalize variable key names. However, simple field renaming is prone to failure if a vendor site changes its layout. To harden this step, the output of every mapping configuration is strictly validated against a **Pydantic Data Contract**.

|        Aspect        |            Detail          |
|----------------------|----------------------------|
| **Validation Point** | Ingestion Pipeline Gateway |
| **Enforcement Tool** | Pydantic (`BaseModel`)     |
| **Error Handling**   | If a source change results in missing mandatory fields (e.g., an empty title) or structural parsing errors, the system triggers a `ValidationError`. The raw record is explicitly blocked from entering the production database and routed to a **Dead Letter Queue (DLQ)** for immediate logging and review. |

### 1.2 Dynamic Mapping Matrix Configuration

The platform relies on a centralized configuration dictionary to map raw payload variations into the uniform database schema fields:

```python
MAPPINGS = {
    "tendersontime": {
        "external_id": "TOT Reference",
        "title": "Titre",
        "country": "Pays",
        "posting_date": "Posting Date",
        "deadline": "Deadline",
        "url": "Lien de l'offre",
        "description": None
    },
    "beta_mr": {
        "external_id": "tender_id",
        "title": "title",
        "country": "location",
        "posting_date": "posting_date",
        "deadline": "deadline",
        "url": "url_link",
        "description": "description"
    }
}
```

### 1.3 The Canonical Pydantic Contract

```python
# Location: src/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CanonicalOpportunity(BaseModel):
    unique_key: str = Field(..., description="Deterministic MD5 hash of title + source to block duplicates")
    source: str = Field(..., description="Name of the crawler/platform source")
    title: str = Field(..., description="Cleaned, validated title of the opportunity")
    country: Optional[str] = None
    posting_date: Optional[str] = None
    deadline: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None

    @field_validator('unique_key', 'source', 'title')
    @classmethod
    def mandatory_fields_cannot_be_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("Field cannot be empty or blank whitespace")
        return str(v).strip()
```

---

## 2. Deduplication & Idempotency Controls

To maintain a predictable budget and stop the system from executing redundant LLM token qualifications on previously seen documents, automated duplicate detection runs immediately during the ingestion process.

### 2.1 Cryptographic Hash Generation

Because external URLs can change arbitrarily due to URL tracking parameters or session keys, duplicate opportunities are identified by their core data content rather than by URL.

- **Algorithm:** MD5 (Message Digest 5)
- **Deterministic Salt Formula:** `lowercase(strip(title)) + "_" + lowercase(strip(source))`

### 2.2 Database-Level Integrity (Idempotency)

The production database uses an explicit database constraint to protect against data corruption, race conditions, and worker retry duplicates.

**Enforced Database Schema:**

```sql
CREATE TABLE public.opportunity (
    id uuid NOT NULL DEFAULT gen_random_uuid (),
    unique_key text NOT NULL,
    source text NOT NULL,
    title text NULL,
    country text NULL,
    posting_date text NULL,
    deadline text NULL,
    url text NULL,
    description text NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    external_id text NULL,
    embedding public.vector NULL,
    CONSTRAINT opportunity_pkey PRIMARY KEY (id),
    CONSTRAINT opportunity_unique_key_unique UNIQUE (unique_key)
) TABLESPACE pg_default;
```

**Pipeline Pattern:** Ingestion scripts write to the table using an `UPSERT` pattern specifying `on_conflict="unique_key"`.

**Idempotency Guarantee:** If a scraping task crashes or runs concurrently, the database constraint `opportunity_unique_key_unique` catches the identical `unique_key`, skipping or updating the row without throwing fatal failures or introducing duplicate rows.

---

## 3. Monitoring & Dead Letter Queue (DLQ) Procedures

Any exception raised during data validation is safely isolated to ensure complete pipeline reliability. A failure in one source string or a change in a vendor schema will never result in an end-to-end pipeline blockage.

### 3.1 Error Lifecycle Flow

1. **Extraction Failure / Schema Shift** — A raw field maps incorrectly, or a critical field like `title` is missing.
2. **Contract Rejection** — Pydantic blocks the instance and raises a validation error.
3. **DLQ Route** — The application catches the exception, logs the event under `DATA_GOVERNANCE_FILTERED`, isolates the bad item payload, and allows the remaining batch records to process smoothly.