import config
import copy
import requests
from tools import read_file
import os
import numpy as np
from dotenv import load_dotenv
load_dotenv()
apikeyE = os.getenv("EmbedAPI")
apikey = os.getenv("API")
model = os.getenv("MODEL")
testdata = os.getenv("testdata")

import logging

logger = logging.getLogger(__name__)


def text_embed(query: str):
    respnse = requests.post(apikeyE,json={"model":"nomic-embed-text","prompt":query})

    reply = respnse.json()
    return reply["embedding"]

def chunk_text(text,chunk_size=150,overlap=15):
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

def find_similar_chunks(query, chunks,k:int=2):
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
    embeded_query = text_embed(qury)
    try:
        text = read_file(path)
    except Exception as e:
         return f"ERROR: Couldnt read file for context {e}"
    doc = chunk_text(text)
    same_same = find_similar_chunks(embeded_query,doc,2)
    
    return same_same

def hit_rate(q_embeds,chunks,top_k = None):
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
    path = r"#:\####\#####.docx"
    text = read_file(path)
    embededdata = copy.deepcopy(testdata)
    for i,item in enumerate(embededdata):
          embededdata[i]["question"] = text_embed(item["question"])
    """n=0
    for chunk_size in [100, 150, 200, 300]:
        for overlap in [10,15,20,25]:
            chunks = chunk_text(text, chunk_size, overlap)   
            for top_n in [1, 2, 3]:
                rate = hit_rate(testdata, chunks, top_n)
                print(f"{n}|chunk_size: {chunk_size}|Overlap: {overlap}|top_n: {top_n}|rate: {rate}")
                n +=1"""
    chunks = chunk_text(text)
    succsess = 0
    for j,question in enumerate(embededdata):
        messages = []
        same_same = find_similar_chunks(question["question"],chunks)
        context = ""
        for i,info in enumerate(same_same):
            context += str(i+1)+". "+info["info"].lower() + ", "

        messages.append({"role":"system","content":context})
        messages.append({"role":"system","content":"Instruction: Answer only if the correct answer is stated in the context, if not then say 'I dont know' "})
        messages.append({"role":"user","content":testdata[j]["question"]})
        response = requests.post(apikey,json={"model": model,"messages": messages,"stream":False})
        results = response.json()
        
        if testdata[j]["ans"] in results["message"]["content"]:
            succsess += 1
            print(f"{j}. Success")
        else: print(f"{j}. Failed - {results['message']['content']}")

    print(f"Success: {succsess}")
    return

def main():
    logger.info("started")
    testing()

if __name__ == "__main__":
     main()