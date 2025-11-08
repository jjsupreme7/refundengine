#!/usr/bin/env python3
"""
Quick test of the RAG chatbot
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from chat_rag import RAGChatbot

# Create chatbot
chatbot = RAGChatbot()

# Test a question
question = "how is computer software taxed in washington?"
print(f"\n❓ Testing question: {question}\n")
answer = chatbot.answer_question(question)
print(f"\n🤖 Answer:\n{answer}\n")
