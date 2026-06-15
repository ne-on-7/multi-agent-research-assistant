# Retrieval-Augmented Generation (RAG)

Retrieval-Augmented Generation (RAG) is a technique that combines a retrieval
system with a generative language model. Instead of relying only on the
knowledge baked into the model's weights, a RAG system first retrieves relevant
documents from an external knowledge source and then conditions the model's
generation on that retrieved context.

## How it works

1. **Retrieve:** the user query is embedded and used to search a vector store for
   the most semantically similar document chunks.
2. **Augment:** the retrieved chunks are inserted into the prompt as context.
3. **Generate:** the language model produces an answer grounded in that context,
   typically with citations back to the source documents.

## Why it is used

- **Reduces hallucination:** grounding answers in retrieved evidence makes the
  model far less likely to fabricate facts.
- **Keeps knowledge current:** the knowledge base can be updated without
  retraining the model.
- **Adds traceability:** because answers cite retrieved sources, users can verify
  claims against the original documents.

Common components of a RAG stack include an embedding model, a vector database
for similarity search, and a generator LLM that synthesizes the final answer.
