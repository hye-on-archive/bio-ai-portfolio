import re
from collections import Counter

import pandas as pd
import requests
import streamlit as st
import xml.etree.ElementTree as ET


# ------------------------------------------------------------
# DTSR: Drug Target ScoutteR
# PubMed API MVP version with candidate term extraction
#
# This app retrieves publicly accessible PubMed metadata and abstracts
# using NCBI E-utilities and extracts candidate biomarker / target terms
# using a simple rule-based MVP approach.
#
# Data principle:
# - Use public metadata and abstracts
# - Do not collect or analyze paywalled full-text papers
# ------------------------------------------------------------


# 페이지 기본 설정
st.set_page_config(
    page_title="DTSR: Drug Target ScoutteR",
    page_icon="🧭",
    layout="wide"
)


# PubMed E-utilities API 주소
# ESearch: 검색어를 넣으면 PMID 목록을 가져오는 API
# EFetch: PMID 목록을 넣으면 논문 상세정보를 가져오는 API
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


# 후보 용어 추출에서 제외할 일반 단어 목록
# 논문 초록에는 DNA, RNA처럼 의미 있는 용어도 있지만,
# 너무 일반적인 단어는 타깃 후보로 보기 어렵기 때문에 제외한다.
STOP_TERMS = {
    "DNA", "RNA", "mRNA", "miRNA", "PCR", "ELISA", "PBS",
    "USA", "UK", "CI", "HR", "OR", "RR", "SD", "SE",
    "AUC", "ROC", "OS", "PFS", "DFS",
    "COVID", "SARS", "HIV",
    "AND", "THE", "FOR", "WITH", "FROM"
}


# pathway 또는 병리기전 관련 키워드
# 이 목록은 후보 타깃 자체라기보다, 질환의 병리기전을 해석하는 데 도움을 주는 키워드다.
PATHWAY_KEYWORDS = [
    "PI3K", "AKT", "MAPK", "ERK", "JAK", "STAT",
    "NF-kB", "WNT", "NOTCH", "TGF-beta", "mTOR",
    "apoptosis", "autophagy", "inflammation", "fibrosis",
    "oxidative stress", "immune response", "DNA repair",
    "cell cycle", "angiogenesis", "metabolism"
]


def build_pubmed_query(disease_name: str) -> str:
    """
    사용자가 입력한 질환명을 PubMed 검색용 query로 바꾸는 함수.

    예:
    Alzheimer's disease 입력
    → ("Alzheimer's disease"[Title/Abstract]) AND (biomarker OR "drug target" OR protein OR pathway OR mechanism)
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

    PMID는 PubMed 논문의 고유 ID다.
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

    PubMed 초록은 여러 조각으로 나뉘어 있을 수 있어서,
    이 함수를 통해 안전하게 합쳐준다.
    """

    if element is None:
        return ""

    return " ".join(element.itertext()).strip()


def extract_article_info(article) -> dict:
    """
    PubMed XML에서 논문 제목, 저널, 연도, 초록, PMID를 추출하는 함수.
    """

    # PMID 추출
    pmid_element = article.find(".//PMID")
    pmid = pmid_element.text if pmid_element is not None else ""

    # 논문 제목 추출
    title_element = article.find(".//ArticleTitle")
    title = get_text_from_element(title_element)

    # 저널명 추출
    journal_element = article.find(".//Journal/Title")
    journal = get_text_from_element(journal_element)

    # 출판연도 추출
    year_element = article.find(".//JournalIssue/PubDate/Year")
    if year_element is not None:
        year = year_element.text
    else:
        medline_date_element = article.find(".//JournalIssue/PubDate/MedlineDate")
        year = medline_date_element.text if medline_date_element is not None else ""

    # 초록 추출
    abstract_elements = article.findall(".//Abstract/AbstractText")
    abstract_parts = [get_text_from_element(element) for element in abstract_elements]
    abstract = " ".join([part for part in abstract_parts if part]).strip()

    # PubMed 링크 생성
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

    추출 기준 예시:
    - TP53, EGFR, BRCA1 같은 대문자 유전자/단백질 패턴
    - IL-6, PD-L1, TNF-alpha 같은 하이픈 포함 바이오마커 패턴
    - PI3K/AKT, JAK/STAT 같은 pathway 관련 키워드
    """

    if not text:
        return []

    candidate_terms = []

    # 1. 대문자/숫자/하이픈 조합 패턴 추출
    # 예: TP53, BRCA1, EGFR, HER2, IL-6, PD-L1, JAK1
    uppercase_pattern = r"\b[A-Z][A-Z0-9-]{1,12}\b"
    uppercase_matches = re.findall(uppercase_pattern, text)

    for term in uppercase_matches:
        if term not in STOP_TERMS and len(term) >= 2:
            candidate_terms.append(term)

    # 2. TNF-alpha, TGF-beta처럼 그리스 문자 표현이 포함된 용어 추출
    greek_pattern = r"\b[A-Z]{2,6}-(?:alpha|beta|gamma|delta)\b"
    greek_matches = re.findall(greek_pattern, text, flags=re.IGNORECASE)

    for term in greek_matches:
        candidate_terms.append(term)

    # 3. pathway 키워드 추출
    lower_text = text.lower()

    for keyword in PATHWAY_KEYWORDS:
        if keyword.lower() in lower_text:
            candidate_terms.append(keyword)

    # 중복 제거는 하지 않고 그대로 반환한다.
    # 이유: 빈도 계산을 위해 반복 등장 횟수를 보존해야 하기 때문이다.
    return candidate_terms


def summarize_candidate_terms(papers: list) -> pd.DataFrame:
    """
    여러 논문에서 추출된 후보 용어의 등장 빈도를 계산하는 함수.
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
        rows.append(
            {
                "Candidate Term": term,
                "Frequency": count
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

                    st.subheader("4. Candidate Target / Biomarker Term Extraction")

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
                            The following terms were extracted from retrieved paper titles and abstracts
                            using a simple rule-based MVP method.
                            """
                        )

                        st.dataframe(candidate_df, use_container_width=True)

                        st.caption(
                            """
                            Note: This extraction is an early MVP heuristic.
                            The extracted terms are not final drug targets.
                            Future versions will validate them using Open Targets, UniProt,
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
                        The next development step is to validate extracted candidate terms
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
    "DTSR MVP v3: PubMed API search with rule-based candidate target / biomarker term extraction."
)
