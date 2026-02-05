# Kenya eCitizen Services Dataset - Data Sources

- This document outlines the specific publicly accessible sections of the Kenya eCitizen platform that were scraped to create the Kenya eCitizen Services Dataset.
- All data was collected exclusively from unauthenticated pages available to the general public, without bypassing access controls or authentication mechanisms.
- The eCitizen platform serves as the primary digital portal for accessing government services in Kenya and is available at:  
  <https://www.ecitizen.go.ke/>
- The dataset includes information on services, agencies, ministries, and FAQs as presented on the platform at the time of scraping.
- All URLs referenced below were valid at the time of data collection and may change as the platform evolves.
- The scrape targets the English-language version of the eCitizen platform.

## Data Sources

### Service Listings

The primary source of service information was the service listings available on the eCitizen platform. Services are organised under ministry pages, with each ministry page listing its associated agencies and the services offered under each agency.

The scraper navigated through each ministry page to extract service-level information across all associated agencies.

Example ministry pages include:

- <https://accounts.ecitizen.go.ke/en/ministries/executive-office-of-the-president>
- <https://accounts.ecitizen.go.ke/en/ministries/ministry-of-education>
- <https://accounts.ecitizen.go.ke/en/ministries/ministry-of-health>

A comprehensive list of ministry pages is available via the eCitizen “National Ministries” index page:

- <https://accounts.ecitizen.go.ke/en/home/national-ministries>

---

### Agency Information

Agency information was extracted from the agency listing page on the eCitizen platform, which provides a consolidated directory of government agencies responsible for service delivery.

Source page:

- <https://accounts.ecitizen.go.ke/en/agencies>

This page includes agency names, descriptions, logo URLs, and links to individual agency pages as presented on the platform.

---

### Ministry Information

Ministry-level information was extracted directly from individual ministry pages on the eCitizen platform. Each ministry page provides a brief description of the ministry, along with aggregate counts of associated agencies and services.

The full list of ministry pages is accessible via:

- <https://accounts.ecitizen.go.ke/en/home/national-ministries>

---

### Frequently Asked Questions (FAQs)

Frequently asked questions related to the eCitizen platform were extracted from the public help and support section of the site.

Source page:

- <https://accounts.ecitizen.go.ke/en/help-and-support>
