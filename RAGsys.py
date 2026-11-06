import config
import requests
from tools import read_file
import os
import numpy as np
from dotenv import load_dotenv
load_dotenv()
apikeyE = os.getenv("EmbedAPI")
apikey = os.getenv("API")
model = os.getenv("MODEL")

import logging

logger = logging.getLogger(__name__)

testdata = [{"question":"Who first used the Latin form of the word psychology?","ans":"Marulić"},
            {"question":"Who is the earliest known English user of the word?","ans":"Blankaart"},
            {"question":"Who defined psychology in 1890 as the science of mental life?","ans":"William James"},
            {"question":"Which psychologist argued in 1913 for a purely objective, behaviorist view?","ans":"Watson"},
            {"question":"What condition does the Ebers Papyrus mention?","ans":"depression"},
            {"question":"Which Greek physician thought mental disorders had physical causes?","ans":"Hippocrates"},
            {"question":"Where did Aristotle think mental processes took place?","ans":"heart"},
            {"question":"Which Qing-era scholar proposed hemispheric lateralization?","ans":"Wang Qingren"},
            {"question":"Who wrote Psychologia Empirica in 1732?","ans":"Christian Wolff"},
            {"question":"Which philosopher rejected experimental psychology?","ans":"Kant"},
            {"question":"Who called himself Professor of Empirical Psychology in 1783?","ans":"Ueberwasser"},
            {"question":"When did Prussia make psychology a mandatory discipline?","ans":"1825"},
            {"question":"Negative test: Who founded the first psychology lab in Leipzig?","ans":" "},
            ]

def text_embed(query: str):
    respnse = requests.post(apikeyE,json={"model":"nomic-embed-text","prompt":query})

    reply = respnse.json()
    return reply["embedding"]

def chunk_text(text,chunk_size=300,overlap=25):
    words = text.split()
    chunks=[]
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+chunk_size])
        embedding = text_embed(chunk)
        chunkwithtext = {"text":chunk,"embedding":embedding}
        chunks.append(chunkwithtext)
        i += chunk_size - overlap
    return chunks

def find_similar_chunks(query, chunks,k):
        all_chunk = []
        for item in chunks:
             similarity = cosine_similarity(query,item["embedding"])
             chunk = {"info":item["text"],"similarity":similarity}
             all_chunk.append(chunk)
        all_chunk.sort(key=lambda x: x["similarity"],reverse= True)
        return all_chunk[:k]

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def document_search(qury: str,path):
    logger.info("RAG started")
    #messages = []
    embeded_query = text_embed(qury)
    try:
        text = read_file(path)
    except Exception as e:
         return f"ERROR: Couldnt read file for context {e}"
    doc = chunk_text(text)
    same_same = find_similar_chunks(embeded_query,doc)
    """context = ""
    for i,info in enumerate(same_same):
         context += str(i+1)+". "+info["info"] + ", "

    messages.append({"role":"system","content":context})
    messages.append({"role":"user","content":qury})"""
    #response = requests.post(apikey,json={"model": model,"messages": messages,"stream":False})
    #results = response.json()
    #return results["message"]["content"]
    #return context
    return same_same

def hit_rate(q_embeds,chunks,top_k):
     succsess = 0
     for qs in q_embeds:  
        same_same = find_similar_chunks(qs["question"],chunks,top_k)
        context = ""
        for i,info in enumerate(same_same):
            context += str(i+1)+". "+info["info"].lower() + ", "
        if qs["ans"].lower() in context:
           succsess += 1

     return f"{succsess}/{len(q_embeds)}"

def testing():
    path = r"D:\python\Psychology.docx"
    text = read_file(path)

    for i,item in enumerate(testdata):
          testdata[i]["question"] = text_embed(item["question"])
    n=0
    for chunk_size in [100, 150, 200, 300]:
        for overlap in [10,15,20,25]:
            chunks = chunk_text(text, chunk_size, overlap)   
            for top_n in [1, 2, 3]:
                rate = hit_rate(testdata, chunks, top_n)
                print(f"{n}|chunk_size: {chunk_size}|Overlap: {overlap}|top_n: {top_n}|rate: {rate}")
                n +=1
    return

def main():
    logger.info("started")
    testing()

if __name__ == "__main__":
     main()