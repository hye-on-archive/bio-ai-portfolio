import re
from collections import Counter

import pandas as pd
import requests
import streamlit as st
import xml.etree.ElementTree as ET


# ------------------------------------------------------------
# DTSR: Drug Target ScoutteR
# PubMed API MVP version with candidate term extraction
# and rule-based target classification
#
# This app retrieves publicly accessible PubMed metadata and abstracts
# using NCBI E-utilities and extracts candidate biomarker / target terms
# using a simple rule-based MVP approach.
#
# Data principle:
# - Use public metadata and abstracts
# - Do not collect or analyze paywalled full-text papers
# ------------------------------------------------------------


st.set_page_config(
    page_title="DTSR: Drug Target ScoutteR",
    page_icon="🧭",
    layout="wide"
)


PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


STOP_TERMS = {
    "DNA", "RNA", "mRNA", "miRNA", "PCR", "ELISA", "PBS",
    "USA", "UK", "CI", "HR", "OR", "RR", "SD", "SE",
    "AUC", "ROC", "OS", "PFS", "DFS",
    "COVID", "SARS", "HIV",
    "AND", "THE", "FOR", "WITH", "FROM"
}


PATHWAY_KEYWORDS = [
    "PI3K", "AKT", "MAPK", "ERK", "JAK", "STAT",
    "NF-kB", "WNT", "NOTCH", "TGF-beta", "mTOR",
    "apoptosis", "autophagy", "inflammation", "fibrosis",
    "oxidative stress", "immune response", "DNA repair",
    "cell cycle", "angiogenesis", "metabolism"
]


# 알려진 후보 용어에 대해 타깃 유형과 가능한 모달리티를 매칭하는 규칙 사전
# 현재는 MVP이므로 일부 대표 용어만 포함한다.
# 향후 UniProt, Open Targets, Human Protein Atlas API로 자동 검증할 예정이다.
KNOWN_TARGET_RULES = {
    "IL-6": {
        "category": "Cytokine / inflammatory mediator",
        "modality": "Neutralizing antibody / IL-6R blockade",
        "note": "Inflammatory cytokine involved in immune and inflammatory signaling."
    },
    "IL6": {
        "category": "Cytokine / inflammatory mediator",
        "modality": "Neutralizing antibody / IL-6R blockade",
        "note": "Inflammatory cytokine involved in immune and inflammatory signaling."
    },
    "TNF": {
        "category": "Cytokine / inflammatory mediator",
        "modality": "Neutralizing antibody / soluble receptor",
        "note": "Major inflammatory cytokine and clinically validated therapeutic target."
    },
    "TNF-alpha": {
        "category": "Cytokine / inflammatory mediator",
        "modality": "Neutralizing antibody / soluble receptor",
        "note": "Major inflammatory cytokine and clinically validated therapeutic target."
    },
    "JAK": {
        "category": "Intracellular kinase / signaling node",
        "modality": "Small molecule inhibitor",
        "note": "Kinase family involved in cytokine signaling."
    },
    "JAK1": {
        "category": "Intracellular kinase",
        "modality": "Small molecule inhibitor / JAK inhibitor",
        "note": "Drug target class with established small molecule inhibitor modality."
    },
    "JAK2": {
        "category": "Intracellular kinase",
        "modality": "Small molecule inhibitor / JAK inhibitor",
        "note": "Drug target class with established small molecule inhibitor modality."
    },
    "STAT": {
        "category": "Transcription factor / signaling mediator",
        "modality": "Indirect targeting / pathway modulation",
        "note": "Important signaling mediator but direct druggability may be challenging."
    },
    "EGFR": {
        "category": "Receptor / cell-surface protein",
        "modality": "Small molecule inhibitor / monoclonal antibody / ADC",
        "note": "Cell-surface receptor with established drug development precedent."
    },
    "HER2": {
        "category": "Receptor / cell-surface antigen",
        "modality": "Monoclonal antibody / ADC / bispecific antibody",
        "note": "Clinically validated cell-surface oncology target."
    },
    "ERBB2": {
        "category": "Receptor / cell-surface antigen",
        "modality": "Monoclonal antibody / ADC / bispecific antibody",
        "note": "Gene symbol for HER2; clinically validated oncology target."
    },
    "PD-L1": {
        "category": "Immune checkpoint ligand / cell-surface protein",
        "modality": "Immune checkpoint inhibitor / bispecific antibody",
        "note": "Immune checkpoint pathway target."
    },
    "PD1": {
        "category": "Immune checkpoint receptor",
        "modality": "Immune checkpoint inhibitor",
        "note": "T-cell immune checkpoint receptor."
    },
    "PD-1": {
        "category": "Immune checkpoint receptor",
        "modality": "Immune checkpoint inhibitor",
        "note": "T-cell immune checkpoint receptor."
    },
    "CTLA4": {
        "category": "Immune checkpoint receptor",
        "modality": "Immune checkpoint inhibitor",
        "note": "Immune checkpoint receptor involved in T-cell regulation."
    },
    "TP53": {
        "category": "Tumor suppressor / transcription factor",
        "modality": "Restoration strategy / synthetic lethality / indirect targeting",
        "note": "Major tumor suppressor; direct targeting is challenging."
    },
    "BRCA1": {
        "category": "DNA repair gene",
        "modality": "Synthetic lethality / PARP inhibitor strategy",
        "note": "DNA repair deficiency can create therapeutic vulnerability."
    },
    "BRCA2": {
        "category": "DNA repair gene",
        "modality": "Synthetic lethality / PARP inhibitor strategy",
        "note": "DNA repair deficiency can create therapeutic vulnerability."
    },
    "PARP": {
        "category": "DNA repair enzyme",
        "modality": "Small molecule inhibitor",
        "note": "DNA repair enzyme with established inhibitor strategy."
    },
    "BACE1": {
        "category": "Protease enzyme",
        "modality": "Small molecule inhibitor",
        "note": "Enzyme involved in amyloid-beta production."
    },
    "TREM2": {
        "category": "Immune receptor / microglial receptor",
        "modality": "Antibody / immune modulation",
        "note": "Microglial receptor linked to neuroinflammation."
    },
    "TAU": {
        "category": "Aggregating protein / neurodegeneration target",
        "modality": "Antibody / aggregation inhibitor / PROTAC exploration",
        "note": "Protein aggregation target relevant to neurodegenerative disease."
    },
    "PSMA": {
        "category": "Cell-surface antigen",
        "modality": "Radioligand therapy / ADC / CAR-T / bispecific antibody",
        "note": "Cell-surface target with strong oncology development precedent."
    },
    "AR": {
        "category": "Nuclear receptor / transcription factor",
        "modality": "Small molecule antagonist / degrader / pathway modulation",
        "note": "Hormone signaling target with established therapeutic relevance."
    },
    "METTL3": {
        "category": "RNA modification enzyme",
        "modality": "Small molecule inhibitor / RNA regulation strategy",
        "note": "Emerging epitranscriptomic target."
    },
}


def build_pubmed_query(disease_name: str) -> str:
    """
    사용자가 입력한 질환명을 PubMed 검색용 query로 바꾸는 함수.
    """

    disease_name = disease_name.strip()

    query = (
        f'("{disease_name}"[Title/Abstract]) '
        f'AND (biomarker OR "drug target" OR protein OR pathway OR mechanism)'
    )

    return query


def search_pubmed_ids(query: str, max_results: int) -> list:
    """
    PubMed ESearch API를 사용해 검색어에 해당하는 PMID 목록을 가져오는 함수.
    """

    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "sort": "relevance"
    }

    response = requests.get(PUBMED_ESEARCH_URL, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()
    pmids = data.get("esearchresult", {}).get("idlist", [])

    return pmids


def get_text_from_element(element) -> str:
    """
    XML element 안의 모든 텍스트를 하나로 합치는 보조 함수.
    """

    if element is None:
        return ""

    return " ".join(element.itertext()).strip()


def extract_article_info(article) -> dict:
    """
    PubMed XML에서 논문 제목, 저널, 연도, 초록, PMID를 추출하는 함수.
    """

    pmid_element = article.find(".//PMID")
    pmid = pmid_element.text if pmid_element is not None else ""

    title_element = article.find(".//ArticleTitle")
    title = get_text_from_element(title_element)

    journal_element = article.find(".//Journal/Title")
    journal = get_text_from_element(journal_element)

    year_element = article.find(".//JournalIssue/PubDate/Year")
    if year_element is not None:
        year = year_element.text
    else:
        medline_date_element = article.find(".//JournalIssue/PubDate/MedlineDate")
        year = medline_date_element.text if medline_date_element is not None else ""

    abstract_elements = article.findall(".//Abstract/AbstractText")
    abstract_parts = [get_text_from_element(element) for element in abstract_elements]
    abstract = " ".join([part for part in abstract_parts if part]).strip()

    pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

    return {
        "PMID": pmid,
        "Title": title,
        "Journal": journal,
        "Year": year,
        "Abstract": abstract,
        "PubMed URL": pubmed_url
    }


def fetch_pubmed_details(pmids: list) -> list:
    """
    PMID 목록을 PubMed EFetch API에 보내서 논문 상세정보를 가져오는 함수.
    """

    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }

    response = requests.get(PUBMED_EFETCH_URL, params=params, timeout=30)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    articles = root.findall(".//PubmedArticle")

    results = [extract_article_info(article) for article in articles]

    return results


def extract_candidate_terms(text: str) -> list:
    """
    논문 제목과 초록에서 후보 타깃/바이오마커처럼 보이는 용어를 추출하는 함수.

    현재는 MVP 단계이므로 정교한 AI 모델이 아니라 규칙 기반 방식을 사용한다.
    """

    if not text:
        return []

    candidate_terms = []

    uppercase_pattern = r"\b[A-Z][A-Z0-9-]{1,12}\b"
    uppercase_matches = re.findall(uppercase_pattern, text)

    for term in uppercase_matches:
        if term not in STOP_TERMS and len(term) >= 2:
            candidate_terms.append(term)

    greek_pattern = r"\b[A-Z]{2,6}-(?:alpha|beta|gamma|delta)\b"
    greek_matches = re.findall(greek_pattern, text, flags=re.IGNORECASE)

    for term in greek_matches:
        candidate_terms.append(term)

    lower_text = text.lower()

    for keyword in PATHWAY_KEYWORDS:
        if keyword.lower() in lower_text:
            candidate_terms.append(keyword)

    return candidate_terms


def classify_candidate_term(term: str) -> dict:
    """
    추출된 후보 용어를 타깃 유형과 가능한 모달리티로 분류하는 함수.

    1. 먼저 KNOWN_TARGET_RULES 사전에 있는지 확인한다.
    2. 없으면 간단한 패턴 기반 규칙으로 추정한다.
    3. 그래도 알 수 없으면 Unclassified로 표시한다.
    """

    normalized_term = term.strip()

    if normalized_term in KNOWN_TARGET_RULES:
        rule = KNOWN_TARGET_RULES[normalized_term]
        return {
            "Category": rule["category"],
            "Possible Modality": rule["modality"],
            "Classification Note": rule["note"]
        }

    upper_term = normalized_term.upper()

    if upper_term in KNOWN_TARGET_RULES:
        rule = KNOWN_TARGET_RULES[upper_term]
        return {
            "Category": rule["category"],
            "Possible Modality": rule["modality"],
            "Classification Note": rule["note"]
        }

    # 패턴 기반 추정 규칙
    if normalized_term.startswith("IL-") or upper_term.startswith("IL"):
        return {
            "Category": "Possible cytokine / interleukin",
            "Possible Modality": "Neutralizing antibody / receptor blockade",
            "Classification Note": "Pattern-based classification. Requires validation."
        }

    if upper_term.startswith("JAK"):
        return {
            "Category": "Possible intracellular kinase",
            "Possible Modality": "Small molecule inhibitor",
            "Classification Note": "Pattern-based classification. Requires validation."
        }

    if upper_term.startswith("CD"):
        return {
            "Category": "Possible cell-surface antigen",
            "Possible Modality": "Monoclonal antibody / ADC / CAR-T / bispecific antibody",
            "Classification Note": "Pattern-based classification. Requires validation."
        }

    if upper_term.startswith("HLA"):
        return {
            "Category": "Immune-related antigen presentation molecule",
            "Possible Modality": "Immune modulation / biomarker use",
            "Classification Note": "Pattern-based classification. Requires validation."
        }

    if upper_term.endswith("R") and len(upper_term) <= 8:
        return {
            "Category": "Possible receptor",
            "Possible Modality": "Antibody / small molecule / ligand-blocking therapy",
            "Classification Note": "Pattern-based classification. Requires validation."
        }

    return {
        "Category": "Unclassified candidate term",
        "Possible Modality": "Requires database validation",
        "Classification Note": "No rule matched. Future versions should validate using UniProt or Open Targets."
    }


def summarize_candidate_terms(papers: list) -> pd.DataFrame:
    """
    여러 논문에서 추출된 후보 용어의 등장 빈도를 계산하고,
    각 후보 용어에 대해 타깃 유형과 가능한 모달리티를 추가하는 함수.
    """

    all_terms = []

    for paper in papers:
        title = paper.get("Title", "")
        abstract = paper.get("Abstract", "")

        combined_text = f"{title} {abstract}"
        terms = extract_candidate_terms(combined_text)

        all_terms.extend(terms)

    term_counts = Counter(all_terms)

    rows = []

    for term, count in term_counts.most_common():
        classification = classify_candidate_term(term)

        rows.append(
            {
                "Candidate Term": term,
                "Frequency": count,
                "Category": classification["Category"],
                "Possible Modality": classification["Possible Modality"],
                "Classification Note": classification["Classification Note"]
            }
        )

    return pd.DataFrame(rows)


# ------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------

st.title("🧭 DTSR: Drug Target ScoutteR")

st.write(
    """
    **DTSR (Drug Target ScoutteR)** is a Bio-AI research platform concept
    designed to help users explore potential drug development targets
    based on disease mechanisms, literature evidence, and public biomedical data.
    """
)

st.info(
    """
    **Data Access Principle**

    DTSR analyzes publicly accessible biomedical information, including
    paper metadata, abstracts, open-access full text, and public biological databases
    available through public APIs.

    In this MVP version, DTSR retrieves **PubMed metadata and abstracts only**.
    It does not collect or analyze paywalled full-text papers without permission.
    """
)

st.divider()

st.header("1. Disease-based PubMed Search")

disease_name = st.text_input(
    "Enter a disease name:",
    placeholder="Example: Alzheimer's disease, rheumatoid arthritis, breast cancer"
)

max_results = st.selectbox(
    "Number of papers to retrieve:",
    options=[5, 10, 20],
    index=0
)

if st.button("Search PubMed with DTSR"):

    if disease_name.strip() == "":
        st.warning("Please enter a disease name first.")

    else:
        pubmed_query = build_pubmed_query(disease_name)

        st.subheader("2. PubMed Search Query")
        st.code(pubmed_query, language="text")

        with st.spinner("Searching PubMed via public API..."):
            try:
                pmids = search_pubmed_ids(pubmed_query, max_results)
                papers = fetch_pubmed_details(pmids)

                if not papers:
                    st.warning("No PubMed results found. Try another disease name or broader keyword.")

                else:
                    st.success(f"Retrieved {len(papers)} PubMed records using public API.")

                    st.subheader("3. Retrieved Paper Metadata and Abstracts")

                    df = pd.DataFrame(papers)

                    st.dataframe(
                        df[["PMID", "Title", "Journal", "Year", "PubMed URL"]],
                        use_container_width=True
                    )

                    st.subheader("4. Candidate Target / Biomarker Term Classification")

                    candidate_df = summarize_candidate_terms(papers)

                    if candidate_df.empty:
                        st.warning(
                            """
                            No candidate terms were extracted by the current rule-based MVP method.
                            Future versions will use LLM-based extraction and biological databases.
                            """
                        )
                    else:
                        st.write(
                            """
                            The following terms were extracted from retrieved paper titles and abstracts.
                            DTSR then applies rule-based classification to estimate target category
                            and possible therapeutic modality.
                            """
                        )

                        st.dataframe(candidate_df, use_container_width=True)

                        st.caption(
                            """
                            Note: This classification is an early MVP heuristic.
                            Extracted terms are not validated drug targets.
                            Future versions will validate them using UniProt, Open Targets,
                            pathway databases, and normal tissue expression data.
                            """
                        )

                    st.subheader("5. Paper Details")

                    for index, paper in enumerate(papers, start=1):
                        with st.expander(f"{index}. {paper['Title']}"):
                            st.write(f"**PMID:** {paper['PMID']}")
                            st.write(f"**Journal:** {paper['Journal']}")
                            st.write(f"**Year:** {paper['Year']}")
                            st.write(f"**PubMed URL:** {paper['PubMed URL']}")

                            if paper["Abstract"]:
                                st.markdown("**Abstract:**")
                                st.write(paper["Abstract"])
                            else:
                                st.warning("No abstract available through PubMed API for this record.")

                    st.subheader("6. Next DTSR Development Step")

                    st.markdown(
                        """
                        The next development step is to validate extracted and classified candidate terms
                        using public biomedical databases.

                        Future versions will integrate:

                        - **Open Targets API** for disease-target association evidence
                        - **UniProt API** for protein function and cellular location
                        - **Europe PMC API** for open-access literature metadata
                        - **OpenAlex API** for scholarly metadata and citation information
                        - **Human Protein Atlas** for normal tissue expression and safety window
                        - **Reactome / KEGG** pathway databases for mechanism mapping
                        """
                    )

            except requests.exceptions.RequestException as error:
                st.error("PubMed API request failed.")
                st.write(error)

            except ET.ParseError:
                st.error("Failed to parse PubMed XML response.")

            except Exception as error:
                st.error("An unexpected error occurred.")
                st.write(error)

st.divider()

st.caption(
    "DTSR MVP v4: PubMed API search with rule-based candidate target classification and modality suggestion."
)
