#!/usr/bin/env python3
"""
Verify the search_tax_law fix and test all Custom GPT questions
"""

from core.enhanced_rag import EnhancedRAG
from openai import OpenAI
import os
import sys
from pathlib import Path

# Load environment
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def verify_fix():
    """Verify that the search_tax_law function is working"""
    print("\n" + "=" * 80)
    print("🔍 VERIFYING SEARCH_TAX_LAW FIX")
    print("=" * 80)

    rag = EnhancedRAG()

    # Try a simple search
    try:
        results = rag.basic_search("digital automated services", top_k=3)

        if results and len(results) > 0:
            print(f"\n✅ SUCCESS! Found {len(results)} results")
            print("\nSample result:")
            print(f"  Citation: {results[0].get('citation', 'N/A')}")
            print(f"  Similarity: {results[0].get('similarity', 0):.2f}")
            print(f"  Text preview: {results[0].get('chunk_text', '')[:150]}...")
            return True
        else:
            print("\n⚠️  Search succeeded but returned 0 results")
            return False

    except Exception as e:
        print(f"\n❌ FAILED! Error: {e}")
        return False


def answer_question(rag, question: str):
    """Answer a question using Enhanced RAG"""

    # Use Enhanced RAG to search
    results = rag.search_enhanced(question, top_k=5)

    if not results:
        return "❌ I couldn't find relevant information in the knowledge base."

    # Build context from results
    context = ""
    for i, doc in enumerate(results, 1):
        citation = doc.get("citation", "Unknown")
        text = doc.get("chunk_text", "")
        relevance = doc.get("relevance_score", doc.get("similarity", 0))

        context += f"\n[Source {i}: {citation} - Relevance: {relevance:.2f}]\n"
        context += text + "\n\n"

    # Generate answer
    system_prompt = """You are a helpful assistant that answers questions about Washington State tax law.  # noqa: E501

IMPORTANT INSTRUCTIONS:
1. Use ONLY the information provided in the context below
2. ALWAYS cite specific RCW/WAC references when making legal statements
3. Include DIRECT QUOTES from source documents using quotation marks
4. If context doesn't contain enough information, say so clearly
5. Be precise and thorough, maintaining legal accuracy"""

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": """Context from knowledge base:
{context}

Question: {question}

Please answer based on the context above.""",
        },
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
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
    print(f"\n📝 {question[:200]}{'...' if len(question) > 200 else ''}\n")
    print("-" * 100)

    answer = answer_question(rag, question)

    print(f"\n🤖 Answer:\n{answer}")
    print("\n" + "=" * 100)

    return answer


if __name__ == "__main__":
    print("\n" + "#" * 100)
    print("# COMPREHENSIVE TEST: VERIFY FIX + TEST ALL CUSTOM GPT QUESTIONS")
    print("#" * 100)

    # Step 1: Verify the fix
    if not verify_fix():
        print("\n❌ Fix verification failed! Stopping tests.")
        sys.exit(1)

    print("\n✅ Fix verified! Proceeding with question tests...\n")

    # Step 2: Initialize RAG
    rag = EnhancedRAG()

    # Step 3: All questions from screenshots + copy-pasted question
    questions = [
        # From screenshots
        'are there any determinations in which the department discusses the "data processing" exclusion and finds that while some element of data processing exists, the service should be viewed more holistically and treated as a taxable digital automated service',  # noqa: E501
        'can you explain what types of services are "hosting" and excluded from digital automated services and give me citations',  # noqa: E501
        "does the bundling rule apply to a professional service sold with a digital automated service",  # noqa: E501
        'if I purchase a "google maps" digital product (not clear if it is a digital file like a digital good or a digital automated service) how can I argue it is not subject to sales tax. Now the digital map will be incorporated into a telecommunications service I am selling.',  # noqa: E501
        'if a vendor sells a digital automated service in 2024 and then provides custom development with respect to that digital automated service is that considered "services provided exclusively in connection with a digital automated service" or does the fact that the development is not provided concurrently with the original sale of the digital automated service mean it is not service provided exclusively in connection with a digital automated service and therefore those services are not subject to sales tax',  # noqa: E501
        "We understand HB 2081 introduces a new 2.1% B&O rate for Service and Other Activities for businesses with annual gross income of $5 million or more, effective October 1, 2025. Could you please confirm if we need to start filing at this increased rate with our October 2025 return?",  # noqa: E501
        "is graphic design considered advertising services?",
        "What are the differences between the statutory definition of taxable IT services vs. the Department's interim guidance on taxable IT services?",  # noqa: E501
        "under the WACs or RCWs what authority exists to determine when sales tax has been collected?",  # noqa: E501
        "can anyone take a tax paid at source deduction or do they have to have a reseller permit. For example if a company pays sales tax on parts that it puts into a repair and then charges sales tax on the repair, can they take a deduction for the sales tax paid at source on their return?",  # noqa: E501
        "are sales to federally recognized tribes subject to sales tax?",
        "Does GAAP accounting drive recognition of gross income for B&O tax purposes?",
        "is the tangible property in direct mail advertising subject to sales or use tax in Washington?",  # noqa: E501
        # The long copy-pasted question about place of receipt
        'I am looking for analysis or discussion regarding "place of receipt" under RCW 82.32.730. The auditor is claiming that the vendor selling materials to ABC from the vendor\'s warehouse in Washington is essentially taking possession of the materials at its warehouse as an agent or designee for ABC. But this looks more like a drop ship in which ABC purchases the materials from the vendor and then the vendor ships the materials outside Washington to ABCs business partners. While ABC may be buying the materials from a vendor with a warehouse in Washington, ABC\'s position is that the sale is not in Washington because it never "receives" the materials. ABC does not believe vendor is its "agent" or designee under WAC 458-20-193 because vendor is the seller and does not do anything on ABCs behalf except pick, pack and ship the materials to ABC\'s partners outside Washington. Further, ABC has a contract with its partners outside Washington in which ABC promises to ship them materials. ABC thinks these partners are designees or agents under WAC 458-20-193 and NOT vendor. ABC is looking for legal support and analysis to source the purchase/sale of the materials outside Washington to where the are shipped and not to the vendor\'s warehouse. What do you think? can you help?',  # noqa: E501
    ]

    print(f"\n🎯 Testing {len(questions)} questions from Custom GPT conversations\n")

    results = []
    for i, question in enumerate(questions, 1):
        result = test_question(rag, question, i)
        results.append({"question": question, "answer": result})

        # Brief pause between questions
        import time

        time.sleep(1)

    print("\n" + "#" * 100)
    print("# TEST SUMMARY")
    print("#" * 100)
    print(f"\n✅ Tested {len(questions)} questions successfully!")
    print("\n📊 Questions that likely got good answers:")

    good_count = 0
    for i, r in enumerate(results, 1):
        if "❌ I couldn't find" not in r["answer"] and "Error" not in r["answer"]:
            good_count += 1
            print(f"  ✅ Question {i}")
        else:
            print(f"  ⚠️  Question {i} - may need knowledge base updates")

    print(f"\n📈 Success Rate: {good_count}/{len(questions)
                                            } ({100 * good_count / len(questions):.1f}%)")  # noqa: E501
    print("\n" + "#" * 100)
