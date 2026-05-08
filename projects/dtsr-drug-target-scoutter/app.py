import requests
import pandas as pd
import streamlit as st
import xml.etree.ElementTree as ET


# ------------------------------------------------------------
# DTSR: Drug Target ScoutteR
# PubMed API MVP version
#
# This app retrieves publicly accessible PubMed metadata and abstracts
# using NCBI E-utilities.
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


def build_pubmed_query(disease_name: str) -> str:
    """
    사용자가 입력한 질환명을 PubMed 검색용 query로 바꾸는 함수.

    예:
    Alzheimer's disease 입력
    → ("Alzheimer's disease"[Title/Abstract]) AND (biomarker OR "drug target" OR protein OR pathway)
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

    PMID는 PubMed 논문의 고유 ID야.
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

                    # 표에서는 초록 전체가 너무 길기 때문에 일부 열만 먼저 보여준다.
                    st.dataframe(
                        df[["PMID", "Title", "Journal", "Year", "PubMed URL"]],
                        use_container_width=True
                    )

                    st.subheader("4. Paper Details")

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

                    st.subheader("5. Next DTSR Development Step")

                    st.markdown(
                        """
                        The next development step is to extract candidate biomarkers,
                        proteins, genes, and pathways from the retrieved abstracts.

                        Future versions will integrate additional public APIs such as:

                        - Open Targets API
                        - UniProt API
                        - Europe PMC API
                        - OpenAlex API
                        - Human Protein Atlas
                        - Reactome / KEGG pathway databases
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
    "DTSR MVP v2: PubMed API search prototype using publicly accessible metadata and abstracts."
)
