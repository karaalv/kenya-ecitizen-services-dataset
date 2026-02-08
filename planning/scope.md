# Kenya eCitizen Services Dataset - Scope

## Dataset Objectives

- The primary objective of this dataset is to provide a structured, accessible, and well-documented collection of information about services publicly listed on the Kenya eCitizen platform.
- The dataset is intended to support research, analysis, and tooling related to digital government service delivery in Kenya.
- A key motivation behind creating this dataset is to support the development of *Mwalika*, an AI assistant designed to help users navigate and utilise the eCitizen platform more effectively. More information can be found in the [Mwalika repository](https://github.com/karaalv/mwalika-documentation).
- The scope of data collection includes publicly accessible service listings, descriptions, categories, responsible agencies, ministries, and associated FAQs available on the eCitizen platform at the time of scraping.

## Out of Scope

- This dataset does not include detailed operational information about services, such as application workflows, eligibility criteria, processing timelines, or user-submitted content.
- The dataset does not include information about the internal operation of the eCitizen platform, including technical infrastructure, authentication mechanisms, user data, or internal workflows.
- The scope of scraped services is limited strictly to those publicly listed on the eCitizen platform and excludes services offered via other government portals, offline channels, or private intermediaries.
- The scope of FAQs is limited to those directly presented on the eCitizen platform and excludes external documentation, help articles, or third-party resources.

## Desired Dataset Structure

- The dataset contains **four primary entities**, with other entities existing to support the structure and relationships between these primary entities:
  - **Services**
    Publicly listed government services available on the eCitizen platform, including their names, responsible agencies and ministries, and links to official service pages.
  - **Agencies**
    Government agencies listed on the eCitizen platform, including their names, descriptions, parent ministries, and associated service listings.
  - **Ministries**
    Government ministries represented on the eCitizen platform, including high-level descriptions and aggregate counts of associated agencies and services.
  - **FAQs**
    Frequently asked questions and answers as presented on the eCitizen platform.

- Relationships between entities are represented using derived identifiers or names extracted from the platform. These identifiers are not official government identifiers and may change if the platform structure changes.

- The dataset is created by scraping publicly accessible sections of the eCitizen platform and structuring the extracted information into formats suitable for analysis and downstream use.
- The dataset is published in both CSV and JSON formats to support a range of research, analytical, and application development use cases.

## Dataset Features Cheatsheet

- This section provides a high-level summary of the key fields desired in each main dataset entity.
- It is intended as a quick reference to the fields that are expected to be derived in each entity, and is not intended to provide a representative sample of the structure of the dataset or the relationships between entities. For a detailed specification of the dataset schema, including field definitions, data types, and relationships, please refer to the [dataset schema documentation](../docs/schema.md).
- For detailed field definitions and constraints, refer to the [data dictionary](../docs/data_dictionary.md) and for dataset context and collection notes, refer to the [metadata documentation](../docs/metadata.md).

### Services

- `service_name`: Name of the service as listed on the eCitizen platform.
- `parent_agency`: Government agency responsible for the service.
- `parent_ministry`: Government ministry under which the service falls.
- `service_url`: URL of the service page on the eCitizen platform.

### Agencies

- `agency_name`: Name of the government agency as listed on the eCitizen platform.
- `parent_ministry`: Government ministry under which the agency falls.
- `agency_description`: Brief description of the agency as listed on the eCitizen platform.
- `logo_url`: URL of the agency logo as presented on the eCitizen platform.
- `agency_url`: URL of the agency page on the eCitizen platform.

### Ministries

- `ministry_name`: Name of the government ministry as listed on the eCitizen platform.
- `ministry_description`: Brief description of the ministry as listed on the eCitizen platform.
- `total_agencies`: Total number of agencies under the ministry as reported on the platform.
- `total_services`: Total number of services under the ministry as reported on the platform.
- `ministry_url`: URL of the ministry page on the eCitizen platform.

### FAQs

- `question`: Frequently asked question as listed on the eCitizen platform.
- `answer`: Corresponding answer as listed on the eCitizen platform.
