from agent.retriever import retrieve_chunks
import json

chunks = retrieve_chunks("What was the role of La Venta for the Olmec culture?")
output = []
for i, c in enumerate(chunks):
    output.append(f"--- Chunk {i} ---")
    output.append(c["text"][:1000])

with open("chunk_debug.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print(f"Num chunks retrieved: {len(chunks)}")
