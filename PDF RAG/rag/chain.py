"""LLM chains for all RAG features using Groq + LCEL."""
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
MODEL = "llama-3.3-70b-versatile"


def get_llm(temperature: float = 0.2):
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model_name=MODEL,
        temperature=temperature,
    )


def _docs_to_str(docs) -> str:
    return "\n\n".join(d.page_content for d in docs)


def answer_question(retriever, question: str) -> str:
    prompt = PromptTemplate.from_template(
        """You are a helpful assistant. Use the context below to answer the question accurately.
If the answer is not in the context, say "I don't have enough information in this document."

Context:
{context}

Question: {question}

Answer:"""
    )
    chain = (
        {"context": retriever | _docs_to_str, "question": RunnablePassthrough()}
        | prompt
        | get_llm()
        | StrOutputParser()
    )
    return chain.invoke(question)


def summarize(retriever, full_text: str) -> str:
    llm = get_llm(temperature=0.3)
    prompt = PromptTemplate.from_template(
        """Summarize the following document in clear, concise paragraphs.
Cover the main points, purpose, and conclusions.

Document:
{text}

Summary:"""
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"text": full_text[:12000]})


def extract_key_points(retriever, full_text: str) -> str:
    llm = get_llm(temperature=0.2)
    prompt = PromptTemplate.from_template(
        """Extract the most important key points from this document as a numbered list.
Be specific and include facts, figures, and conclusions.

Document:
{text}

Key Points:"""
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"text": full_text[:12000]})


def detect_topics(retriever, full_text: str) -> str:
    llm = get_llm(temperature=0.2)
    prompt = PromptTemplate.from_template(
        """Identify and list the main topics and themes covered in this document.
For each topic, write a brief one-sentence description.

Document:
{text}

Topics:"""
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"text": full_text[:12000]})


def generate_quiz(retriever, full_text: str, num_questions: int = 5) -> str:
    llm = get_llm(temperature=0.5)
    prompt = PromptTemplate.from_template(
        """Create {n} multiple-choice quiz questions based on this document.
Format each question as:
Q[n]: <question>
A) <option>
B) <option>
C) <option>
D) <option>
Answer: <letter>

Document:
{text}

Quiz:"""
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"text": full_text[:12000], "n": num_questions})


def generate_flashcards(retriever, full_text: str, num_cards: int = 8) -> str:
    llm = get_llm(temperature=0.4)
    prompt = PromptTemplate.from_template(
        """Create {n} flashcards from this document.
Format each as:
FRONT: <concept or question>
BACK: <definition or answer>
---

Document:
{text}

Flashcards:"""
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"text": full_text[:12000], "n": num_cards})
