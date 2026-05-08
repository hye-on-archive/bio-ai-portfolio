# DTSR: Drug Target ScoutteR

## 1. Project Overview

DTSR, Drug Target ScoutteR, is a Bio-AI research platform concept designed to help users explore and prioritize potential drug development targets based on disease mechanisms.

The goal of DTSR is not to simply list disease-associated biomarkers.  
Instead, DTSR aims to identify target candidates that may have real drug development potential by considering disease relevance, functional importance, targetability, safety window, modality suitability, and literature evidence.

This project is part of my Bio × AI portfolio for learning and demonstrating how biomedical domain knowledge can be connected with generative AI and service development.

---

## 2. Core Concept

Many biomarkers are frequently mentioned in biomedical papers, but not all biomarkers are suitable drug development targets.

A useful drug target should be evaluated through multiple perspectives, such as:

- Is it strongly related to the disease?
- Does it play a functional role in disease progression?
- Can it be accessed or modulated by a drug?
- Is it more important in disease tissue than in normal tissue?
- Is there a reasonable safety window?
- Which drug modality is suitable for this target?
- Is there enough literature or biological evidence?

DTSR is designed to support this filtering process.

---

## 3. Platform Direction

Although my research background includes prostate cancer, DTSR is not intended to be limited to prostate cancer.

DTSR is designed as a general disease-based drug target scouting platform that can be expanded to multiple disease areas, including:

- Cancer
- Autoimmune diseases
- Metabolic diseases
- Neurodegenerative diseases
- Rare diseases
- Infectious diseases
- Fibrotic diseases
- Cardiovascular diseases

Prostate cancer may be used as one example disease in the MVP, but the long-term direction is to understand disease-specific pathological mechanisms and identify actionable target candidates across diverse diseases.

---

## 4. Target Filtering Framework

DTSR evaluates target candidates using the following criteria.

### 4.1 Disease Relevance

How strongly is the target associated with the disease?

Examples:

- Disease-specific expression
- Association with prognosis
- Association with treatment response or resistance
- Disease subtype relevance
- Repeated evidence from biomedical literature

### 4.2 Functional Importance

Does the target play an important functional role in the disease mechanism?

Examples:

- Disease driver
- Resistance mediator
- Essential pathway node
- Immune regulation factor
- Pathological signaling regulator

### 4.3 Targetability

Can the target be modulated by a drug?

Examples:

- Cell-surface antigen
- Receptor
- Enzyme
- Kinase
- Secreted cytokine
- Intracellular disease-driving protein
- RNA or splice variant

### 4.4 Disease Selectivity

Is the target more relevant in disease tissue or disease state than in normal physiology?

This criterion helps reduce targets that are broadly essential in both normal and disease cells.

### 4.5 Safety Window

Does the target have a reasonable safety profile?

Examples:

- Low expression in vital normal tissues
- Limited risk of on-target off-tumor toxicity
- Avoidance of broadly essential pathways
- Manageable immune or systemic toxicity risk

### 4.6 Modality Fit

Which drug modality may be suitable for this target?

Examples:

- ADC
- CAR-T
- Bispecific antibody
- Monoclonal antibody
- Small molecule inhibitor
- PROTAC / TPD
- RNA therapy
- Gene therapy
- Enzyme replacement therapy

### 4.7 Evidence Strength

How strong is the supporting evidence?

Examples:

- Literature evidence
- Preclinical validation
- Clinical validation
- Public database support
- Existing drug development precedent

---

## 5. DTSR Scoring System

DTSR uses a simple prototype scoring system.

Each criterion is scored from 1 to 5.

Scoring categories:

- Disease relevance
- Functional importance
- Targetability
- Disease selectivity
- Safety window
- Modality fit
- Evidence strength

Total score:

```text
DTSR Score = sum of 7 criteria / 35
```

---

## 6. UniProt Validation Status

The current version of DTSR includes a UniProt public API validation feature.

After extracting and classifying candidate terms from PubMed titles and abstracts, DTSR validates selected candidate terms using the UniProt public API.

This step helps DTSR check whether extracted candidate terms can be matched to reviewed human protein entries.

---

## 7. Implemented UniProt Validation Features

Current implemented features include:

- UniProt public API connection
- Candidate term search against UniProtKB
- Human protein filtering using organism ID 9606
- Reviewed protein entry prioritization
- UniProt accession retrieval
- UniProt entry name retrieval
- Gene name retrieval
- Recommended protein name retrieval
- Organism information retrieval
- Functional annotation retrieval when available
- UniProt URL generation

Current UniProt validation output includes:

```text
Candidate Term
Frequency
Category
Possible Modality
Classification Note
UniProt Match
UniProt Accession
UniProt Entry
Gene Name
Protein Name
Organism
Function
UniProt URL
```

---

## 8. Open Targets Entity Search Status

The current version of DTSR includes an Open Targets entity search prototype.

After retrieving PubMed metadata and abstracts, extracting candidate terms, classifying them, and validating selected candidates with UniProt, DTSR now searches Open Targets entities related to:

- The input disease name
- UniProt-validated candidate gene names

This step prepares DTSR for future disease-target association evidence retrieval.

---

## 9. Implemented Open Targets Features

Current implemented features include:

- Open Targets GraphQL API connection
- Disease entity search using the input disease name
- Phenotype entity search support
- Target entity search using UniProt-validated gene names
- Open Targets ID retrieval
- Entity name retrieval
- Entity type retrieval
- Entity description retrieval
- Disease entity candidate table
- Target entity candidate table

Current Open Targets output includes:

```text
Open Targets ID
Name
Entity Type
Description
```

---

## 10. Open Targets Association Score Prototype

The current version of DTSR includes an Open Targets association score prototype.

After retrieving PubMed metadata and abstracts, extracting candidate terms, validating selected candidates with UniProt, and searching Open Targets disease and target entities, DTSR attempts to retrieve disease-target association scores from Open Targets.

This step helps DTSR move from entity search toward evidence-based target prioritization.

---

## 11. Implemented Association Score Features

Current implemented features include:

- Open Targets disease entity search
- Open Targets target entity search
- Automatic selection of the first disease entity candidate
- Target-disease association score query prototype
- Evidence type score retrieval when available
- Association status display
- Association score table generation

Current association output includes:

```text
Candidate Term
Gene Name
Open Targets Target ID
Open Targets Target Name
Open Targets Disease ID
Association Score
Association Status
Evidence Type Scores
```

