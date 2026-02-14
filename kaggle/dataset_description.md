# Kenya eCitizen Services Dataset (February 2026 Snapshot)

## Overview

The Kenya eCitizen platform serves as the primary digital portal for accessing
government services in Kenya. This dataset provides a structured, point-in-time
snapshot of ministries, departments, agencies, services, and frequently asked
questions publicly listed on the platform as observed on 14 February 2026.

The dataset is intended to support research and analysis in areas including:

- Digital government service delivery
- Public sector platform design
- Service discoverability and navigation
- Civic technology
- AI-assisted public service systems
- Public administration and policy analysis

This dataset represents only publicly accessible, unauthenticated content.

## Dataset Contents

The dataset contains five structured entities:

- **services** (5,489 records)
- **agencies** (286 records)
- **ministries** (27 records)
- **departments** (54 records)
- **faqs** (15 records)

All entities are provided in CSV format.

### Services

Each service record includes:

- `service_id` (deterministic synthetic identifier)
- `service_name`
- `service_url`
- `ministry_id`
- `department_id`
- `agency_id`

Service identifiers are derived from hierarchical context to ensure stability
within the dataset version.

### Agencies

Agency records include:

- Agency name
- Public description
- Logo URL (where available)
- Parent ministry and department identifiers
- Observed service counts

### Ministries

Ministry records include:

- Ministry name
- Public description (where available)
- Platform-reported agency and service counts
- Observed counts derived from structured scraping

### FAQs

Frequently asked questions and answers as presented in the public help section.

## Coverage Interpretation

At the time of scraping, the eCitizen platform publicly displayed a statement
indicating that it hosts over 22,000 government services.

This dataset captures 5,489 services that are directly discoverable through
the publicly navigable ministry → department → agency hierarchy.

The discrepancy between the reported total and the observed count likely reflects:

- Differences in counting methodology
- Inclusion of transactional or form-level variations
- Context-dependent or dynamically generated services
- Authenticated-only listings
- Internal aggregation logic not exposed through public navigation

This dataset intentionally enumerates only services that are publicly visible
and programmatically discoverable through structured navigation.

## Data Collection Methodology

Data was collected using automated browser navigation (Playwright),
with HTML parsing performed using BeautifulSoup and structured validation
using Pydantic.

Scraping behaviour was designed to be non-adversarial:

- Sequential navigation only
- Human-like pacing delays
- No authentication bypass
- No circumvention of access controls
- No scraping of user data

Raw HTML was stored locally for reproducibility before transformation into
structured entity tables.

Deterministic hashing was used to generate synthetic identifiers, ensuring
referential integrity across entities.

## Data Quality and Validation

The dataset demonstrates strong structural integrity:

- No duplicate identifiers across any entity
- No orphaned relational records
- Minimal missing values
- Full referential consistency between services, agencies, departments, and ministries

Missing values correspond only to content absent on the platform at the time
of scraping.

Observed service and agency counts align closely with platform-reported counts,
with only minor discrepancies in isolated cases.

## Limitations

- The dataset represents a snapshot and is not continuously updated.
- It does not include authenticated-only services.
- It does not include service workflow steps, eligibility criteria,
  or operational processing details.
- Platform structure and counts may change over time.
- Identifiers are synthetic and not official government identifiers.

---

## Source Code and Reproducibility

The full scraping pipeline, documentation, and processing methodology are
available in the public repository:

<https://github.com/karaalv/kenya-ecitizen-services-dataset>

The repository includes:

- Detailed methodology documentation
- Schema and data dictionary specifications
- Deterministic identifier generation logic
- Data validation procedures
- Structured raw and processed data workflows

The codebase is provided to support transparency, reproducibility,
and methodological clarity.

## Intended Use

This dataset is suitable for:

- Academic research
- Civic technology development
- Public sector digital transformation analysis
- Data journalism
- AI and information retrieval systems

It should not be treated as an official or legally authoritative source.
For official information, refer to the eCitizen platform directly.
