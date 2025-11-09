from flask import Flask, render_template, request, jsonify
import brain

app = Flask(__name__, template_folder='templates', static_folder='static')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.get_json(force=True)
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'Question is required'}), 400

    # Retrieve relevant docs using your existing vector search
    try:
        relevant_docs = brain.search(question, k=6)
        context = brain.format_context(relevant_docs)

        chain = brain.prompt | brain.model
        result = chain.invoke({
            'context': context,
            'question': question
        })

        # Return the assistant answer as plain text
        return jsonify({'answer': str(result)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Pre-initialize vector store before starting the server
try:
    import vector_lazy
    print("Pre-initializing vector store...")
    vector_lazy.get_vectorstore()
    print("Vector store ready.")
except Exception as e:
    print(f"Error during vector store pre-initialization: {e}")

if __name__ == '__main__':
    # Run on localhost:5000
    app.run(host='127.0.0.1', port=5000, debug=True)
