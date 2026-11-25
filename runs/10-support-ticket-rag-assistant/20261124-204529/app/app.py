import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from src import db
from src import generator
from src.db import get_top_k_for_text

load_dotenv()

app = Flask(__name__)

@app.route('/suggest', methods=['POST'])
def suggest():
    data = request.get_json() or {}
    ticket_text = data.get('ticket_text')
    if not ticket_text:
        return jsonify({'error': 'ticket_text is required'}), 400

    # Retrieve top-5 similar docs
    results = get_top_k_for_text(ticket_text, embedder=None, k=5)
    contexts = []
    sources = []
    scores = []
    for r in results:
        contexts.append({'title': r.get('title'), 'content': r.get('content')})
        sources.append(r.get('metadata', {}))
        scores.append(r.get('score', 0))

    suggestion = generator.generate_suggestion(ticket_text, contexts)

    return jsonify({'suggested_resolution': suggestion, 'sources': sources, 'scores': scores})

if __name__ == '__main__':
    app.run(debug=True)
