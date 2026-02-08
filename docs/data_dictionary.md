# Kenya eCitizen Services Dataset – Data Dictionary

## Overview

This document defines the semantics, meaning, and intended usage of all fields
contained in the Kenya eCitizen Services Dataset.

It should be read alongside:

- [schema.md](schema.md) for structural relationships and entity layout
- [metadata.md](metadata.md) for dataset context, sources, methodology, and limitations

This data dictionary focuses on **what each field represents**, not how the
dataset is stored or processed.

## Identifier Generation and String Types

### Deterministic Identifier Generation

All identifier fields (`*_id`) in this dataset are generated using a
**deterministic hashing process** applied to one or more **normalised string
values**.

This ensures that:

- identical inputs always produce the same identifier,
- relationships between entities remain stable within a dataset version,
- identifiers can be regenerated if the dataset is rebuilt.

These identifiers:

- are not official government identifiers,
- are scoped only to this dataset,
- may change if upstream names or structures on the eCitizen platform change.

### String Type Distinctions

Two categories of string fields are used throughout the dataset:

1. **Identifier strings**
   - Used for fields such as `*_id`
   - ASCII-only
   - Contain no whitespace or special characters
   - Intended for internal reference and joins

2. **Text and URL strings**
   - UTF-8 encoded
   - Used for names, descriptions, questions, answers, and URLs
   - May contain whitespace, punctuation, or special characters

## 1. FAQ Entity (`faqs`)

### 1.1 `faq_id`

- **Type**: String (identifier)
- **Description**: Stable identifier derived from a hash of the question and answer text.
- **Example**: <!-- TODO -->
- **Notes**:
  - Used to uniquely identify FAQ entries within the dataset.
  - Changes to either the question or answer text will result in a new identifier.

### 1.2 `question`

- **Type**: String (UTF-8 encoded text)
- **Description**: The FAQ question text as presented on the eCitizen platform.
- **Example**: Can my visa be extended if it expires while I am in Kenya?
- **Notes**:
  - Used together with `answer` to generate `faq_id`.

### 1.3 `answer`

- **Type**: String (UTF-8 encoded text)
- **Description**: The answer corresponding to the FAQ question.
- **Example**: Yes, the visitors pass can be extended on fns.immigration.go.ke.
- **Notes**:
  - Used together with `question` to generate `faq_id`.

## 2. Agency Entity (`agencies`)

### 2.1 `agency_id`

- **Type**: String (identifier)
- **Description**: Stable identifier derived from the normalised agency name.
- **Example**: <!-- TODO -->
- **Notes**:
  - Used to reference agencies across related entities.

### 2.2 `ministry_id`

- **Type**: String (identifier)
- **Description**: Identifier of the parent ministry.
- **Reference**: [`ministries.ministry_id`](#41-ministry_id)

### 2.3 `department_id`

- **Type**: String (identifier)
- **Description**: Identifier of the parent department.
- **Reference**: [`departments.department_id`](#31-department_id)

### 2.4 `agency_name`

- **Type**: String (UTF-8 encoded text)
- **Description**: Official agency name as listed on the eCitizen platform.
- **Example**: Agricultural Development Corporation
- **Notes**:
  - Changes to this value may result in a new `agency_id`.

### 2.5 `agency_description`

- **Type**: String (UTF-8 encoded text)
- **Description**: Public description of the agency’s mandate or function.
- **Example**: Promote the production of Kenya’s essential agricultural inputs
- **Notes**:
  - May be null if no description is provided on the platform.

### 2.6 `logo_url`

- **Type**: String (UTF-8 encoded URL)
- **Description**: Absolute URL of the agency’s logo image.
- **Example**: <https://demoadmin.ecitizen.pesaflow.com/assets/uploads/>...
- **Notes**:
  - URLs are not guaranteed to be stable over time.

### 2.7 `agency_url`

- **Type**: String (UTF-8 encoded URL)
- **Description**: Absolute URL of the agency’s page.
- **Example**: <https://adc.go.ke/shop>
- **Notes**:
  - Stored as provided by the platform without normalisation.

## 3. Department Entity (`departments`)

### 3.1 `department_id`

- **Type**: String (identifier)
- **Description**: Stable identifier derived from the normalised department name.
- **Example**: <!-- TODO -->

### 3.2 `ministry_id`

- **Type**: String (identifier)
- **Description**: Identifier of the parent ministry.
- **Reference**: [`ministries.ministry_id`](#41-ministry_id)

### 3.3 `department_name`

- **Type**: String (UTF-8 encoded text)
- **Description**: Department name as listed on the eCitizen platform.
- **Example**: Department of Agriculture

### 3.4 `observed_agency_count`

- **Type**: Integer
- **Description**: Number of agencies associated with the department in the dataset.
- **Example**: 5
- **Notes**:
  - Derived from observed relationships at the time of scraping.

### 3.5 `observed_service_count`

- **Type**: Integer
- **Description**: Number of services associated with the department in the dataset.
- **Example**: 20

## 4. Ministry Entity (`ministries`)

### 4.1 `ministry_id`

- **Type**: String (identifier)
- **Description**: Stable identifier derived from the normalised ministry name.
- **Example**: <!-- TODO -->

### 4.2 `ministry_name`

- **Type**: String (UTF-8 encoded text)
- **Description**: Ministry name as listed on the eCitizen platform.
- **Example**: Ministry of Agriculture and Livestock Development

### 4.3 `ministry_description`

- **Type**: String (UTF-8 encoded text)
- **Description**: Public description of the ministry’s mandate.
- **Example**: Responsible for formulation and implementation of agricultural policy.

### 4.4 `reported_agency_count`

- **Type**: Integer
- **Description**: Agency count as reported by the eCitizen platform.
- **Example**: 10

### 4.5 `observed_agency_count`

- **Type**: Integer
- **Description**: Agency count observed in the dataset.
- **Example**: 8

### 4.6 `reported_service_count`

- **Type**: Integer
- **Description**: Service count as reported by the eCitizen platform.
- **Example**: 50

### 4.7 `observed_service_count`

- **Type**: Integer
- **Description**: Service count observed in the dataset.
- **Example**: 45

### 4.8 `ministry_url`

- **Type**: String (UTF-8 encoded URL)
- **Description**: URL of the ministry’s page on the eCitizen platform.
- **Example**: <https://www.ecitizen.go.ke/>...

## 5. Service Entity (`services`)

### 5.1 `service_id`

- **Type**: String (identifier)
- **Description**: Stable identifier derived from the normalised service name and
  associated agency.
- **Example**: <!-- TODO -->

### 5.2 `agency_id`

- **Type**: String (identifier)
- **Reference**: [`agencies.agency_id`](#21-agency_id)

### 5.3 `department_id`

- **Type**: String (identifier)
- **Reference**: [`departments.department_id`](#31-department_id)

### 5.4 `ministry_id`

- **Type**: String (identifier)
- **Reference**: [`ministries.ministry_id`](#41-ministry_id)

### 5.5 `service_name`

- **Type**: String (UTF-8 encoded text)
- **Description**: Service name as listed on the eCitizen platform.
- **Example**: Apply for Agricultural Input Subsidy Program

### 5.6 `service_url`

- **Type**: String (UTF-8 encoded URL)
- **Description**: URL of the service’s page on the eCitizen platform.
- **Example**: <https://www.ecitizen.go.ke/>...

### 5.7 `service_description`

- **Type**: String (UTF-8 encoded text)
- **Description**: Description of the service.
- **Notes**:
  - Reserved for future use.
  - Null for all records in the current dataset version.

### 5.8 `requirements`

- **Type**: String (UTF-8 encoded text)
- **Description**: Requirements for accessing or applying for the service.
- **Notes**:
  - Reserved for future use.
  - Null for all records in the current dataset version.
