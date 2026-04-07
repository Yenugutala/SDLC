Loading PDF: dps/samples/DPS - UCM .pdf

Found 11 page(s). Sending to GPT-4o via OpenRouter...

  Extracting page 1...
============================================================
PAGE 1
============================================================
# RITM2195089-DPS-Unified Customer Master NA

## Document Signatures (User Requirements)

| Role                       | Name       | Signature                                                                                                                                                                                                                       | Date        |
|----------------------------|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|
| Business Data Product Owner | Nikhil Mugye | ![DocuSigned by: Nikhil Mugye](signature) <br> Signer Name: Nikhil Mugye <br> Signing Reason: I approve this document <br> Signing Time: 24-Aug-2023 | 24-Aug-2023 |

## Document Signatures (Functional Design)

| Role                    | Name           | Signature                                                                                                                                                                                                                       | Date        |
|-------------------------|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|
| Architecture Committee  | Don Peacock    | ![DocuSigned by: Don Peacock](signature) <br> Signer Name: Don Peacock <br> Signing Reason: I approve this document <br> Signing Time: 24-Aug-2023 | 24-Aug-2023 |
| TGS Functional Lead     | Kartik Ravi    | ![DocuSigned by: Kartik Ravi](signature) <br> Signer Name: Kartik Ravi <br> Signing Reason: I approve this document <br> Signing Time: 24-Aug-2023 | 24-Aug-2023 |
| TGS Development Lead    | Anindya Bose   | ![DocuSigned by: Anindya Bose](signature) <br> Signer Name: Anindya Bose <br> Signing Reason: I approve this document <br> Signing Time: 24-Aug-2023 | 24-Aug-2023 |
| TGS AMO Lead            | Bobby Velagapudi | ![DocuSigned by: Bobby Velagapudi](signature) <br> Signer Name: Bobby Velagapudi <br> Signing Reason: I approve this document <br> Signing Time: 24-Aug-2023 | 24-Aug-2023 |

## Document Revision History

| Revision | Author     | Reason for Revision |
|----------|------------|---------------------|
| 01       | Kartik Ravi |                     |

## Table of Contents

  Extracting page 2...
============================================================
PAGE 2
============================================================
# 1.0 Purpose

The purpose of this DPS document is to describe the information that is necessary to visualize company’s growth and profitability from our Sales Teams perspective that sell BD products to our true end customers.

This document will provide business analytics group and development team a complete understanding of the requirements for the Commercial Operations Unified Customer Master Data Model, how it works, and what will be available to consume for downstream reporting applications.

# 2.0 Scope

## 2.1 In scope for this document is:

- The Scope represents the Unified Customer Master Model requirements for the NA Region Commercial Operations full implementation using Azure Databricks platform.
- Scope includes business criteria and expectations as an outcome of the full implementation.

## 2.2 Out of scope for this document is:

- System Design and Build Requirements
- Detailed technical mapping, design specifications, and approach.

# 3.0 Definitions / Acronyms

The table below describes acronyms used in this document.

| Term / Abbreviation | Definition |
|---------------------|------------|
| Azure Databricks    | Azure Databricks(ADB) is a unified, open analytics platform for building, deploying, sharing, and maintaining enterprise-grade data, analytics, and AI solutions at scale |
| HANA / BW4HANA      | SAP version - High Performance Analytical Appliance An in-memory, column-oriented, relational database management system |
| Calculation View(s) | A calculation view is a flexible information view that one can use to define more advanced slices on the data available in the SAP HANA database |
| KPI                 | Key Performance Indicators |
| SLT                 | SLT is the ETL (Extract, Transform, Load) tool which allows us to load and replicate data in real-time or schedule data from SAP source system or Non-SAP System into SAP HANA Database |
| SDI                 | Smart Data Integration |
| ADF                 | Azure Data factory |
| SLA                 | Service Level Agreement |
| Dashboard           | A data dashboard is a tool business use to help track, analyze, and display data, usually to gain deeper insight into the organization |

  Extracting page 3...
============================================================
PAGE 3
============================================================
## ERP
| ERP                      | Enterprise resource planning (ERP) manages and integrates business processes through a single system |
|--------------------------|-----------------------------------------------------------------------------------------------------|
| Upstream Applications    | Source systems, SAP, JDE, etc.                                                                      |
| Downstream Applications  | Visualization tools, Power BI, etc.                                                                 |
| PBI                      | Power BI                                                                                            |
| PBI App                  | A Power BI app typically contains multiple reports, with each report containing multiple pages or dashboards. Apps are published for consumption in Power BI Service. |
| PBI Report               | A Power BI report represents a logical grouping of pages or dashboards containing multiple visualizations in tabular or chart form |
| QS                       | Qlik Sense                                                                                          |
| BI                       | Business Intelligence                                                                               |
| CCO                      | Commercial & Customer Operations                                                                    |

## 4.0 References
SIAM Project Managed docs.

- APP00011880 Azure DataBricks PRD Global
- APP00008364 - MS PowerBI PRD Global (General)
- DOC0019340 SAP_BW4Hana_RAA_001 (Revision 3)
- DOC0023304 APPLICATION_MIGRATION_TO_HANA_RIA001_GBL (Revision 4)
- DMND0119894, PRJ0256660: 1008218 Migration of Reporting and Data Tools to HANA

Plan view ID: 1008218

| File | Modified |
|------|----------|
| No files shared here yet. | Drag and drop to upload or browse for files |

## 5.0 Roles and Responsibilities
Refer to Section 5.0 in [System Development Life Cycle - TGS Led Analytics](#)

5.1 Author - Compiles input from core team and authors the URS document in accordance BD IT policies and procedures.

5.2 Business Owner - Approves the URS Document to ensure the end users’ needs have been captured.

5.3 Business Partner - Approves the URS to ensure the URS is in alignment with IT guiding principles and provides input to the URS to incorporate the end user needs into the document.

  Extracting page 4...
============================================================
PAGE 4
============================================================
5.4 Techno Functional Lead – Provides expertise on functional area as well as oversees technical solution to meet application standards

5.5 BD Solution Delivery Architect – Owns the overall technical solution from BD and responsible for approving the design as well as ensuring the application meets BD standards

5.6 Solution Build Team – Development team responsible for the execution of the data model

5.7 QA / Validation Approver – Needs to ensure URS was created in accordance with BD GIT specific policies and procedures.

6.0 Assumptions, Dependencies and Constraints

### 6.1 Assumptions

- Canonical model will be for North America Region (US & Canada)
- System connection/configuration and supporting environments are available as per project timeline for development to start
- Development resources will be onboarded on time to meet project timelines
- Ability to view and validate data agnostic of end state applications/tools.
- Solution needs to integrate and cooperate with the new Fixed Capacity Enhancement team (Bit by Bit team)
- New Fixed Capacity Enhancement team is responsible to build the visuals/dashboard
- Governance for AMO and SLA for bug-fix/production implementation following current architecture until data mesh process is standardized.

### 6.2 Dependencies

- Data ingestion from source systems is completed and source system tables/supporting data is replicated into the Azure data bricks landscape.
- Various Azure data bricks tools like clusters, notebooks, logical system connections with other BD systems like SAP, BW4HANA and external systems like Salesforce will need to be made available to choose from, at different stages of build.

### 6.3 Constraints

#### 6.3.1 Timelines and Milestones

- Timeline will be defined as a part of Jira Product backlog prioritization by Data product owner.

#### 6.3.2 Compatibility

- Azure Databricks and upstream applications will need to be compatible.

#### 6.3.3 Availability

- **User Acceptance Testing** – Users will need to be identified and committed according to Data Product timeline.
- Business SLA for dashboard refresh is (Need time) to support this requirement data needs to be available earlier as captured in requirements.

#### 6.3.4 Maintenance

- Maintenance will follow the production support model.

#### 6.3.5 Scope lock

- Once Scope locked/ Design defined, the enhancements completed in parallel with project can NOT change Design/Solution

  Extracting page 5...
============================================================
PAGE 5
============================================================
```
7.0 User Requirements

7.1 Data Product Requirements

| Req. ID# | Requirement Description |
|----------|-------------------------|
| 7.1.1    | Unified Customer Master fields available for consumption will include: <br><br> • Keys <br> o ERP Customer Key <br> o JDE Survivor Key <br> o Logical Survivor Key <br> o Survivor Customer Key <br> • Columns <br> o Account Group <br> o Account Group ID <br> o Account Group with ID <br> o Alternate Site Division <br> o Alternate Site IDN <br> o BioScience Group <br> o Central Billing Block <br> o Central Delivery Block <br> o Central Order Block <br> o Created On Date <br> o CRO Group <br> o Customer Classification <br> o Customer Classification ID <br> o Customer Classification with ID <br> o Date Added <br> o DH Hospital ID <br> o Distributor Division <br> o Distributor Group <br> o Distributor Parent <br> o Distributor Type <br> o Division ID <br> o EAN Address <br> o EAN Address2 <br> o EAN Backfill Flag |
```

  Extracting page 6...
============================================================
PAGE 6
============================================================
- EAN City
- EAN Class of Trade
- EAN Country
- EAN Hierarchy Level
- EAN Latitude
- EAN Longitude
- EAN Network
- EAN Network Parent
- EAN Network Parent Backfill Flag
- EAN Network Parent with #
- EAN Network Parent#
- EAN Network with #
- EAN Network#
- EAN Postal Code
- EAN Source ID
- EAN Source System
- EAN State
- Enterprise Account Name
- Enterprise Account Name with #
- Enterprise Account Number
- ERP 5 Digit Zip
- ERP Active Flag
- ERP Address
- ERP Address2
- ERP Address3
- ERP Address4
- ERP City
- ERP Class of Trade Level1
- ERP Class of Trade Level1 with ID
- ERP Class of Trade Level2
- ERP Class of Trade Level2 with ID
- ERP COT Acute Rollup Level1
- ERP COT Acute Rollup Level2
- ERP Country
- ERP Customer
- ERP Customer Function

  Extracting page 7...
============================================================
PAGE 7
============================================================
- ERP Customer Name2
- ERP Customer Name3
- ERP Customer Name4
- ERP Customer#
- ERP Fax Number
- ERP In Reltio
- ERP Merged Category
- ERP Merged Category ID
- ERP Phone Number
- ERP PO Box
- ERP PO Box City
- ERP PO Box Postal Code
- ERP Postal Code
- ERP Search Term
- ERP Source Class of Trade ID
- ERP Source System
- ERP Source System ID
- ERP State
- ERP Transportation Zone
- ERP URL
- Everest Customer Group1
- Everest Customer Group1 ID
- Everest Customer Group1 with ID
- Everest Customer Group2
- Everest Customer Group2 ID
- Everest Customer Group2 with ID
- Everest Customer Group3
- Everest Customer Group3 ID
- Everest Customer Group3 with ID
- Everest Customer Group5
- Everest Customer Group5 ID
- Everest Customer Group5 with ID
- Everest Nielsen ID
- Government Division ID
- Government Flag
- Government IDN

  Extracting page 8...
============================================================
PAGE 8
============================================================
- Government IDN Co
- Government IDN Division
- Government IDN Parent
- Government Parent
- Government Strategic ID
- JDE Customer Type
- JDE Customer Type ID
- JDE Customer Type with ID
- JDE Survivor Source ID
- JDE Survivor#
- Lab Group
- Logical Survivor Source ID
- Logical Survivor#
- Membership Added Date
- Membership Deleted Date
- Membership Priority
- Membership SubGroup
- Membership Type
- Reltio ERP#
- Strategic Division
- Strategic Grouping
- Strategic ID
- Strategic IDN
- Strategic IDN Parent
- Strategic Parent
- Survivor Address
- Survivor Address2
- Survivor Backfill Flag
- Survivor City
- Survivor Class of Trade Level1
- Survivor Class of Trade Level1 with ID
- Survivor Class of Trade Level2
- Survivor Class of Trade Level2 with ID
- Survivor COT Acute Rollup Level1
- Survivor COT Acute Rollup Level2
- Survivor Country

  Extracting page 9...
============================================================
PAGE 9
============================================================
```
- Survivor Customer
- Survivor Customer#
- Survivor Function
- Survivor Latitude
- Survivor Longitude
- Survivor Merged Category
- Survivor Merged Category ID
- Survivor Merged Category Type
- Survivor Postal Code
- Survivor Source System
- Survivor State
- Tahiti Account Type
- Tahiti Account Type ID
- Tahiti Account Type with ID
- Tahiti DUNS#
- Tahiti GPO Hospital ID
- Tahiti GPO IDN
- Tahiti Industry
- Tahiti Industry Code
- Tahiti Industry with ID
- Tahiti Sales Orgs

### 7.2 Source System

| Req. ID# | Requirement Description |
|----------|-------------------------|
| 7.2.1    | EVEREST ECC             |
| 7.2.2    | TAHITI                  |
| 7.2.3    | BARD                    |

### 7.3 Security Groups (Access)

| Req. ID# | Requirement Description |
|----------|-------------------------|
|          |                         |

### 7.4 Visualization Layer

| Req. ID# | Requirement Description |
|----------|-------------------------|
|          |                         |

## 8.0 Functional Design

A summarized list of all functional requirements is given in the table below. This list is followed by each requirement in detail.
```

  Extracting page 10...
============================================================
PAGE 10
============================================================
```
| Req. ID# | Functional Requirement/Description |
|----------|------------------------------------|
| 8.1.1    | 1. Develop a SQL solution to build customer master from various source systems mentioned above 2. Develop a SQL solution to build unified customer master from above silos of customer master 3. The specs for the unified customer master is in this link bdx_unified_customer_master_na (2).xlsx 4. The HQL files for unified customer master is in the link HQL - Unified Customer Master |

8.1 Data Product Requirements

8.1.1 Transformation & Business Logic:

8.2 Data Latency

The data latency requirements are given in the table below.

| Source System | Data Posted into Source System By | Data Should be available in PBI Dashboards by* |
|---------------|-----------------------------------|------------------------------------------------|

8.3 Data Ingestion

| Req. ID# | Requirement Description |
|----------|-------------------------|
| 8.3.1    | All data ingested via Attunity should be CDC. |
| 8.3.2    | All data where CDC is not an option should be scheduled as per daily frequency. |

8.4 Security (Definition)

| Req. ID# | Requirement Description |
|----------|-------------------------|

8.5 Regulatory

| Req. ID# | Requirement Description |
|----------|-------------------------|

9.0 Architecture Committee

9.1 Infrastructure

| Req. ID# | Requirement Description |
|----------|-------------------------|
| 9.1.1    | Data Product Build follows Theia Datamesh architecture and |
```

  Extracting page 11...
============================================================
PAGE 11
============================================================
```
principles.

10.0 AMO Support

| Req. ID# | Requirement Description                        | AMO Support |
|----------|------------------------------------------------|-------------|
| 10.1     | Jobs need to be monitored daily.               | ☑ Standard  |
|          |                                                | ☐ Additional|
| 10.2     | Reported issues need to resolve in timely      | ☑ Standard  |
|          | basis.                                         | ☐ Additional|

11.0 Mapping Specs

| File | Modified |
|------|----------|
| No files shared here yet. | |
| Drag and drop to upload or browse for files | |

12.0 Appendix

END OF DOCUMENT
```

