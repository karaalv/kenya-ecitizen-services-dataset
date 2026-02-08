# Kenya eCitizen Services Dataset - Schema

## Overview

This document defines the structural schema for the Kenya eCitizen Services Dataset.
It specifies the dataset entities, their fields, and the relationships between them.

This schema is intended as a structural reference only. Detailed field semantics,
data types, constraints, and examples are documented in
[data_dictionary.md](data_dictionary.md). Dataset context, sources, collection
methodology, and limitations are documented in
[metadata.md](metadata.md).

### Dataset Structure and Identifiers

The dataset is organised into five entities: **services**, **agencies**,
**departments**, **ministries**, and **faqs**.

All entities use stable synthetic identifiers (`*_id`) to preserve relationships.
These identifiers are:

- derived from **normalised entity names**,
- generated using **deterministic hashing**,
- not official government identifiers,
- scoped only to this dataset.

If the structure or naming on the eCitizen platform changes, identifiers may need
to be regenerated and relationships re-established.

URLs stored in the dataset are absolute URLs pointing to public eCitizen pages.
These URLs are not guaranteed to be stable over time and may change if the
platform structure changes.

All fields defined in this schema are expected to be present for each record.
Field values may be `null` or empty where information is not publicly available
or could not be extracted at the time of scraping.

Aggregate count fields (`reported_*_count`, `observed_*_count`) represent values
reported by the platform or derived from the dataset at the time of collection
and may differ due to platform inconsistencies or subsequent updates.

## Entities and Fields

### 1. FAQ Entity (`faqs`)

| Field Name | Type   | Description                                                     |
|------------|--------|-----------------------------------------------------------------|
| faq_id     | String | Stable identifier derived from a hash of the question and answer|
| question   | String | FAQ question text as listed on the eCitizen platform            |
| answer     | String | Corresponding FAQ answer text                                   |

---

### 2. Agency Entity (`agencies`)

| Field Name           | Type   | Description                                                     |
|----------------------|--------|-----------------------------------------------------------------|
| agency_id            | String | Identifier derived from normalised agency name (hashed)         |
| ministry_id          | String | Identifier of parent ministry (hashed from normalised name)     |
| department_id        | String | Identifier of parent department (hashed from normalised name)   |
| agency_name          | String | Agency name as listed on the eCitizen platform                  |
| agency_description   | String | Public agency description                                       |
| logo_url             | String | URL of agency logo image                                        |
| agency_url           | String | URL of agency page on the eCitizen platform                     |

---

### 3. Department Entity (`departments`)

| Field Name               | Type    | Description                                                     |
|--------------------------|---------|-----------------------------------------------------------------|
| department_id            | String  | Identifier derived from normalised department name (hashed)     |
| ministry_id              | String  | Identifier of parent ministry (hashed from normalised name)     |
| department_name          | String  | Department name as listed on the eCitizen platform              |
| observed_agency_count    | Integer | Number of agencies observed under the department                |
| observed_service_count   | Integer | Number of services observed under the department                |

---

### 4. Ministry Entity (`ministries`)

| Field Name               | Type    | Description                                                     |
|--------------------------|---------|-----------------------------------------------------------------|
| ministry_id              | String  | Identifier derived from normalised ministry name (hashed)       |
| ministry_name            | String  | Ministry name as listed on the eCitizen platform                |
| ministry_description     | String  | Public ministry description                                     |
| reported_agency_count    | Integer | Agency count reported by the eCitizen platform                  |
| observed_agency_count    | Integer | Agency count observed in the dataset                            |
| reported_service_count   | Integer | Service count reported by the eCitizen platform                 |
| observed_service_count   | Integer | Service count observed in the dataset                           |
| ministry_url             | String  | URL of ministry page on the eCitizen platform                   |

---

### 5. Service Entity (`services`)

| Field Name            | Type    | Description                                                     |
|-----------------------|---------|-----------------------------------------------------------------|
| service_id            | String  | Identifier derived from normalised service name (hashed)        |
| agency_id             | String  | Identifier of responsible agency (hashed from normalised name)  |
| department_id         | String  | Identifier of parent department (hashed from normalised name)   |
| ministry_id           | String  | Identifier of parent ministry (hashed from normalised name)     |
| service_name          | String  | Service name as listed on the eCitizen platform                 |
| service_url           | String  | URL of the service page on the eCitizen platform                |
| service_description   | String  | Reserved for future use, currently null                         |
| requirements          | String  | Reserved for future use, currently null                         |

## Notes

This dataset represents a point-in-time snapshot of the eCitizen platform.
Platform structure, content, and counts may change over time and may not be
reflected in this dataset.

The dataset is intended for research, analysis, and tooling purposes.
It should not be treated as an authoritative or legally binding source.
For interpretive guidance, limitations, and ethical considerations, refer to
[metadata.md](metadata.md).
