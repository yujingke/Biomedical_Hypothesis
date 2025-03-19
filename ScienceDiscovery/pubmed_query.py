# pubmed_query.py
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def query_pubmed_by_mesh(mesh_term: str, start_date: str, end_date: str = None, retmax: int = 5):

    if end_date is None:
        end_date = datetime.now().strftime("%Y/%m/%d")

    query = f'{mesh_term}[MeSH Terms] AND ("{start_date}"[PDAT] : "{end_date}"[PDAT])'
    
    search_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    search_params = {
        'db': 'pubmed',
        'term': query,
        'retmax': retmax,
        'retmode': 'json'
    }
    api_key = os.getenv("PUBMED_API_KEY")
    if api_key:
        search_params['api_key'] = api_key
    
    response = requests.get(search_url, params=search_params)
    if response.status_code != 200:
        raise Exception(f"Retrieval error, status code: {response.status_code}")
    search_data = response.json()
    idlist = search_data.get('esearchresult', {}).get('idlist', [])
    if not idlist:
        return []
    

    efetch_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    efetch_params = {
        'db': 'pubmed',
        'id': ','.join(idlist),
        'retmode': 'xml'
    }
    if api_key:
        efetch_params['api_key'] = api_key
    
    efetch_response = requests.get(efetch_url, params=efetch_params)
    if efetch_response.status_code != 200:
        raise Exception(f"An error occurred when obtaining the article details, status code: {efetch_response.status_code}")
    
    root = ET.fromstring(efetch_response.content)
    articles = []
    for pubmed_article in root.findall('PubmedArticle'):
        medline = pubmed_article.find('MedlineCitation')
        article_elem = medline.find('Article')
        # title
        title_elem = article_elem.find('ArticleTitle')
        title = title_elem.text if title_elem is not None else "no title"
        # abstract
        abstract_elem = article_elem.find('Abstract')
        abstract_text = ""
        if abstract_elem is not None:
            texts = [elem.text for elem in abstract_elem.findall('AbstractText') if elem.text]
            abstract_text = " ".join(texts)
        # Just simply extract the year
        pub_date = "Unknown"
        journal = article_elem.find('Journal')
        if journal is not None:
            journal_issue = journal.find('JournalIssue')
            if journal_issue is not None:
                pub_date_elem = journal_issue.find('PubDate')
                if pub_date_elem is not None:
                    year_elem = pub_date_elem.find('Year')
                    medline_date_elem = pub_date_elem.find('MedlineDate')
                    if year_elem is not None:
                        pub_date = year_elem.text
                    elif medline_date_elem is not None:
                        pub_date = medline_date_elem.text
        # construct URL
        pmid_elem = medline.find('PMID')
        pmid = pmid_elem.text if pmid_elem is not None else "Unknown"
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        articles.append({
            'id': pmid,
            'title': title,
            'abstract': abstract_text,
            'pub_date': pub_date,
            'url': url
        })
    
    def parse_year(date_str):
        try:
            return int(date_str[:4])
        except:
            return 0
    articles_sorted = sorted(articles, key=lambda a: parse_year(a['pub_date']), reverse=True)
    return articles_sorted

def query_pubmed_by_keyword(keyword: str, start_date: str = None, end_date: str = None, retmax: int = 5):

    # If the time interval is specified, add time filtering conditions
    date_query = ""
    if start_date or end_date:
        if not start_date:
            start_date = "1800/01/01"  
        if not end_date:
            end_date = datetime.now().strftime("%Y/%m/%d")
        date_query = f' AND ("{start_date}"[PDAT] : "{end_date}"[PDAT])'
    
    # Directly use keywords to construct query
    query = f'{keyword}{date_query}'
    
    search_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    search_params = {
        'db': 'pubmed',
        'term': query,
        'retmax': retmax,
        'retmode': 'json'
    }
    api_key = os.getenv("PUBMED_API_KEY")
    if api_key:
        search_params['api_key'] = api_key
    
    response = requests.get(search_url, params=search_params)
    if response.status_code != 200:
        raise Exception(f"Retrieval error, status code: {response.status_code}")
    search_data = response.json()
    idlist = search_data.get('esearchresult', {}).get('idlist', [])
    if not idlist:
        return []
    
    # Get detailed information
    efetch_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    efetch_params = {
        'db': 'pubmed',
        'id': ','.join(idlist),
        'retmode': 'xml'
    }
    if api_key:
        efetch_params['api_key'] = api_key
    
    efetch_response = requests.get(efetch_url, params=efetch_params)
    if efetch_response.status_code != 200:
        raise Exception(f"An error occurred when obtaining the article details, status code: {efetch_response.status_code}")
    
    root = ET.fromstring(efetch_response.content)
    articles = []
    for pubmed_article in root.findall('PubmedArticle'):
        medline = pubmed_article.find('MedlineCitation')
        article_elem = medline.find('Article')
        title_elem = article_elem.find('ArticleTitle')
        title = title_elem.text if title_elem is not None else "no title"
        abstract_elem = article_elem.find('Abstract')
        abstract_text = ""
        if abstract_elem is not None:
            texts = [elem.text for elem in abstract_elem.findall('AbstractText') if elem.text]
            abstract_text = " ".join(texts)
        pub_date = "Unknown"
        journal = article_elem.find('Journal')
        if journal is not None:
            journal_issue = journal.find('JournalIssue')
            if journal_issue is not None:
                pub_date_elem = journal_issue.find('PubDate')
                if pub_date_elem is not None:
                    year_elem = pub_date_elem.find('Year')
                    medline_date_elem = pub_date_elem.find('MedlineDate')
                    if year_elem is not None:
                        pub_date = year_elem.text
                    elif medline_date_elem is not None:
                        pub_date = medline_date_elem.text
        pmid_elem = medline.find('PMID')
        pmid = pmid_elem.text if pmid_elem is not None else "Unknown"
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        articles.append({
            'id': pmid,
            'title': title,
            'abstract': abstract_text,
            'pub_date': pub_date,
            'url': url
        })
    
    def parse_year(date_str):
        try:
            return int(date_str[:4])
        except:
            return 0
    articles_sorted = sorted(articles, key=lambda a: parse_year(a['pub_date']), reverse=True)
    return articles_sorted


if __name__ == "__main__":
    keyword = "BRCA1"
    start = "2022/01/01"
    articles = query_pubmed_by_keyword(keyword, start)
    if articles:
        for art in articles:
            print(f"{art['pub_date']}: {art['title']}")
            print(f"Abstract: {art['abstract']}")
            print(f"URL: {art['url']}\n")
    else:
        print("No relevant literature was found.")
