# Semantic ingestion template v3
# See chat for rationale.

import os,re,requests,chromadb
from uuid import uuid4
from utils.logger import start_timer,end_timer,log_data

BASE_DIR=os.path.dirname(os.path.dirname(__file__))
PDF_FOLDER=os.path.join(BASE_DIR,"knowledge","rag_sources")
CHROMA_PATH=os.path.join(BASE_DIR,"chroma_db")
COLLECTION_NAME="massaciuccoli_knowledge"
OLLAMA_BASE_URL=os.getenv("OLLAMA_BASE_URL","http://ollama:11434")
OLLAMA_EMBED_URL=f"{OLLAMA_BASE_URL}/api/embeddings"
EMBED_MODEL="nomic-embed-text"
MAX_SECTION_SIZE=2500

def split_sections(text):
    p=re.compile(r'={10,}\s*\n([A-Z0-9 \-/()]+?)\s*\n={10,}',re.MULTILINE)
    m=list(p.finditer(text))
    if not m:return [{"title":"FULL_DOCUMENT","text":text.strip()}]
    out=[]
    for i,x in enumerate(m):
        s=x.end();e=m[i+1].start() if i+1<len(m) else len(text)
        b=text[s:e].strip()
        if b: out.append({"title":x.group(1).strip(),"text":b})
    return out

def split_large_section(sec):
    if len(sec["text"])<=MAX_SECTION_SIZE:return [sec]
    ss=re.split(r'(?<=[.!?])\s+',sec["text"]);out=[];cur="";i=1
    for s in ss:
        if len(cur)+len(s)<MAX_SECTION_SIZE: cur+=" "+s
        else:
            out.append({"title":f'{sec["title"]} ({i})',"text":cur.strip()})
            i+=1;cur=s
    if cur.strip(): out.append({"title":f'{sec["title"]} ({i})',"text":cur.strip()})
    return out

def get_embedding(t):
    r=requests.post(OLLAMA_EMBED_URL,json={"model":EMBED_MODEL,"prompt":t},timeout=30)
    r.raise_for_status();return r.json()["embedding"]

def ingest_pdfs(force=False):
    client=chromadb.PersistentClient(path=CHROMA_PATH)
    if force:
        try: client.delete_collection(COLLECTION_NAME)
        except: pass
    col=client.get_or_create_collection(COLLECTION_NAME)
    total=0
    for fn in sorted(os.listdir(PDF_FOLDER)):
        if not fn.endswith(".txt"): continue
        with open(os.path.join(PDF_FOLDER,fn),encoding="utf-8") as f: txt=f.read()
        chunks=[]
        for s in split_sections(txt): chunks.extend(split_large_section(s))
        log_data(f"chunks::{fn}",len(chunks))
        for c in chunks:
            emb=get_embedding(c["text"])
            col.add(ids=[str(uuid4())],embeddings=[emb],documents=[c["text"]],metadatas=[{"source":fn,"document":os.path.splitext(fn)[0],"section":c["title"]}])
            total+=1
    print(f"Knowledge Base rebuilt. Total chunks: {total}")



# ======================================================
# KB CHECK
# ======================================================

def is_kb_empty():

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = client.get_or_create_collection(
        COLLECTION_NAME
    )

    try:
        return collection.count() == 0
    except:
        return True


# ======================================================
# AUTO INIT
# ======================================================

def ensure_kb_ready():

    if is_kb_empty():

        print(
            "\n📚 Knowledge base empty → running ingestion...\n"
        )

        ingest_pdfs(force=True)

    else:

        print(
            "\n✅ Knowledge base already populated.\n"
        )
        
# ======================================================
# RUN
# ======================================================

if __name__=="__main__":
    ingest_pdfs(force=True)