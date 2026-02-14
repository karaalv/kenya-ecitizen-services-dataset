# Kenya eCitizen Services Dataset

**version**: 1.0.0
**Date**: February 2026

## Overview

- This repository contains a structured dataset of services provided via the Kenya eCitizen platform.
- eCitizen is an online portal that enables Kenyan citizens to access a wide range of government services and represents a major step towards the digitisation of public service delivery in Kenya.
- The dataset includes information on available services, including service names, descriptions, categories, URLs, responsible agencies, and additional relevant metadata.
- In addition to service listings, the dataset includes frequently asked questions (FAQs) associated with eCitizen services to support understanding and usage of the platform.
- Official information about the eCitizen platform is available at the [eCitizen Portal](https://www.ecitizen.go.ke/).
- This dataset was originally curated to support the development of *Mwalika*, an AI assistant designed to help users navigate and utilise the eCitizen platform more effectively, more can be found about Mwalika in the [Mwalika repository](https://github.com/karaalv/mwalika-documentation)
- The dataset has been made publicly available to support research and development in digital government services, AI-assisted public service delivery, and related fields.
- This dataset is intended for research, analysis, and tooling purposes only. It must not be used as legal advice or as a definitive source for regulatory or compliance decisions.
- All information contained in this dataset is derived from publicly accessible content on the eCitizen platform and has been structured to improve accessibility and analysis.

## Disclaimer

- This dataset is an independent, third-party compilation derived from publicly available information on the Kenya eCitizen platform as of February 2026.
- While reasonable efforts have been made to ensure accuracy and completeness, the eCitizen platform may change without notice, and discrepancies may exist.
- This dataset does not replace or supersede the official eCitizen platform. Users must verify critical or time-sensitive information directly via official government channels.
- The creators of this dataset accept no responsibility for inaccuracies, omissions, or consequences arising from its use.
- Where this dataset is used in critical or decision-support contexts, users are responsible for validating all information against official sources.
- The creators of this dataset are not affiliated with the Government of Kenya, the eCitizen platform, or any associated government agency.

## Data Freshness and Coverage

This dataset represents a snapshot of the eCitizen platform.
The scrape was performed on **14 February 2026**. There are no guarantees of ongoing updates, and the dataset should be treated as a point-in-time extraction.

### Platform Coverage

The eCitizen platform publicly reports hosting **over 22,000 government services**.
However, this scrape identified and extracted **5,489 services** that are directly listed and navigable through the platform’s public ministry → department → agency structure.

This represents the complete set of services that are:

- Directly exposed via ministry and agency landing pages
- Linked through standard public navigation paths
- Accessible without authentication or hidden query mechanisms

No duplicate services were observed.

### Interpreting the 22,000 Figure

The substantial gap between the reported “22,000+ services” and the 5,489 services observed suggests that:

- The reported figure may include:
  - Sub-services
  - Transactional variations
  - Form-level endpoints
  - Internal system entries
- Some services may be nested in deeper navigation layers not surfaced through the primary ministry/agency hierarchy
- Certain services may only be accessible after authentication, form progression, or dynamic interaction

There is no evidence that the discrepancy is caused by scraper malfunction.
Given the structured and consistent extraction across ministries, agencies, and departments, the observed service count reflects the services that are programmatically discoverable via the publicly exposed site structure.

That said, complete enumeration of all possible transactional endpoints remains future work.

### Structural Consistency

Across entities:

- **27 ministries** extracted
- **54 departments** extracted
- **286 agencies** extracted
- **5,489 services** extracted
- **15 FAQs** extracted

No duplicate IDs were detected in any entity.

Minor discrepancies were observed between reported and observed counts for certain ministries, but these remain negligible (typically differences of 1–2 services) and are likely attributable to transient listing differences or conditional visibility rather than systemic extraction issues.

### Missing Data

Missing values are minimal and correspond to fields that are genuinely absent on the website rather than extraction errors. For example:

- Two ministries lack descriptions
- Two departments lack observed service counts
- One agency lacks description and logo metadata

The services dataset itself contains no missing values in core relational fields.

### Summary

This dataset captures the publicly navigable service surface of the eCitizen platform with high structural integrity and minimal data loss.

While the platform’s reported service total significantly exceeds the number of directly discoverable services, the extracted dataset represents the coherent, publicly structured layer of the system.

Deeper transactional enumeration, hidden endpoints, and authenticated flows are intentionally out of scope and are left for future expansion.

## Dataset Structure and Documentation

- Documentation describing the dataset structure, field definitions, and relationships is provided in the `docs/` directory:
  - [schema.md](docs/schema.md) defines the structural schema of the dataset, including entities and their relationships.
  - [data_dictionary.md](docs/data_dictionary.md) provides detailed definitions and descriptions for each field in the dataset.
  - [metadata.md](docs/metadata.md) offers context on data sources, collection methodology, and limitations.

## Contents

- In addition to the final dataset, this repository documents the data collection, processing, and validation steps used to produce the dataset.
- Repository structure is as follows:

### `data/`

- Contains data produced by the scraping and processing pipeline.
- `raw/`: Raw HTML files and initial scraped outputs.
- `processed/`: Cleaned and structured datasets in CSV and JSON formats.

### `docs/`

- Dataset documentation and supporting metadata.
- `data_dictionary.md`: Field definitions and descriptions.
- `metadata.md`: Dataset context, sources, and collection notes.
- `schema.md`: Dataset schema specification.

### `scraper/`

- Scraping and processing scripts used to collect the data.
- `run.py` serves as the primary entry point for executing the scrape.

### `planning/`

- Planning and governance documentation for dataset creation.
- `scope.md`: Dataset objectives and boundaries.
- `data_sources.md`: Source URLs and platform sections scraped.
- `methodology.md`: Data collection and processing approach.
- `legal_considerations.md`: Legal and ethical considerations.

### `kaggle/`

- Files required for Kaggle dataset publication.
- `dataset_description.md`: Kaggle-facing dataset description.
- `kaggle_metadata.json`: Kaggle metadata configuration.

### `notebooks/`

- Jupyter notebooks used for data exploration, validation, and analysis.

## Usage

- This dataset may be used for:
  - Research into digital government service delivery.
  - Development of AI assistants and public-service tooling.
  - Analysis of service availability and accessibility on the eCitizen platform.
- Users are encouraged to cite this repository when using the dataset in academic, research, or commercial work.
- Users must ensure compliance with any applicable terms of service and legal considerations outlined in `legal_considerations.md`.

## Citation

If you use this dataset in your work, please cite it as follows:

> Karanja, A. (2026). Kenya eCitizen Services Dataset.
> GitHub repository: <https://github.com/karaalv/kenya-ecitizen-services-dataset>

## Maintenance

- There are currently no guaranteed update schedules for this dataset.
- Updates may be published if significant changes occur on the eCitizen platform or if coverage is expanded.
- Contributions are welcome via pull requests or issue submissions, particularly for corrections, coverage improvements, or documentation enhancements.

## License

- Two licences apply to this repository:
  - The dataset is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/) and can be found in the `data/LICENSE` file.
  - The scraping and processing code is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) and is provided in the root `LICENSE` file.
- Users should review the relevant licence files before reusing or redistributing the dataset or code.

## Contributing

- Contributions are welcome and encouraged.
- Please ensure all contributions comply with the applicable licences and include appropriate attribution.
- Contributors should follow existing code style and documentation conventions.
- For collaboration enquiries, contact: [alvinnjiiri@gmail.com](mailto:alvinnjiiri@gmail.com)

## Contact

- For questions, feedback, or issues related to this dataset, please contact:
  [alvinnjiiri@gmail.com](mailto:alvinnjiiri@gmail.com)
