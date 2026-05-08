# Open Targets Integration Plan

## 1. Purpose

The purpose of Open Targets integration is to evaluate whether candidate targets extracted by DTSR have known disease-target association evidence.

DTSR currently performs the following steps:

```text
Disease name input
↓
PubMed metadata and abstract retrieval
↓
Candidate biomarker / target term extraction
↓
Candidate classification and modality suggestion
↓
UniProt validation for protein / gene identity
