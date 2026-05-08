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

### 1. Disease Relevance

How strongly is the target associated with the disease?

Examples:

- Disease-specific expression
- Association with prognosis
- Association with treatment response or resistance
- Disease subtype relevance
- Repeated evidence from biomedical literature

### 2. Functional Importance

Does the target play an important functional role in the disease mechanism?

Examples:

- Disease driver
- Resistance mediator
- Essential pathway node
- Immune regulation factor
- Pathological signaling regulator

### 3. Targetability

Can the target be modulated by a drug?

Examples:

- Cell-surface antigen
- Receptor
- Enzyme
- Kinase
- Secreted cytokine
- Intracellular disease-driving protein
- RNA or splice variant

### 4. Disease Selectivity

Is the target more relevant in disease tissue or disease state than in normal physiology?

This criterion helps reduce targets that are broadly essential in both normal and disease cells.

### 5. Safety Window

Does the target have a reasonable safety profile?

Examples:

- Low expression in vital normal tissues
- Limited risk of on-target off-tumor toxicity
- Avoidance of broadly essential pathways
- Manageable immune or systemic toxicity risk

### 6. Modality Fit

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

### 7. Evidence Strength

How strong is the supporting evidence?

Examples:

- Literature evidence
- Preclinical validation
- Clinical validation
- Public database support
- Existing drug development precedent

---

## 8. DTSR Scoring System

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

---

## 8. Current Implementation Status

The current version of DTSR is an MVP-stage Streamlit prototype.

At this stage, DTSR does not yet perform real-time PubMed API search.  
Instead, it provides the first working interface and documents the core analysis framework before public API integration.

Current implemented components:

- Streamlit-based search strategy UI
- Disease name input field
- PubMed-style search query generation
- Public API-based data access principle notice
- Planned public API source list
- DTSR scoring framework documentation
- Sample target scouting report example

---

## 9. Current Project Structure

```text
dtsr-drug-target-scoutter/
├── README.md
├── app.py
├── requirements.txt
├── docs/
│   └── scoring_framework.md
└── examples/
    └── sample_report.md
