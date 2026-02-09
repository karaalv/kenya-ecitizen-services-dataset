# Kenyan eCitizen Services Dataset – Methodology

## 1. Overview

This document describes the methodology used to collect, process, and validate the
Kenya eCitizen Services Dataset. It covers the technical approach used to scrape
the eCitizen platform, manage scraping behaviour, and process raw data into the
final dataset format defined in [schema.md](schema.md) and
[data_dictionary.md](data_dictionary.md).

This document focuses on methodological and technical implementation decisions for
major steps in the pipeline. Dataset context, sources, and limitations are documented
in [metadata.md](metadata.md). Field-level semantics, constraints, and examples are
documented in [data_dictionary.md](data_dictionary.md).

Implementation details are available in the [scraper/](../scraper/) directory.
Python 3.12 was used for all scraping and processing code. Notable libraries included
`playwright` (browser automation), `BeautifulSoup` (HTML parsing), `pandas` (data
manipulation), and `pydantic` (validation). Exact dependency versions were captured
in `requirements.txt`.

The final dataset outputs were written to [data/processed/](../data/processed/), with
one subfolder per entity (e.g. `data/processed/faqs/`, `data/processed/ministries/`)
and both CSV and JSON representations per entity. The CSV and JSON files contained
the same underlying records.

The dataset represented a snapshot of the eCitizen platform at the time of scraping
(February 2026). No guarantees of ongoing updates were made.

Observations from the exploration notebooks in [notebooks/](../notebooks/) informed
this methodology. The notebooks contained detailed investigative work, while this
document summarised the final approach and design decisions.

## 2. High Level Approach

### 2.1 General Considerations

The eCitizen platform presented a multi-level hierarchy (ministries, departments,
agencies, services) with inconsistencies across sections. A systematic approach was
required to collect data comprehensively and map relationships reliably.

A hybrid scraping strategy was used:

- `playwright` handled navigation and dynamic content rendering.
- `BeautifulSoup` extracted and structured data from saved HTML.

Processing focused on:

- transforming raw HTML into structured entity records,
- generating stable synthetic identifiers via deterministic hashing,
- validating outputs and relationships against the defined schema.

### 2.2 Processing Phases

Scraping and processing were executed as a pipeline. Network navigation and page
requests were executed sequentially. Once HTML files had been saved locally, parsing
and post-processing steps over those saved artefacts were executed in parallel where
possible.

The pipeline was split into three phases:

1. **FAQ scraping and processing**
   - Scraped FAQ content and produced the `faqs` entity.

2. **Initial agency scraping and processing**
   - Scraped the global agency listing to collect agency metadata
     (description, logo URL, agency URL) and produced an initial agency dataset
     keyed by `agency_name_hash`.

3. **Ministries, departments, agencies, and services scraping and processing**
   - Scraped ministry pages, derived departments and agency placements from ministry
     navigation elements, backfilled relationships, and scraped service listings
     scoped by ministry and agency context.

The precise steps in each phase are described in sections 3 to 5.

### 2.3 IP Limits and Scraping Behaviour

The platform did not expose a public API and required browser automation. No public
rate limits were documented at the time of scraping. A cautious approach was used to
avoid undue load and reduce the likelihood of triggering anti-scraping controls.

The following behaviour was implemented:

- **Sequential requests only**
  All page navigations and network requests were executed sequentially. Parallelism
  was used only for processing work performed on already-saved HTML.

- **Human-like pacing**
  A random base delay between **2–6 seconds** was applied between page requests, with
  an additional random jitter between **0–4 seconds**.

- **Backoff on anomalies**
  When signs of throttling or blocking were observed (e.g. repeated timeouts, 429s,
  empty dynamic content, suspected bot checks), the scraper paused for **3 minutes**
  and resumed with increased pacing (base delay **10–20 seconds**) for the next
  **10 requests**. If anomalies continued, exponential backoff was applied to pauses.
  After **5 consecutive blocks**, scraping aborted and the failure was logged for
  manual review.

- **Local persistence of HTML**
  Scraped HTML was saved locally to avoid repeated requests and to allow processing
  to be re-run without re-scraping.

- **Non-adversarial client behaviour**
  A single consistent browser context was used with no user-agent rotation and no
  fingerprint obfuscation. No attempt was made to bypass bot detection, access
  controls, or authentication.

- **Session continuity**
  Browser sessions and cookies were preserved across requests to reflect natural
  navigation.

Non-goals included:

- no proxy pools or IP rotation,
- no CAPTCHA bypassing,
- no access to restricted content.

### 2.4 Processing Runtime and Idempotency

Processing was designed to be idempotent. Failures in downstream parsing or
validation did not require re-scraping.

This was achieved by:

- saving raw HTML under `data/raw/` per entity and traversal stage,
- saving intermediate outputs and state checkpoints for entity processors,
- writing temporary state to `data/tmp/` (excluded from version control),
- logging failures under `data/tmp/logs/` with affected inputs and error context.

To avoid stalling on transient failures, pages were retried up to **3 times** with a
**30 second** timeout per attempt and exponential backoff between attempts before
being marked as failed.

Progress and processing status were tracked using terminal logs and `tqdm` progress
bars.

### 2.5 Identifier Generation and Hashing

Stable synthetic identifiers were generated using deterministic hashing.

#### 2.5.1 Normalisation

Input text was normalised prior to hashing using the following steps:

1. Converted to lowercase
2. Unicode normalisation (NFKD)
3. Stripped accents and diacritics
4. Removed all non `[a-z0-9]` characters
5. Collapsed to a single string

#### 2.5.2 Hashing

Normalised inputs were hashed using SHA-256 (`hashlib.sha256`). The hexadecimal
digest was truncated to the first **12** characters.

When multiple inputs were used, they were concatenated using `-` as a delimiter
before hashing.

#### 2.5.3 Identifier Schemes

Identifiers were generated as follows:

- `faq_id` = hash(`question`-`answer`)
- `ministry_id` = hash(`ministry_name`)
- `department_id` = hash(`ministry_id`-`department_name`)
- `agency_name_hash` = hash(`agency_name`)
- `agency_id` = hash(`ministry_id`-`department_id`-`agency_name`)
- `service_id` = hash(`ministry_id`-`department_id`-`agency_id`-`service_name`)

This design reduced ambiguity from duplicate names by scoping identifiers to the
hierarchical context in which entities appeared.

## 3. Phase 1: FAQ Scraping and Processing

### 3.1 Scraping the FAQ Section

The FAQ section was accessible at:
<https://accounts.ecitizen.go.ke/en/help-and-support>

The scraper waited until the FAQ list had loaded by checking that the `ul` element
inside the `div#faqs` contained one or more `li` children. This was performed using
`playwright` waiting utilities.

Once loaded, the `div#faqs` HTML fragment was extracted and saved under
`data/raw/faqs/`.

### 3.2 Processing the FAQ Data

Saved HTML was parsed using `BeautifulSoup`. Each FAQ entry appeared as an `li` with
an id of the form `faq_<number>`. The question was extracted from a `button`, and the
answer from the neighbouring `div`.

The dataset then computed:

- `faq_id` from `question-answer` (deterministic hash)

Processed outputs were validated and written to `data/processed/faqs/` in CSV and JSON.

## 4. Phase 2: Initial Agency Scraping and Processing

### 4.1 Scraping the Agency Listings

The global agency listing was accessed at:
<https://www.ecitizen.go.ke/en/agencies>

The scraper navigated to the page and waited for agency cards to load by checking
for anchor elements within the agency grid.

The grid HTML fragment was extracted and saved under `data/raw/agencies/`.

### 4.2 Processing the Agency Data

Saved agency listing HTML was parsed. For each agency card:

- `agency_name` was extracted from the `h4` tag
- `agency_description` was extracted from the neighbouring `p` tag
- `logo_url` was extracted from the nested `img[src]`
- `agency_url` was extracted from the anchor `href`

An initial agency record set was produced with:

- `agency_name_hash` = hash(`agency_name`)
- ministry and department placement fields left as null at this stage

These records were stored in processing state to support later backfilling during
phase 3. Parsing and validation over the saved HTML were parallelised.

## 5. Phase 3: Ministries, Departments, Agencies, and Services

### 5.1 Obtaining Ministry Source URLs

Ministry URLs were not fully consistent across the platform. In particular, some
ministries did not follow the expected URL pattern.

To obtain authoritative ministry URLs, the ministries listing page was scraped:
<https://accounts.ecitizen.go.ke/en/home/national-ministries>

The scraper waited for relevant ministry anchor elements to load, extracted ministry
names and URLs, and saved the HTML under `data/raw/ministries/`.

Initial ministry state was created with:

- `ministry_id` = hash(`ministry_name`)
- counts left null until ministry pages were parsed

### 5.2 Scraping Ministry Pages

Ministry pages were then visited sequentially using the collected ministry URLs.

For each ministry page, the scraper waited for the "Overview" section to load and
saved relevant HTML fragments under `data/raw/ministries/<ministry_id>/`.

#### 5.2.1 Scraping Ministry Overview

From the saved overview fragment, the pipeline extracted:

- `ministry_description`
- `reported_agency_count`
- `reported_service_count`

Parsing and validation over saved fragments were parallelised.

#### 5.2.2 Scraping Departments and Agency Placements

Departments and agencies were discoverable from a listbox-style navigation section.
This section was saved as `departments_and_agencies.html`.

Each agency placement entry provided an agency label and a URL containing query
parameters for department and agency. From these:

- `department_name` was parsed from the URL
- `department_id` was computed as hash(`ministry_id`-`department_name`)
- `ministry_departments_url` was derived by removing the agency query component

Agency placements were then derived:

- `agency_id` was computed as hash(`ministry_id`-`department_id`-`agency_name`)
- `agency_name_hash` was computed as hash(`agency_name`)
- agency metadata from phase 2 was joined using `agency_name_hash` where available
- `ministry_departments_agencies_url` was retained for traceability and navigation

#### 5.2.3 Scraping Services per Agency Placement

Service listings loaded based on department and agency query parameters. For each
agency placement URL, the scraper navigated sequentially to load the service list,
waited for the service container to render, and saved the service listing HTML under:

`data/raw/ministries/<ministry_id>/<department_id>/<agency_id>/services.html`

Each service entry was extracted from anchors in the listing:

- `service_name` from anchor text
- `service_url` from anchor `href`
- `service_id` computed as
  hash(`ministry_id`-`department_id`-`agency_id`-`service_name`)

`service_description` and `requirements` were reserved for future dataset versions
and were null for this dataset snapshot.

Some services linked to external websites rather than remaining within eCitizen. No
distinction was made in the dataset, the `service_url` preserved the observed link.

## 5.3 Finalising the Dataset

After scraping and parsing completed, entity tables were materialised into dataframes.
Computation over processed records (counts, joins, relationship checks) was performed
in parallel.

Derived fields were computed, including:

- `observed_agency_count`, `observed_service_count`, `observed_department_count`

Final validation checks included:

- required columns present per entity,
- referential integrity across identifiers (e.g. all service `agency_id` values
  existed in the agencies entity),
- basic URL formatting checks.

Outputs were written to `data/processed/` in CSV and JSON per entity.

## 6. Edge Cases and Data Quality Considerations

### 6.1 Inconsistent Agencies Across Pages

Some agencies discovered within ministry pages did not appear in the global agency
listing. In those cases, placement records were still created during phase 3, but
metadata fields that depended on the global listing (e.g. `agency_description`,
`logo_url`, `agency_url`) remained null.

### 6.2 Base URL Mapping

Requests to `https://www.ecitizen.go.ke/` redirected to `https://accounts.ecitizen.go.ke/`
during navigation. For consistency in the dataset, generated and stored platform URLs
using the `https://www.ecitizen.go.ke` base where applicable, even when scraping was
performed through redirected hosts.

### 6.3 Duplicate Agency, Department, and Service Names

Duplicate names across ministries, departments, agencies, and services were treated
as expected platform behaviour. To avoid identifier collisions and ambiguous joins:

- department identifiers were scoped by ministry (`ministry_id-department_name`)
- agency identifiers were scoped by ministry and department
  (`ministry_id-department_id-agency_name`)
- service identifiers were scoped by ministry, department, and agency
  (`ministry_id-department_id-agency_id-service_name`)
- agency metadata joins were performed using `agency_name_hash` (name-only hash),
  separate from the placement-scoped `agency_id`

This approach reduced ambiguity while preserving traceability of where entities
appeared in the platform hierarchy.

## 7. Conclusion

This methodology describes how the Kenya eCitizen Services Dataset was created by
scraping publicly accessible platform content, saving raw HTML for reproducibility,
and transforming it into structured entities with stable synthetic identifiers.

The final dataset represented ministries, departments, agencies, services, and FAQs
as observed in February 2026. Users are expected to account for platform change over
time and the edge cases described in section 6. For dataset context and limitations,
refer to [metadata.md](metadata.md).
