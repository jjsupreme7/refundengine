#!/usr/bin/env python3
"""
Test multiple questions from custom GPT against our RAG system
"""

import sys
from pathlib import Path

# Add chatbot to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).parent / ".env")

from chatbot.chat_rag import RAGChatbot  # noqa: E402


def test_question(chatbot, question: str, question_num: int):
    """Test a single question against our RAG system"""
    print("\n" + "=" * 100)
    print(f"QUESTION {question_num}")
    print("=" * 100)
    print(f"\n📝 {question}\n")
    print("-" * 100)

    answer = chatbot.answer_question(question)

    print(f"\n🤖 Answer:\n{answer}")
    print("\n" + "=" * 100)

    return answer


if __name__ == "__main__":
    chatbot = RAGChatbot()

    questions = [
        # Question 1: Data processing exclusion
        'are there any determinations in which the department discusses the "data processing" exclusion and finds that while some element of data processing exists, the service should be viewed more holistically and treated as a taxable digital automated service',  # noqa: E501
        # Question 2: Hosting services
        'can you explain what types of services are "hosting" and excluded from digital automated services and give me citations',  # noqa: E501
        # Question 3: Bundling rule
        "does the bundling rule apply to a professional service sold with a digital automated service",  # noqa: E501
        # Question 4: Google Maps
        'if I purchase a "google maps" digital product (not clear if it is a digital file like a digital good or a digital automated service) how can I argue it is not subject to sales tax. Now the digital map will be incorporated into a telecommunications service I am selling.',  # noqa: E501
        # Question 5: HB 2081 - The 2.1% B&O rate question!
        "We understand HB 2081 introduces a new 2.1% B&O rate for Service and Other Activities for businesses with annual gross income of $5 million or more, effective October 1, 2025. Could you please confirm if we need to start filing at this increased rate with our October 2025 return?",  # noqa: E501
        # Question 6: Graphic design
        "is graphic design considered advertising services?",
        # Question 7: IT services
        "What are the differences between the statutory definition of taxable IT services vs. the Department's interim guidance on taxable IT services?",  # noqa: E501
        # Question 8: Sales tax collection authority
        "under the WACs or RCWs what authority exists to determine when sales tax has been collected?",  # noqa: E501
        # Question 9: Tax paid at source
        "can anyone take a tax paid at source deduction or do they have to have a reseller permit. For example if a company pays sales tax on parts that it puts into a repair and then charges sales tax on the repair, can they take a deduction for the sales tax paid at source on their return?",  # noqa: E501
        # Question 10: Tribal sales
        "are sales to federally recognized tribes subject to sales tax?",
        # Question 11: GAAP accounting
        "Does GAAP accounting drive recognition of gross income for B&O tax purposes?",
        # Question 12: Direct mail
        "is the tangible property in direct mail advertising subject to sales or use tax in Washington?",  # noqa: E501
        # Question 13: Place of receipt analysis
        """I am looking for analysis or discussion regarding "place of receipt" under RCW 82.32.730. The auditor is claiming that the vendor selling materials to ABC from the vendor's warehouse in Washington is essentially taking possession of the materials at its warehouse as an agent or designee for ABC. But this looks more like a drop ship in which ABC purchases the materials from the vendor and then the vendor ships the materials outside Washington to ABCs business partners. While ABC may be buying the materials from a vendor with a warehouse in Washington, ABC's position is that the sale is not in Washington because it never "receives" the materials. ABC does not believe vendor is its "agent" or designee under WAC 458-20-193 because vendor is the seller and does not do anything on ABCs behalf except pick, pack and ship the materials to ABC's partners outside Washington. Further, ABC has a contract with its partners outside Washington in which ABC promises to ship them materials. ABC thinks these partners are designees or agents under WAC 458-20-193 and NOT vendor. ABC is looking for legal support and analysis to source the purchase/sale of the materials outside Washington to where the are shipped and not to the vendor's warehouse. What do you think? can you help?""",  # noqa: E501
    ]

    print("\n" + "#" * 100)
    print("# TESTING MULTIPLE QUESTIONS FROM CUSTOM GPT CONVERSATIONS")
    print("#" * 100)

    results = []
    for i, question in enumerate(questions, 1):
        result = test_question(chatbot, question, i)
        results.append({"question": question, "answer": result})

        # Brief pause between questions
        import time  # noqa: E402

        time.sleep(1)

    print("\n" + "#" * 100)
    print("# TEST SUMMARY")
    print("#" * 100)
    print(f"\n✅ Tested {len(questions)} questions")
    print("\nReview the answers above to see how our RAG system performed!")
