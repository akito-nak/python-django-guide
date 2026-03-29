"""
============================================================
12 - AI: NLP, LLMs, EMBEDDINGS & RAG
============================================================
This is where modern AI meets Python. Large Language Models
(LLMs) have transformed what's possible in software — and
Python is the language of this revolution.

We'll cover:
  - Text processing and NLP basics
  - OpenAI API and prompt engineering
  - Embeddings and semantic search
  - RAG (Retrieval-Augmented Generation)
  - LangChain for building AI pipelines
  - Building an AI-powered Django endpoint
  - Fine-tuning and evaluation

Install:
  pip install openai langchain chromadb sentence-transformers
  pip install transformers torch  (for local models)
============================================================
"""

import os
from typing import Any
from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────
# OPENAI API — the fastest path to LLM-powered features
# ─────────────────────────────────────────────────────────────

OPENAI_BASICS = """
# Install: pip install openai
# Set: OPENAI_API_KEY=sk-...

from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from environment

# Basic completion
response = client.chat.completions.create(
    model="gpt-4o-mini",  # or "gpt-4o", "gpt-4-turbo"
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",   "content": "What is the capital of France?"},
    ],
    temperature=0.7,   # 0 = deterministic, 2 = very random
    max_tokens=100,
)
print(response.choices[0].message.content)
print(f"Tokens used: {response.usage.total_tokens}")

# Streaming — for real-time responses (like ChatGPT)
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Count to 10 slowly."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)
"""


# ─────────────────────────────────────────────────────────────
# PROMPT ENGINEERING — the art of talking to LLMs
# ─────────────────────────────────────────────────────────────

class PromptTemplate:
    """A reusable, parameterized prompt."""

    def __init__(self, template: str, input_variables: list[str]) -> None:
        self.template = template
        self.input_variables = input_variables

    def format(self, **kwargs) -> str:
        missing = set(self.input_variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing variables: {missing}")
        return self.template.format(**kwargs)

    def __repr__(self) -> str:
        return f"PromptTemplate(variables={self.input_variables})"


# System prompt patterns that actually work
SYSTEM_PROMPTS = {
    "json_extractor": """
You are a precise data extraction assistant. 
Extract information from the provided text and return ONLY valid JSON.
Do not include any explanation or markdown — just the JSON object.
If a field cannot be found, use null.
""",

    "code_reviewer": """
You are an expert Python code reviewer. 
Analyze the provided code and return a structured review covering:
1. Correctness — bugs, edge cases
2. Performance — inefficiencies
3. Style — PEP 8 compliance, readability
4. Security — vulnerabilities
Be specific and actionable. Format your response as JSON.
""",

    "rag_answerer": """
You are a helpful assistant. Answer the user's question using ONLY the 
information provided in the context below. If the answer is not in the 
context, say "I don't have enough information to answer that."

Context:
{context}
""",

    "classifier": """
Classify the following text into exactly one of these categories: {categories}.
Return ONLY the category name, nothing else.
""",
}


class ChatSession:
    """Maintain conversation history for multi-turn conversations."""

    def __init__(self, system_prompt: str = "You are a helpful assistant.") -> None:
        self.messages: list[dict] = [
            {"role": "system", "content": system_prompt}
        ]

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def chat(self, user_message: str, **kwargs) -> str:
        """Send a message and get a response (simulated here)."""
        self.add_user_message(user_message)

        # In reality:
        # from openai import OpenAI
        # client = OpenAI()
        # response = client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=self.messages,
        #     **kwargs
        # )
        # reply = response.choices[0].message.content
        # self.add_assistant_message(reply)
        # return reply

        reply = f"[Response to: {user_message[:50]}...]"  # placeholder
        self.add_assistant_message(reply)
        return reply

    def reset(self, keep_system: bool = True) -> None:
        if keep_system:
            self.messages = [self.messages[0]]
        else:
            self.messages = []

    @property
    def turn_count(self) -> int:
        return len([m for m in self.messages if m["role"] == "user"])


# ─────────────────────────────────────────────────────────────
# STRUCTURED OUTPUT — make LLMs return typed data
# ─────────────────────────────────────────────────────────────

import json
from pydantic import BaseModel, Field

class ExtractedPerson(BaseModel):
    name: str
    age: int | None = None
    email: str | None = None
    company: str | None = None

class ExtractedPeople(BaseModel):
    people: list[ExtractedPerson]
    confidence: float = Field(ge=0.0, le=1.0)

STRUCTURED_OUTPUT_EXAMPLE = """
# OpenAI supports structured output natively (beta):
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Extract people information from text."},
        {"role": "user",   "content": "Alice Smith (30) works at Acme Corp, alice@acme.com"},
    ],
    response_format=ExtractedPeople,  # Pydantic model!
)
people = response.choices[0].message.parsed  # Already a Pydantic object!
print(people.people[0].name)   # "Alice Smith"
print(people.people[0].age)    # 30
"""


# ─────────────────────────────────────────────────────────────
# EMBEDDINGS — the math behind semantic search
# ─────────────────────────────────────────────────────────────
# An embedding is a list of numbers (a vector) that captures
# the MEANING of text. Similar meanings → similar vectors.
# This is what powers semantic search, recommendations, and RAG.

EMBEDDINGS_EXPLANATION = """
"cat" → [0.23, -0.45, 0.78, ...]  (1536 dimensions with text-embedding-3-small)
"dog" → [0.21, -0.43, 0.75, ...]  (similar! because cats and dogs are semantically related)
"SQL" → [0.89, 0.12, -0.33, ...]  (very different — programming vs animals)

Cosine similarity between "cat" and "dog": ~0.85 (high)
Cosine similarity between "cat" and "SQL": ~0.12 (low)

This is the foundation of semantic search — instead of matching keywords,
you match meanings.
"""

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    import math
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a ** 2 for a in vec1))
    mag2 = math.sqrt(sum(b ** 2 for b in vec2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)


class SemanticSearch:
    """Simple in-memory semantic search using embeddings."""

    def __init__(self, model_name: str = "text-embedding-3-small") -> None:
        self.model_name = model_name
        self.documents: list[str] = []
        self.embeddings: list[list[float]] = []

    def add_documents(self, documents: list[str]) -> None:
        """Embed and store documents."""
        for doc in documents:
            embedding = self._embed(doc)
            self.documents.append(doc)
            self.embeddings.append(embedding)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """Find the most semantically similar documents."""
        query_embedding = self._embed(query)
        similarities = [
            cosine_similarity(query_embedding, doc_emb)
            for doc_emb in self.embeddings
        ]
        # Sort by similarity, return top_k
        ranked = sorted(
            enumerate(similarities), key=lambda x: x[1], reverse=True
        )[:top_k]
        return [
            {"document": self.documents[i], "score": score, "rank": rank + 1}
            for rank, (i, score) in enumerate(ranked)
        ]

    def _embed(self, text: str) -> list[float]:
        """In reality, call the OpenAI embeddings API."""
        # from openai import OpenAI
        # client = OpenAI()
        # response = client.embeddings.create(input=text, model=self.model_name)
        # return response.data[0].embedding
        import random
        return [random.gauss(0, 1) for _ in range(8)]  # mock 8-dim vector


# ─────────────────────────────────────────────────────────────
# RAG — Retrieval-Augmented Generation
# ─────────────────────────────────────────────────────────────
# Problem: LLMs have a knowledge cutoff. Your data isn't in them.
# Solution: At query time, RETRIEVE relevant documents and
# INJECT them into the prompt. The LLM answers using YOUR data.
#
# Flow:
#   1. Index: embed all your documents → store in vector DB
#   2. Query: embed user question → find similar documents
#   3. Generate: inject documents into prompt → LLM generates answer

@dataclass
class Document:
    content: str
    metadata: dict = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Document(content={self.content[:50]!r}, metadata={self.metadata})"


class SimpleRAGSystem:
    """
    A minimal but complete RAG implementation.
    In production, use ChromaDB, Pinecone, Weaviate, or pgvector.
    """

    def __init__(self, llm_client=None) -> None:
        self.documents: list[Document] = []
        self.llm_client = llm_client

    def index_documents(self, texts: list[str], metadatas: list[dict] | None = None) -> None:
        """Step 1: Embed all documents and store them."""
        print(f"Indexing {len(texts)} documents...")
        for i, text in enumerate(texts):
            embedding = self._embed(text)
            doc = Document(
                content=text,
                metadata=(metadatas or [{}] * len(texts))[i],
                embedding=embedding,
            )
            self.documents.append(doc)
        print(f"Indexed {len(self.documents)} documents total")

    def retrieve(self, query: str, top_k: int = 3) -> list[Document]:
        """Step 2: Find the most relevant documents."""
        query_embedding = self._embed(query)
        scored = [
            (doc, cosine_similarity(query_embedding, doc.embedding))
            for doc in self.documents
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored[:top_k]]

    def generate(self, query: str, top_k: int = 3) -> dict:
        """Step 3: Retrieve + generate answer."""
        # Retrieve relevant documents
        relevant_docs = self.retrieve(query, top_k)

        # Build context from retrieved docs
        context = "\n\n---\n\n".join([
            f"Source: {doc.metadata.get('source', 'Unknown')}\n{doc.content}"
            for doc in relevant_docs
        ])

        # Build the prompt
        prompt = f"""Answer the question based only on the context provided.
If the answer is not in the context, say "I don't know based on the provided information."

Context:
{context}

Question: {query}

Answer:"""

        # Generate answer
        # In reality, call your LLM here:
        # response = self.llm_client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # answer = response.choices[0].message.content

        answer = f"[Answer to '{query}' based on {len(relevant_docs)} retrieved documents]"

        return {
            "query": query,
            "answer": answer,
            "sources": [
                {"content": doc.content[:100], "metadata": doc.metadata}
                for doc in relevant_docs
            ],
            "num_sources": len(relevant_docs),
        }

    def _embed(self, text: str) -> list[float]:
        """Mock embedding — replace with real API call."""
        import random, hashlib
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        return [random.gauss(0, 1) for _ in range(16)]


# ─────────────────────────────────────────────────────────────
# LANGCHAIN — building complex LLM pipelines
# ─────────────────────────────────────────────────────────────

LANGCHAIN_EXAMPLE = """
# pip install langchain langchain-openai langchain-community chromadb

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader, WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

# ── Load and split documents ──────────────────────────────────
loader = PyPDFLoader("your_document.pdf")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,        # characters per chunk
    chunk_overlap=200,      # overlap to avoid losing context at chunk boundaries
    separators=["\\n\\n", "\\n", " ", ""],
)
chunks = splitter.split_documents(documents)
print(f"Split into {len(chunks)} chunks")

# ── Create vector store ──────────────────────────────────────
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# ── Build RAG chain with LCEL (LangChain Expression Language) ──
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_template(
    "Answer the question using only the context.\\n\\n"
    "Context: {context}\\n\\n"
    "Question: {question}"
)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Use it:
answer = rag_chain.invoke("What are the main findings?")

# ── Conversational RAG — with memory ─────────────────────────
memory = ConversationBufferWindowMemory(
    k=5,                              # remember last 5 exchanges
    memory_key="chat_history",
    return_messages=True,
)

conv_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    return_source_documents=True,
)

result = conv_chain.invoke({"question": "What is the main topic?"})
print(result["answer"])
print(result["source_documents"])

# ── Tool-using agent ─────────────────────────────────────────
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.tools import tool

@tool
def search_web(query: str) -> str:
    "Search the web for current information."
    # implementation...
    return f"Results for: {query}"

@tool
def get_weather(city: str) -> str:
    "Get current weather for a city."
    return f"Weather in {city}: 72°F, sunny"

@tool
def calculate(expression: str) -> str:
    "Evaluate a mathematical expression."
    return str(eval(expression))  # ⚠️ sanitize in production!

tools = [search_web, get_weather, calculate]
agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
result = executor.invoke({"input": "What's the weather in NYC and what's 15% of 850?"})
"""

# ─────────────────────────────────────────────────────────────
# HUGGING FACE TRANSFORMERS — run models locally
# ─────────────────────────────────────────────────────────────

HUGGINGFACE_EXAMPLE = """
# pip install transformers torch  (or tensorflow)

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

# ── Sentiment analysis ────────────────────────────────────────
sentiment = pipeline("sentiment-analysis")
result = sentiment("I love Python and Django!")
print(result)  # [{'label': 'POSITIVE', 'score': 0.9998}]

# ── Text generation ───────────────────────────────────────────
generator = pipeline("text-generation", model="gpt2")
outputs = generator(
    "The future of AI is",
    max_new_tokens=100,
    num_return_sequences=2,
    temperature=0.8,
)
for output in outputs:
    print(output["generated_text"])

# ── Named Entity Recognition ──────────────────────────────────
ner = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english",
               aggregation_strategy="simple")
entities = ner("Apple Inc. was founded by Steve Jobs in Cupertino, California.")
for entity in entities:
    print(f"{entity['word']}: {entity['entity_group']} ({entity['score']:.4f})")

# ── Semantic similarity with sentence-transformers ────────────
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")  # fast, good quality
sentences = [
    "The cat sat on the mat",
    "A feline rested on a rug",   # similar
    "Machine learning is great",   # different
]
embeddings = model.encode(sentences)
similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
print(f"Similarity: {similarity:.4f}")  # ~0.85

# ── Zero-shot classification — no training needed! ────────────
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
result = classifier(
    "The new Python 3.12 release improves performance significantly.",
    candidate_labels=["technology", "sports", "politics", "entertainment"],
)
print(result["labels"][0], result["scores"][0])  # technology, 0.98
"""

# ─────────────────────────────────────────────────────────────
# DJANGO INTEGRATION — AI-powered API endpoint
# ─────────────────────────────────────────────────────────────

DJANGO_AI_ENDPOINT = """
# views.py — AI-powered endpoint with caching and rate limiting
import hashlib
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from openai import OpenAI

class AIRateThrottle(UserRateThrottle):
    rate = "20/day"   # each user gets 20 AI calls per day


class DocumentQAView(APIView):
    throttle_classes = [AIRateThrottle]

    def post(self, request):
        query = request.data.get("query", "").strip()
        document_ids = request.data.get("document_ids", [])

        if not query:
            return Response({"error": "Query is required"}, status=400)
        if len(query) > 500:
            return Response({"error": "Query too long (max 500 chars)"}, status=400)

        # Cache key based on query + documents
        cache_key = f"ai_qa_{hashlib.md5((query + str(sorted(document_ids))).encode()).hexdigest()}"
        cached = cache.get(cache_key)
        if cached:
            return Response({**cached, "cached": True})

        # Load documents from DB
        documents = Document.objects.filter(id__in=document_ids, user=request.user)
        if not documents:
            return Response({"error": "No documents found"}, status=404)

        # Build context
        context = "\\n\\n---\\n\\n".join([
            f"Document: {doc.title}\\n{doc.content[:2000]}"  # truncate long docs
            for doc in documents
        ])

        try:
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Answer using only this context:\\n\\n{context}"},
                    {"role": "user",   "content": query},
                ],
                max_tokens=500,
                temperature=0.1,  # low temp for factual Q&A
            )
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

        except Exception as e:
            import logging
            logging.error(f"OpenAI API error: {e}")
            return Response(
                {"error": "AI service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        result = {
            "query": query,
            "answer": answer,
            "tokens_used": tokens_used,
            "sources": [{"id": doc.id, "title": doc.title} for doc in documents],
            "cached": False,
        }

        # Cache for 1 hour
        cache.set(cache_key, result, timeout=3600)

        return Response(result)


class EmbeddingSearchView(APIView):
    \\\"\\\"\\\"Semantic search endpoint.\\\"\\\"\\\"

    def post(self, request):
        query = request.data.get("query", "").strip()
        top_k = min(int(request.data.get("top_k", 5)), 20)

        # Get query embedding
        client = OpenAI()
        response = client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding

        # Search vector database (using pgvector)
        # from pgvector.django import CosineDistance
        # results = DocumentChunk.objects.annotate(
        #     distance=CosineDistance("embedding", query_embedding)
        # ).order_by("distance")[:top_k]

        return Response({"results": [], "query": query})
"""

# ─────────────────────────────────────────────────────────────
# PROMPT ENGINEERING PATTERNS
# ─────────────────────────────────────────────────────────────

class PromptPatterns:
    """Battle-tested prompt engineering patterns."""

    @staticmethod
    def chain_of_thought(problem: str) -> str:
        """Make the LLM reason step by step — dramatically improves accuracy."""
        return f"""Solve the following problem step by step.
Show your reasoning for each step before giving the final answer.

Problem: {problem}

Step-by-step solution:"""

    @staticmethod
    def few_shot(examples: list[dict], query: str) -> str:
        """Provide examples to guide the output format."""
        example_str = "\n\n".join([
            f"Input: {ex['input']}\nOutput: {ex['output']}"
            for ex in examples
        ])
        return f"""Here are some examples:

{example_str}

Now do the same for:
Input: {query}
Output:"""

    @staticmethod
    def self_consistency(question: str, n: int = 3) -> str:
        """Generate multiple solutions and pick the most common answer."""
        return f"""Answer the following question {n} different ways,
then determine the most consistent answer.

Question: {question}

Solution 1:
[reason through it one way]

Solution 2:
[reason through it differently]

Solution 3:
[reason through it a third way]

Final answer (most consistent across solutions):"""

    @staticmethod
    def role_prompting(role: str, task: str) -> str:
        """Assign a persona to improve domain-specific responses."""
        return f"""You are {role}.

{task}"""

    @staticmethod
    def output_format(task: str, format_spec: str) -> str:
        """Specify exactly what format you want back."""
        return f"""{task}

Return your response in the following JSON format:
{format_spec}

Important: Return ONLY the JSON object. No explanation, no markdown, no extra text."""


# Demo
if __name__ == "__main__":
    # Test the RAG system
    rag = SimpleRAGSystem()
    rag.index_documents([
        "Python is a high-level programming language created by Guido van Rossum in 1991.",
        "Django is a high-level Python web framework that encourages rapid development.",
        "Machine learning is a subset of artificial intelligence.",
        "NumPy is the fundamental package for scientific computing with Python.",
        "PyTorch is an open-source machine learning framework developed by Meta.",
    ], metadatas=[
        {"source": "python_docs"},
        {"source": "django_docs"},
        {"source": "ml_intro"},
        {"source": "numpy_docs"},
        {"source": "pytorch_docs"},
    ])

    result = rag.generate("What is Django?")
    print("=== RAG Demo ===")
    print(f"Query: {result['query']}")
    print(f"Answer: {result['answer']}")
    print(f"Sources: {[s['metadata'] for s in result['sources']]}")

    # Prompt patterns
    print("\n=== Chain of Thought ===")
    print(PromptPatterns.chain_of_thought("If I have 3 boxes with 12 apples each, and I give away 15, how many remain?"))

    print("\n=== Few Shot ===")
    examples = [
        {"input": "The movie was amazing!", "output": "POSITIVE"},
        {"input": "I hated every minute.", "output": "NEGATIVE"},
    ]
    print(PromptPatterns.few_shot(examples, "It was okay, nothing special."))
