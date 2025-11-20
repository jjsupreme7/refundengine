#!/usr/bin/env python3
"""
Test Enhanced RAG system against custom GPT questions
"""

from core.enhanced_rag import EnhancedRAG
from openai import OpenAI
import os
from pathlib import Path

# Load environment
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def answer_question_with_enhanced_rag(rag, question: str):
    """Answer a question using Enhanced RAG"""

    # Use Enhanced RAG to search
    results = rag.search_enhanced(question, top_k=3)

    if not results:
        return "❌ I couldn't find any relevant information in the knowledge base for that question."  # noqa: E501

    # Build context from results
    context = ""
    for i, doc in enumerate(results, 1):
        citation = doc.get("citation", "Unknown")
        text = doc.get("chunk_text", "")
        relevance = doc.get("relevance_score", doc.get("similarity", 0))

        context += f"\n[Source {i}: {citation} - Relevance: {relevance:.2f}]\n"
        context += text[:800] + "\n\n"

    # Generate answer
    system_prompt = """You are a helpful assistant that answers questions about Washington State tax law.  # noqa: E501

IMPORTANT INSTRUCTIONS:
1. Use ONLY the information provided in the context below to answer questions
2. ALWAYS cite specific RCW/WAC references when making legal statements
3. Include DIRECT QUOTES from the source documents using quotation marks
4. If the context doesn't contain enough information, say so
5. Be precise and thorough, maintaining legal accuracy"""

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": """Context from knowledge base:
{context}

Question: {question}

Please answer the question based on the context above.""",
        },
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.3,
            max_tokens=800,
        )

        answer = response.choices[0].message.content

        # Show sources
        sources_text = "\n\n📚 Sources Referenced:"
        for i, doc in enumerate(results, 1):
            citation = doc.get("citation", "N/A")
            relevance = doc.get("relevance_score", doc.get("similarity", 0))
            sources_text += f"\n  [{i}] {citation} (relevance: {relevance:.2f})"

        return answer + sources_text

    except Exception as e:
        return f"❌ Error generating answer: {e}"


def test_question(rag, question: str, question_num: int):
    """Test a single question"""
    print("\n" + "=" * 100)
    print(f"QUESTION {question_num}")
    print("=" * 100)
    print(f"\n📝 {question}\n")
    print("-" * 100)

    answer = answer_question_with_enhanced_rag(rag, question)

    print(f"\n🤖 Answer:\n{answer}")
    print("\n" + "=" * 100)

    return answer


if __name__ == "__main__":
    # Initialize Enhanced RAG
    rag = EnhancedRAG()

    # Subset of questions to test
    questions = [
        # Question 1: Hosting services
        'can you explain what types of services are "hosting" and excluded from digital automated services and give me citations',  # noqa: E501
        # Question 2: HB 2081 - The 2.1% B&O rate question!
        "We understand HB 2081 introduces a new 2.1% B&O rate for Service and Other Activities for businesses with annual gross income of $5 million or more, effective October 1, 2025. Could you please confirm if we need to start filing at this increased rate with our October 2025 return?",  # noqa: E501
        # Question 3: Tax paid at source
        "can anyone take a tax paid at source deduction or do they have to have a reseller permit. For example if a company pays sales tax on parts that it puts into a repair and then charges sales tax on the repair, can they take a deduction for the sales tax paid at source on their return?",  # noqa: E501
        # Question 4: Tribal sales
        "are sales to federally recognized tribes subject to sales tax?",
        # Question 5: Data processing exclusion
        'are there any determinations in which the department discusses the "data processing" exclusion and finds that while some element of data processing exists, the service should be viewed more holistically and treated as a taxable digital automated service',  # noqa: E501
    ]

    print("\n" + "#" * 100)
    print("# TESTING ENHANCED RAG WITH CUSTOM GPT QUESTIONS")
    print("#" * 100)

    results = []
    for i, question in enumerate(questions, 1):
        result = test_question(rag, question, i)
        results.append({"question": question, "answer": result})

        # Brief pause between questions
        import time

        time.sleep(2)

    print("\n" + "#" * 100)
    print("# TEST SUMMARY")
    print("#" * 100)
    print(f"\n✅ Tested {len(questions)} questions with Enhanced RAG")
    print("\nThe Enhanced RAG system should provide much better results!")
