# Kenya eCitizen Services Dataset – Schema

## Overview

This document defines the structural schema for the Kenya eCitizen Services Dataset.
It specifies the dataset entities, their fields, and the relationships between them.

This schema is intended as a structural reference only. Detailed field semantics,
data types, constraints, and examples are documented in
[data_dictionary.md](data_dictionary.md). Dataset context, sources, collection
methodology, and limitations are documented in
[metadata.md](metadata.md).

## Dataset Structure and Identifiers

The dataset is organised into five entities: **faqs**, **ministries**,
**departments**, **agencies**, and **services**.

All entities use stable synthetic identifiers (`*_id`) to preserve relationships.
Identifiers are generated using **deterministic hashing** over **normalised input
strings**, with multiple inputs concatenated using the hyphen character (`-`) as a
delimiter before hashing.

Identifiers are:

- deterministic and reproducible,
- not official government identifiers,
- scoped to this dataset only.

If upstream naming or platform structure changes, identifiers may need to be
regenerated and relationships re-established.

URLs stored in the dataset are absolute URLs pointing to public eCitizen pages.
These URLs are not guaranteed to be stable over time and may change if the
platform structure changes.

All fields defined in this schema are expected to be present for each record.
Field values may be `null` where information is not publicly available or could
not be extracted at the time of scraping.

Aggregate count fields (`reported_*_count`, `observed_*_count`) represent values
reported by the platform or derived from the dataset at the time of collection
and may differ due to platform inconsistencies or subsequent updates.

## Entities and Fields

### 1. FAQ Entity (`faqs`)

| Field Name | Type   | Description                                                     |
|------------|--------|-----------------------------------------------------------------|
| faq_id     | String | Identifier derived from hash of `question-answer`               |
| question   | String | FAQ question text as listed on the eCitizen platform            |
| answer     | String | Corresponding FAQ answer text                                   |

---

### 2. Ministry Entity (`ministries`)

| Field Name                | Type    | Description                                                                  |
|---------------------------|---------|------------------------------------------------------------------------------|
| ministry_id               | String  | Identifier derived from normalised ministry name                             |
| ministry_name             | String  | Ministry name as listed on the eCitizen platform                             |
| ministry_description      | String  | Public ministry description                                                  |
| reported_agency_count     | Integer | Agency count reported by the eCitizen platform                               |
| observed_agency_count     | Integer | Agency count observed in the dataset                                         |
| reported_service_count    | Integer | Service count reported by the eCitizen platform                              |
| observed_service_count    | Integer | Service count observed in the dataset                                        |
| observed_department_count | Integer | Department count observed in the dataset                                     |
| ministry_url              | String  | URL of ministry page on the eCitizen platform                                |

---

### 3. Department Entity (`departments`)

| Field Name               | Type    | Description                                                                 |
|--------------------------|---------|-----------------------------------------------------------------------------|
| department_id            | String  | Identifier derived from `ministry_id-department_name`                       |
| ministry_id              | String  | Identifier of parent ministry                                               |
| department_name          | String  | Department name as listed on the eCitizen platform                          |
| observed_agency_count    | Integer | Number of agencies observed under the department                            |
| observed_service_count   | Integer | Number of services observed under the department                            |
| ministry_departments_url | String  | Ministry page URL scoped to the department via query parameters             |

---

### 4. Agency Entity (`agencies`)

| Field Name                             | Type   | Description                                                                 |
|----------------------------------------|--------|-----------------------------------------------------------------------------|
| agency_id                              | String | Identifier derived from `ministry_id-department_id-agency_name`             |
| agency_name_hash                       | String | Identifier derived from normalised agency name only                         |
| ministry_id                            | String | Identifier of parent ministry                                               |
| department_id                          | String | Identifier of parent department                                             |
| agency_name                            | String | Agency name as listed on the eCitizen platform                              |
| agency_description                     | String | Public agency description                                                   |
| logo_url                               | String | URL of agency logo image                                                    |
| agency_url                             | String | URL of agency page from the eCitizen platform                               |
| ministry_departments_agencies_url      | String | Ministry page URL scoped to department and agency via query parameters      |

**Note**:
`agency_name_hash` is used to join agency metadata collected from the global
agency listing with agency placements discovered under specific ministries
and departments.

---

### 5. Service Entity (`services`)

| Field Name            | Type    | Description                                                                  |
|-----------------------|---------|------------------------------------------------------------------------------|
| service_id            | String  | Identifier derived from `ministry_id-department_id-agency_id-service_name`   |
| agency_id             | String  | Identifier of responsible agency                                             |
| department_id         | String  | Identifier of parent department                                              |
| ministry_id           | String  | Identifier of parent ministry                                                |
| service_name          | String  | Service name as listed on the eCitizen platform                              |
| service_url           | String  | URL of the service page on the eCitizen platform                             |
| service_description   | String  | Reserved for future use, currently null                                      |
| requirements          | String  | Reserved for future use, currently null                                      |

---

## Notes

This dataset represents a point-in-time snapshot of the eCitizen platform.
Platform structure, content, and counts may change over time and may not be
reflected in this dataset.

The dataset is intended for research, analysis, and tooling purposes.
It should not be treated as an authoritative or legally binding source.
For interpretive guidance, limitations, and ethical considerations, refer to
[metadata.md](metadata.md).
