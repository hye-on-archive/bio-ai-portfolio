import re
from collections import Counter

import pandas as pd
import requests
import streamlit as st
import xml.etree.ElementTree as ET


# ------------------------------------------------------------
# DTSR: Drug Target ScoutteR
# MVP v7: PubMed API + UniProt validation
# + Open Targets entity search + association score prototype
#
# Data principle:
# - Use public metadata and abstracts
# - Use public biological databases
# - Do not collect or analyze paywalled full-text papers
# ------------------------------------------------------------


st.set_page_config(
    page_title="DTSR: Drug Target ScoutteR",
    page_icon="🧭",
    layout="wide"
)


PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"

OPEN_TARGETS_GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"


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
    disease_name = disease_name.strip()

    query = (
        f'("{disease_name}"[Title/Abstract]) '
        f'AND (biomarker OR "drug target" OR protein OR pathway OR mechanism)'
    )

    return query


def search_pubmed_ids(query: str, max_results: int) -> list:
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
    if element is None:
        return ""

    return " ".join(element.itertext()).strip()


def extract_article_info(article) -> dict:
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


def get_primary_gene_name(entry: dict) -> str:
    genes = entry.get("genes", [])

    if not genes:
        return ""

    first_gene = genes[0]
    gene_name = first_gene.get("geneName", {}).get("value", "")

    return gene_name


def get_recommended_protein_name(entry: dict) -> str:
    protein_description = entry.get("proteinDescription", {})

    recommended_name = protein_description.get("recommendedName", {})
    full_name = recommended_name.get("fullName", {})
    protein_name = full_name.get("value", "")

    if protein_name:
        return protein_name

    submission_names = protein_description.get("submissionNames", [])
    if submission_names:
        return submission_names[0].get("fullName", {}).get("value", "")

    return ""


def get_function_comment(entry: dict) -> str:
    comments = entry.get("comments", [])

    for comment in comments:
        if comment.get("commentType") == "FUNCTION":
            texts = comment.get("texts", [])
            if texts:
                return texts[0].get("value", "")

    return ""


def parse_uniprot_result(entry: dict) -> dict:
    accession = entry.get("primaryAccession", "")
    entry_name = entry.get("uniProtkbId", "")
    organism = entry.get("organism", {}).get("scientificName", "")

    gene_name = get_primary_gene_name(entry)
    protein_name = get_recommended_protein_name(entry)
    function = get_function_comment(entry)

    uniprot_url = f"https://www.uniprot.org/uniprotkb/{accession}/entry" if accession else ""

    return {
        "UniProt Accession": accession,
        "UniProt Entry": entry_name,
        "Gene Name": gene_name,
        "Protein Name": protein_name,
        "Organism": organism,
        "Function": function,
        "UniProt URL": uniprot_url
    }


def search_uniprot_candidate(term: str) -> dict:
    clean_term = term.strip()

    if not clean_term:
        return {}

    query = f'(gene_exact:{clean_term}) AND (organism_id:9606) AND (reviewed:true)'

    params = {
        "query": query,
        "format": "json",
        "size": 1
    }

    response = requests.get(UNIPROT_SEARCH_URL, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    if not results:
        fallback_query = f'({clean_term}) AND (organism_id:9606) AND (reviewed:true)'
        fallback_params = {
            "query": fallback_query,
            "format": "json",
            "size": 1
        }

        fallback_response = requests.get(UNIPROT_SEARCH_URL, params=fallback_params, timeout=20)
        fallback_response.raise_for_status()

        fallback_data = fallback_response.json()
        fallback_results = fallback_data.get("results", [])

        if not fallback_results:
            return {
                "UniProt Match": "No reviewed human match found",
                "UniProt Accession": "",
                "UniProt Entry": "",
                "Gene Name": "",
                "Protein Name": "",
                "Organism": "",
                "Function": "",
                "UniProt URL": ""
            }

        parsed = parse_uniprot_result(fallback_results[0])
    else:
        parsed = parse_uniprot_result(results[0])

    parsed["UniProt Match"] = "Reviewed human match found"

    return parsed


def query_open_targets(query: str, variables: dict) -> dict:
    response = requests.post(
        OPEN_TARGETS_GRAPHQL_URL,
        json={
            "query": query,
            "variables": variables
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise ValueError(data["errors"])

    return data.get("data", {})


def search_open_targets_entities(search_query: str, entity_names: list, size: int = 5) -> list:
    graphql_query = """
    query SearchEntities($queryString: String!, $entityNames: [String!], $page: Pagination) {
      search(queryString: $queryString, entityNames: $entityNames, page: $page) {
        hits {
          id
          name
          entity
          description
        }
      }
    }
    """

    variables = {
        "queryString": search_query,
        "entityNames": entity_names,
        "page": {
            "index": 0,
            "size": size
        }
    }

    data = query_open_targets(graphql_query, variables)
    hits = data.get("search", {}).get("hits", [])

    return hits


def open_targets_hits_to_dataframe(hits: list) -> pd.DataFrame:
    rows = []

    for hit in hits:
        rows.append(
            {
                "Open Targets ID": hit.get("id", ""),
                "Name": hit.get("name", ""),
                "Entity Type": hit.get("entity", ""),
                "Description": hit.get("description", "")
            }
        )

    return pd.DataFrame(rows)


def get_association_score_from_open_targets(target_id: str, disease_id: str) -> dict:
    """
    Open Targets GraphQL API에서 target-disease association score를 조회하는 함수.

    Open Targets association query는 targetId와 diseaseId를 사용한다.
    """

    if not target_id or not disease_id:
        return {
            "Association Score": "",
            "Association Status": "Missing target ID or disease ID"
        }

    graphql_query = """
    query AssociationScore($targetId: String!, $diseaseId: String!) {
      association(targetId: $targetId, diseaseId: $diseaseId) {
        score
        datatypeScores {
          id
          score
        }
      }
    }
    """

    variables = {
        "targetId": target_id,
        "diseaseId": disease_id
    }

    try:
        data = query_open_targets(graphql_query, variables)
        association = data.get("association")

        if not association:
            return {
                "Association Score": "",
                "Association Status": "No association found"
            }

        score = association.get("score", "")
        datatype_scores = association.get("datatypeScores", [])

        evidence_summary = []

        for item in datatype_scores:
            evidence_summary.append(
                f"{item.get('id', '')}: {item.get('score', '')}"
            )

        return {
            "Association Score": score,
            "Association Status": "Association found",
            "Evidence Type Scores": "; ".join(evidence_summary)
        }

    except Exception as error:
        return {
            "Association Score": "",
            "Association Status": f"Association query failed: {error}",
            "Evidence Type Scores": ""
        }


def summarize_candidate_terms(papers: list) -> pd.DataFrame:
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


def validate_candidates_with_uniprot(candidate_df: pd.DataFrame, max_candidates: int) -> pd.DataFrame:
    if candidate_df.empty:
        return candidate_df

    rows = []

    selected_candidates = candidate_df.head(max_candidates)

    for _, row in selected_candidates.iterrows():
        candidate_term = row["Candidate Term"]

        try:
            uniprot_info = search_uniprot_candidate(candidate_term)
        except requests.exceptions.RequestException:
            uniprot_info = {
                "UniProt Match": "UniProt request failed",
                "UniProt Accession": "",
                "UniProt Entry": "",
                "Gene Name": "",
                "Protein Name": "",
                "Organism": "",
                "Function": "",
                "UniProt URL": ""
            }

        merged_row = row.to_dict()
        merged_row.update(uniprot_info)
        rows.append(merged_row)

    return pd.DataFrame(rows)


def search_open_targets_for_validated_candidates(uniprot_df: pd.DataFrame, max_targets: int) -> pd.DataFrame:
    if uniprot_df.empty or "Gene Name" not in uniprot_df.columns:
        return pd.DataFrame()

    rows = []

    selected_df = uniprot_df.head(max_targets)

    for _, row in selected_df.iterrows():
        gene_name = row.get("Gene Name", "")
        candidate_term = row.get("Candidate Term", "")

        if not gene_name:
            rows.append(
                {
                    "Candidate Term": candidate_term,
                    "Gene Name": gene_name,
                    "Open Targets ID": "",
                    "Name": "",
                    "Entity Type": "",
                    "Description": "No UniProt gene name available for Open Targets search."
                }
            )
            continue

        try:
            hits = search_open_targets_entities(gene_name, ["target"], size=1)
        except Exception as error:
            rows.append(
                {
                    "Candidate Term": candidate_term,
                    "Gene Name": gene_name,
                    "Open Targets ID": "",
                    "Name": "",
                    "Entity Type": "",
                    "Description": f"Open Targets search failed: {error}"
                }
            )
            continue

        if not hits:
            rows.append(
                {
                    "Candidate Term": candidate_term,
                    "Gene Name": gene_name,
                    "Open Targets ID": "",
                    "Name": "",
                    "Entity Type": "",
                    "Description": "No Open Targets target entity found."
                }
            )
            continue

        top_hit = hits[0]

        rows.append(
            {
                "Candidate Term": candidate_term,
                "Gene Name": gene_name,
                "Open Targets ID": top_hit.get("id", ""),
                "Name": top_hit.get("name", ""),
                "Entity Type": top_hit.get("entity", ""),
                "Description": top_hit.get("description", "")
            }
        )

    return pd.DataFrame(rows)


def safe_get_first_disease_id(disease_ot_df: pd.DataFrame) -> str:
    if disease_ot_df.empty or "Open Targets ID" not in disease_ot_df.columns:
        return ""

    first_id = disease_ot_df.iloc[0].get("Open Targets ID", "")

    return first_id


def build_association_table(target_ot_df: pd.DataFrame, disease_id: str) -> pd.DataFrame:
    """
    Open Targets target entity 후보들과 disease ID를 이용해
    association score 표를 만드는 함수.
    """

    if target_ot_df.empty:
        return pd.DataFrame()

    rows = []

    for _, row in target_ot_df.iterrows():
        candidate_term = row.get("Candidate Term", "")
        gene_name = row.get("Gene Name", "")
        target_id = row.get("Open Targets ID", "")
        target_name = row.get("Name", "")

        association_info = get_association_score_from_open_targets(
            target_id=target_id,
            disease_id=disease_id
        )

        rows.append(
            {
                "Candidate Term": candidate_term,
                "Gene Name": gene_name,
                "Open Targets Target ID": target_id,
                "Open Targets Target Name": target_name,
                "Open Targets Disease ID": disease_id,
                "Association Score": association_info.get("Association Score", ""),
                "Association Status": association_info.get("Association Status", ""),
                "Evidence Type Scores": association_info.get("Evidence Type Scores", "")
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

    In this MVP version, DTSR retrieves **PubMed metadata and abstracts**, validates
    selected candidate terms using the **UniProt public API**, and searches disease-target
    evidence using the **Open Targets public GraphQL API**.

    DTSR does not collect or analyze paywalled full-text papers without permission.
    """
)

st.divider()

st.header("1. Disease-based PubMed Search")

disease_name = st.text_input(
    "Enter a disease name:",
    placeholder="Example: Alzheimer's disease, rheumatoid arthritis, breast cancer"
)

max_results = st.selectbox(
    "Number of PubMed papers to retrieve:",
    options=[5, 10, 20],
    index=0
)

max_uniprot_candidates = st.selectbox(
    "Number of extracted candidate terms to validate with UniProt:",
    options=[3, 5, 10],
    index=0
)

if st.button("Search PubMed and Validate Candidates with DTSR"):

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
                            """
                        )

                        st.subheader("5. UniProt Validation for Top Candidate Terms")

                        with st.spinner("Validating selected candidate terms using UniProt public API..."):
                            uniprot_df = validate_candidates_with_uniprot(
                                candidate_df,
                                max_uniprot_candidates
                            )

                        st.dataframe(uniprot_df, use_container_width=True)

                        st.caption(
                            """
                            UniProt validation checks whether selected candidate terms can be matched
                            to reviewed human protein entries. This is still an early validation step
                            and should not be interpreted as final target validation.
                            """
                        )

                        st.subheader("6. Open Targets Entity Search")

                        with st.spinner("Searching Open Targets disease entity..."):
                            try:
                                disease_hits = search_open_targets_entities(
                                    disease_name,
                                    ["disease", "phenotype"],
                                    size=5
                                )
                                disease_ot_df = open_targets_hits_to_dataframe(disease_hits)
                            except Exception as error:
                                disease_ot_df = pd.DataFrame(
                                    [
                                        {
                                            "Open Targets ID": "",
                                            "Name": "",
                                            "Entity Type": "",
                                            "Description": f"Open Targets disease search failed: {error}"
                                        }
                                    ]
                                )

                        st.markdown("### Disease Entity Candidates")
                        st.dataframe(disease_ot_df, use_container_width=True)

                        with st.spinner("Searching Open Targets target entities for UniProt-validated candidates..."):
                            target_ot_df = search_open_targets_for_validated_candidates(
                                uniprot_df,
                                max_uniprot_candidates
                            )

                        st.markdown("### Target Entity Candidates")
                        st.dataframe(target_ot_df, use_container_width=True)

                                            st.subheader("7. Open Targets Association Score Prototype")

                        disease_options = create_disease_selection_options(disease_ot_df)

                        if not disease_options:
                            st.warning(
                                """
                                No valid Open Targets disease entity candidates were found.
                                Association score retrieval cannot be performed.
                                """
                            )
                        else:
                            selected_disease_option = st.selectbox(
                                "Select the correct Open Targets disease entity for association scoring:",
                                options=disease_options
                            )

                            selected_disease_id = extract_disease_id_from_option(selected_disease_option)

                            st.write(f"Selected Open Targets Disease ID: `{selected_disease_id}`")

                            if not selected_disease_id:
                                st.warning(
                                    """
                                    No valid disease ID was selected.
                                    Association score retrieval cannot be performed.
                                    """
                                )
                            else:
                                with st.spinner("Retrieving Open Targets association scores using selected disease entity..."):
                                    association_df = build_association_table(
                                        target_ot_df,
                                        selected_disease_id
                                    )

                                if association_df.empty:
                                    st.warning("No association score table could be generated.")
                                else:
                                    st.dataframe(association_df, use_container_width=True)

                                    st.caption(
                                        """
                                        Association scores are retrieved from Open Targets using the user-selected
                                        disease entity and target entity candidates. This improves reliability compared
                                        with automatically selecting the first disease candidate.
                                        """
                                    )

                 
                    st.subheader("8. Paper Details")

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

                    st.subheader("9. Next DTSR Development Step")

                    st.markdown(
                        """
                        The next development step is to improve disease and target entity selection
                        and integrate association evidence into the DTSR scoring framework.

                        Future versions will integrate:

                        - **Refined Open Targets association evidence**
                        - **Human Protein Atlas** for normal tissue expression and safety window
                        - **Reactome / KEGG** pathway databases for mechanism mapping
                        - **Europe PMC API** for open-access literature metadata
                        - **OpenAlex API** for scholarly metadata and citation information
                        """
                    )

            except requests.exceptions.RequestException as error:
                st.error("Public API request failed.")
                st.write(error)

            except ET.ParseError:
                st.error("Failed to parse PubMed XML response.")

            except Exception as error:
                st.error("An unexpected error occurred.")
                st.write(error)

st.divider()

st.caption(
    "DTSR MVP v8: PubMed API + UniProt validation + user-selected Open Targets disease association scoring."
)
