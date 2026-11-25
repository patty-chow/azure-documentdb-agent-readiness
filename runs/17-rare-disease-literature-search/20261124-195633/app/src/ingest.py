import os
import time
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from dotenv import load_dotenv
# llama_index imports are optional at module import time; import in functions to reduce test-time fragility
from src.db import get_db
from pymongo import UpdateOne
import openai

load_dotenv()

OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
OPENAI_EMBEDDING_DIMS = int(os.getenv('OPENAI_EMBEDDING_DIMS', '1536'))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

# Simple PubMed fetch using E-utilities
ESEARCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
EFETCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'


def search_pubmed(query, retmax=100):
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': retmax,
        'retmode': 'xml'
    }
    r = requests.get(ESEARCH_URL, params=params)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    ids = [id_el.text for id_el in root.findall('.//IdList/Id')]
    return ids


def fetch_abstracts(pmids):
    docs = []
    batch = []
    for i in range(0, len(pmids), 100):
        chunk = pmids[i:i+100]
        params = {'db': 'pubmed', 'id': ','.join(chunk), 'retmode': 'xml'}
        r = requests.get(EFETCH_URL, params=params)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        for article in root.findall('.//PubmedArticle'):
            pmid_el = article.find('.//PMID')
            pmid = pmid_el.text if pmid_el is not None else None
            abstract_el = article.find('.//Abstract/AbstractText')
            abstract = ''.join(abstract_el.itertext()) if abstract_el is not None else ''
            year_el = article.find('.//PubDate/Year')
            if year_el is None:
                # fallback to MedlineDate or ArticleDate
                y = article.find('.//PubDate/MedlineDate')
                year = y.text if y is not None else None
            else:
                year = year_el.text
            title_el = article.find('.//ArticleTitle')
            title = ''.join(title_el.itertext()) if title_el is not None else ''
            docs.append({'pmid': pmid, 'title': title, 'abstract': abstract, 'year': year})
        time.sleep(0.35)  # be polite to NCBI
    return docs


def chunk_texts(docs, chunk_size=512, chunk_overlap=50):
    """
    Try to use LlamaIndex TokenTextSplitter if available; otherwise fall back to a simple whitespace splitter.
    """
    try:
        from llama_index.text_splitter import TokenTextSplitter
        splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        use_split = lambda text: splitter.split_text(text)
    except Exception:
        # fallback naive splitter
        def use_split(text):
            words = text.split()
            chunks = []
            i = 0
            while i < len(words):
                chunk = ' '.join(words[i:i+chunk_size])
                chunks.append(chunk)
                i += chunk_size - chunk_overlap
            return chunks

    all_chunks = []
    for d in docs:
        text = (d.get('title') or '') + '\n' + (d.get('abstract') or '')
        chunks = use_split(text)
        for i, c in enumerate(chunks):
            all_chunks.append({'pmid': d.get('pmid'), 'year': d.get('year'), 'chunk_id': f"{d.get('pmid')}_{i}", 'text': c})
    return all_chunks


def embed_texts(chunks, batch_size=16):
    embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [c['text'] for c in batch]
        resp = openai.Embedding.create(model=OPENAI_EMBEDDING_MODEL, input=texts)
        for j, item in enumerate(batch):
            emb = resp['data'][j]['embedding']
            item['embedding'] = emb
            item['model'] = OPENAI_EMBEDDING_MODEL
            item['schemaVersion'] = 1
            embeddings.append(item)
        time.sleep(0.1)
    return embeddings


def upsert_chunks(chunks):
    db = get_db()
    coll = db['pubmed_chunks']
    ops = []
    for c in chunks:
        key = {'_id': c['chunk_id']}
        doc = {**c}
        ops.append(UpdateOne(key, {'$set': doc}, upsert=True))
    if ops:
        res = coll.bulk_write(ops)
        return res.bulk_api_result
    return None


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', default='"rare disease" OR orphanet OR "rare genetic disease"')
    parser.add_argument('--count', type=int, default=50)
    args = parser.parse_args()

    pmids = search_pubmed(args.query, retmax=args.count)
    print(f'Found {len(pmids)} PMIDs')
    docs = fetch_abstracts(pmids)
    print(f'Fetched {len(docs)} articles')
    chunks = chunk_texts(docs)
    print(f'Created {len(chunks)} chunks')
    embedded = embed_texts(chunks)
    print(f'Embedded {len(embedded)} chunks')
    res = upsert_chunks(embedded)
    print('Upsert result:', res)
