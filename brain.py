from langchain_ollama.llms import OllamaLLM 
from langchain_core.prompts import ChatPromptTemplate
from vector_lazy import search

model = OllamaLLM(model="llama3.2")

template = """You are a helpful and concise AI assistant that provides clear, straightforward answers based on the available documents.

Context from relevant documents:
{context}

Question: {question}

Instructions:
1. Answer directly and naturally
2. Be concise but informative
3. Use bullet points for lists
4. If you can't answer from the context, say so clearly
5. No need to reference the documents in your answer

Answer:"""

prompt = ChatPromptTemplate.from_template(template)

def format_context(documents):
    """Format retrieved documents into a string"""
    return "\n\n".join(f"Document {i+1} (source: {doc.metadata.get('source','unknown')}):\n{doc.page_content}" for i, doc in enumerate(documents))

def debug_retrieval(documents):
    """Print brief metadata/snippet for each retrieved document for debugging."""
    for i, doc in enumerate(documents):
        src = doc.metadata.get('source', 'unknown')
        desc = doc.metadata.get('description', '')
        snippet = (doc.page_content[:300] + ('...' if len(doc.page_content) > 300 else ''))
        print(f"[{i+1}] source={src} desc={desc}\n    {snippet}\n")

def main():
    print("\n💡 Welcome to your Personal AI Assistant! Ask me anything about your documents.")
    print("Type 'q' to quit.\n")
    
    while True:
        question = input("\n🤔 Question: ")
        if question.lower() == "q":
            print("\nGoodbye! Have a great day! 👋\n")
            break

        # Retrieve relevant documents
        relevant_docs = search(question, k=6)
        context = format_context(relevant_docs)

        print("\n🤖 Answer:")
        chain = prompt | model
        result = chain.invoke({
            "context": context,
            "question": question
        })

        print("\nAnswer:")
        print(result)

if __name__ == "__main__":
    main()