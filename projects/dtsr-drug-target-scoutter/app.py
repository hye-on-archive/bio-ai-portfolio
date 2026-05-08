import streamlit as st

# ------------------------------------------------------------
# DTSR: Drug Target ScoutteR
# First MVP UI prototype
#
# This app is designed to become a public API-based
# drug target scouting platform.
# ------------------------------------------------------------


# 페이지 기본 설정
# page_title: 브라우저 탭에 표시되는 이름
# page_icon: 브라우저 탭과 앱 상단에 표시되는 아이콘
# layout="wide": 화면을 넓게 사용
st.set_page_config(
    page_title="DTSR: Drug Target ScoutteR",
    page_icon="🧭",
    layout="wide"
)


# 앱 제목
st.title("🧭 DTSR: Drug Target ScoutteR")


# 앱 소개 문구
st.write(
    """
    **DTSR (Drug Target ScoutteR)** is a Bio-AI research platform concept
    designed to help users explore potential drug development targets
    based on disease mechanisms, literature evidence, and public biomedical data.
    """
)


# 공개 API 기반 분석 원칙 안내
st.info(
    """
    **Data Access Principle**

    DTSR analyzes publicly accessible biomedical information, including
    paper metadata, abstracts, open-access full text, and public biological databases
    available through public APIs.

    DTSR does not collect or analyze paywalled full-text papers without permission.
    """
)


st.divider()


# 사용자 입력 섹션
st.header("1. Disease-based Search")

# 사용자가 질환명을 입력하는 칸
# 입력된 질환명은 disease_name 변수에 저장됨
disease_name = st.text_input(
    "Enter a disease name:",
    placeholder="Example: Alzheimer's disease, rheumatoid arthritis, breast cancer"
)


# 검색할 논문 개수 선택
# 사용자가 5, 10, 20, 50 중 하나를 선택할 수 있음
max_results = st.selectbox(
    "Number of papers to retrieve:",
    options=[5, 10, 20, 50],
    index=1
)


# 검색 버튼
# 사용자가 버튼을 누르면 아래 코드가 실행됨
if st.button("Generate DTSR Search Strategy"):

    # 질환명이 비어 있으면 경고 메시지 출력
    if disease_name.strip() == "":
        st.warning("Please enter a disease name first.")

    # 질환명이 입력되어 있으면 검색 전략 생성
    else:
        st.subheader("2. Generated Search Strategy")

        # PubMed 검색에 사용할 기본 query 생성
        pubmed_query = f'("{disease_name}"[Title/Abstract]) AND (biomarker OR "drug target" OR protein OR pathway)'

        st.markdown("### PubMed Search Query")
        st.code(pubmed_query, language="text")

        st.write(
            """
            This query is designed to search for biomedical papers related to the
            disease name, biomarkers, drug targets, proteins, and pathways.
            """
        )

        st.markdown("### Planned Public API Sources")

        st.write(
            """
            In future versions, DTSR will retrieve and integrate data from:
            """
        )

        st.markdown(
            """
            - **PubMed API**: paper titles, abstracts, PMID, journal, publication year
            - **Europe PMC API**: open-access full text availability and metadata
            - **OpenAlex API**: citation count, open-access status, scholarly metadata
            - **Crossref API**: DOI, journal, publisher, license metadata
            - **UniProt API**: protein function, gene name, subcellular location
            - **Open Targets API**: disease-target association evidence
            - **Reactome / KEGG**: biological pathway information
            - **Human Protein Atlas**: normal tissue expression and safety window
            """
        )

        st.subheader("3. Planned DTSR Analysis Flow")

        st.markdown(
            """
            After retrieving public data, DTSR will analyze the disease and target candidates
            using the following framework:

            1. **Disease mechanism understanding**
            2. **Candidate biomarker / protein / target extraction**
            3. **Literature evidence organization**
            4. **Targetability evaluation**
            5. **Safety window assessment**
            6. **Modality matching**
               - ADC
               - CAR-T
               - Bispecific antibody
               - Monoclonal antibody
               - Small molecule inhibitor
               - PROTAC / TPD
               - RNA therapy
            7. **DTSR target score calculation**
            8. **Research report generation**
            """
        )

        st.subheader("4. Current MVP Status")

        st.success(
            f"""
            Search strategy generated for: **{disease_name}**

            Planned number of papers to retrieve: **{max_results}**

            Current version: Search strategy prototype  
            Next version: PubMed API connection
            """
        )


st.divider()


# 하단 설명
st.caption(
    "DTSR MVP v1: Search strategy UI prototype. PubMed API integration will be added in the next development step."
)
