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

When multiple input values are used, they are concatenated using the
hyphen character (`-`) as a delimiter prior to hashing.

This ensures that:

- identical inputs always produce the same identifier,
- hierarchical context is preserved in identifiers,
- relationships between entities remain stable within a dataset version.

Identifiers:

- are not official government identifiers,
- are scoped only to this dataset,
- may change if upstream names or platform structure change.

### String Type Distinctions

Two categories of string fields are used throughout the dataset:

1. **Identifier strings**
   - Used for fields such as `*_id` and `agency_name_hash`
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
- **Description**: Stable identifier derived from a hash of `question-answer`.
- **Example**: `a3f9c27b91de`
- **Notes**:
  - Used to uniquely identify FAQ entries within the dataset.
  - Changes to either the question or answer text will result in a new identifier.

### 1.2 `question`

- **Type**: String (UTF-8 encoded text)
- **Description**: The FAQ question text as presented on the eCitizen platform.
- **Example**: Can my visa be extended if it expires while I am in Kenya?

### 1.3 `answer`

- **Type**: String (UTF-8 encoded text)
- **Description**: The answer corresponding to the FAQ question.
- **Example**: Yes, the visitors pass can be extended on fns.immigration.go.ke.

## 2. Ministry Entity (`ministries`)

### 2.1 `ministry_id`

- **Type**: String (identifier)
- **Description**: Stable identifier derived from the normalised ministry name.
- **Example**: `4b8e2d91ac7f`

### 2.2 `ministry_name`

- **Type**: String (UTF-8 encoded text)
- **Description**: Ministry name as listed on the eCitizen platform.
- **Example**: Ministry of Agriculture and Livestock Development

### 2.3 `ministry_description`

- **Type**: String (UTF-8 encoded text)
- **Description**: Public description of the ministry’s mandate.
- **Example**: Responsible for formulation and implementation of agricultural policy.

### 2.4 `reported_agency_count`

- **Type**: Integer
- **Example**: 10

### 2.5 `observed_agency_count`

- **Type**: Integer
- **Example**: 8

### 2.6 `reported_service_count`

- **Type**: Integer
- **Example**: 50

### 2.7 `observed_service_count`

- **Type**: Integer
- **Example**: 45

### 2.8 `observed_department_count`

- **Type**: Integer
- **Example**: 3

### 2.9 `ministry_url`

- **Type**: String (UTF-8 encoded URL)
- **Example**: <https://www.ecitizen.go.ke/en/ministries/agriculture>

## 3. Department Entity (`departments`)

### 3.1 `department_id`

- **Type**: String (identifier)
- **Description**: Stable identifier derived from `ministry_id-department_name`.
- **Example**: `c91d72e4ab05`

### 3.2 `ministry_id`

- **Type**: String (identifier)
- **Reference**: [`ministries.ministry_id`](#21-ministry_id)

### 3.3 `department_name`

- **Type**: String (UTF-8 encoded text)
- **Example**: Department of Agriculture

### 3.4 `observed_agency_count`

- **Type**: Integer
- **Example**: 5

### 3.5 `observed_service_count`

- **Type**: Integer
- **Example**: 20

### 3.6 `ministry_departments_url`

- **Type**: String (UTF-8 encoded URL)
- **Example**: <https://www.ecitizen.go.ke/en/ministries/agriculture?department=agriculture>

## 4. Agency Entity (`agencies`)

### 4.1 `agency_id`

- **Type**: String (identifier)
- **Description**: Stable identifier derived from
  `ministry_id-department_id-agency_name`.
- **Example**: `9d3b61a7e4f2`

### 4.2 `agency_name_hash`

- **Type**: String (identifier)
- **Description**: Identifier derived from the normalised agency name only.
- **Example**: `f27a91c3d6b4`
- **Notes**:
  - Used to join agency metadata from global listings with ministry placements.

### 4.3 `ministry_id`

- **Type**: String (identifier)
- **Reference**: [`ministries.ministry_id`](#21-ministry_id)

### 4.4 `department_id`

- **Type**: String (identifier)
- **Reference**: [`departments.department_id`](#31-department_id)

### 4.5 `agency_name`

- **Type**: String (UTF-8 encoded text)
- **Example**: Agricultural Development Corporation

### 4.6 `agency_description`

- **Type**: String (UTF-8 encoded text)
- **Example**: Promote the production of Kenya’s essential agricultural inputs

### 4.7 `logo_url`

- **Type**: String (UTF-8 encoded URL)
- **Example**: <https://demoadmin.ecitizen.pesaflow.com/assets/uploads/adc.png>

### 4.8 `agency_url`

- **Type**: String (UTF-8 encoded URL)
- **Example**: <https://adc.go.ke>

### 4.9 `observed_service_count`

- **Type**: Integer
- **Example**: 20

### 4.10 `ministry_departments_agencies_url`

- **Type**: String (UTF-8 encoded URL)
- **Example**: <https://www.ecitizen.go.ke/en/ministries/agriculture?department=agriculture&agency=adc>

## 5. Service Entity (`services`)

### 5.1 `service_id`

- **Type**: String (identifier)
- **Description**: Stable identifier derived from
  `ministry_id-department_id-agency_id-service_name`.
- **Example**: `6a91e4d27bc8`

### 5.2 `agency_id`

- **Type**: String (identifier)
- **Reference**: [`agencies.agency_id`](#41-agency_id)

### 5.3 `department_id`

- **Type**: String (identifier)
- **Reference**: [`departments.department_id`](#31-department_id)

### 5.4 `ministry_id`

- **Type**: String (identifier)
- **Reference**: [`ministries.ministry_id`](#21-ministry_id)

### 5.5 `service_name`

- **Type**: String (UTF-8 encoded text)
- **Example**: Apply for Agricultural Input Subsidy Program

### 5.6 `service_url`

- **Type**: String (UTF-8 encoded URL)
- **Example**: <https://www.ecitizen.go.ke/services/agricultural-input-subsidy>

### 5.7 `service_description`

- **Type**: String (UTF-8 encoded text)
- **Notes**:
  - Reserved for future use.
  - Null for all records in the current dataset version.

### 5.8 `requirements`

- **Type**: String (UTF-8 encoded text)
- **Notes**:
  - Reserved for future use.
  - Null for all records in the current dataset version.
