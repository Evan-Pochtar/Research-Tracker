from flask import Flask, render_template, request, jsonify
import json
import os
import re

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data.json')

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return {"tasks": [], "papers": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def parse_citation(citation: str) -> dict:
    patterns = [
        re.compile(
            r'^(?P<authors>.+?)\.\s+'                     # authors
            r'(?P<title>.+?)\.\s+'                       # title
            r'(?P<journal>.+?)\s+'                        # journal (non-greedy)
            r'(?P<volume>\d+),\s*(?P<article_number>\d+)\s*'  # volume, article number
            r'\((?P<year>\d{4})\)\.?\s*'               # year
            r'(?P<doi>https?://\S+|doi:\S+)'              # DOI or URL
        ),
        re.compile(
            r'^(?P<authors>.+?)\.\s+["“](?P<title>.+?)["”]\.?\s*'
            r'(?P<journal>.+?)\s+vol\.?\s*(?P<volume>\d+)\s*,\s*(?P<issue>\d+)'  # journal up to vol
            r'\s*\((?P<year>\d{4})\)\s*:\s*(?P<pages>\d+(-\d+)?)\.\s*'
            r'(?:doi:)?(?P<doi>doi:\S+|https?://\S+)'     # DOI
        ),
        re.compile(
            r'^(?P<authors>.+?)\.\s+'                     # authors
            r'(?P<title>.+?)\.\s+'                       # title
            r'In:\s*(?P<book>[^.]+)\.\s*'               # book container
            r'(?P<doi>https?://\S+)'                      # DOI
        )
    ]

    for pat in patterns:
        m = pat.match(citation)
        if m:
            d = m.groupdict()
            return {
                'authors': d.get('authors', '').strip(),
                'title': d.get('title', '').strip(),
                'journal': d.get('journal', '').strip(),
                'publication': d.get('journal', '').strip(),
                'volume': d.get('volume', '').strip(),
                'issue': d.get('issue', '').strip(),
                'year': d.get('year', '').strip(),
                'pages': d.get('pages', '').strip(),
                'article_number': d.get('article_number', '').strip(),
                'doi': d.get('doi', '').strip(),
                'book': d.get('book', '').strip(),
            }

    # Fallbacks
    result = {k: '' for k in ['authors','title','journal','publication','volume','issue','year','pages','article_number','doi','book']}
    result['authors'] = citation.split('.',1)[0].strip()

    title_m = re.search(r'["“](.+?)["”]', citation)
    if title_m: result['title'] = title_m.group(1)

    journal_m = re.search(r'\.["”]\.?\s*(?P<journal>[^\d]+?)(?:vol\.?|\d{4})', citation)
    if journal_m: result['journal'] = journal_m.group('journal').strip().rstrip('.')

    year_m  = re.search(r'(\d{4})', citation)
    if year_m: result['year'] = year_m.group(1)

    doi_m   = re.search(r'(https?://\S+|doi:\S+)', citation)
    if doi_m: result['doi'] = doi_m.group(1)

    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/papers', methods=['GET'])
def get_papers():
    data = load_data()
    return jsonify({"papers": data.get("papers", [])})

@app.route('/api/papers', methods=['POST'])
def add_paper():
    data = load_data()
    new_paper = request.json
    
    if 'id' not in new_paper:
        max_id = 0
        for paper in data.get("papers", []):
            if paper.get('id', 0) > max_id:
                max_id = paper['id']
        new_paper['id'] = max_id + 1
    
    if "papers" not in data:
        data["papers"] = []
    
    data['papers'].append(new_paper)
    save_data(data)
    return jsonify(new_paper)

@app.route('/api/papers/<int:paper_id>', methods=['PUT'])
def update_paper(paper_id):
    data = load_data()
    updated_paper = request.json
    
    for i, paper in enumerate(data.get("papers", [])):
        if paper['id'] == paper_id:
            data['papers'][i] = updated_paper
            save_data(data)
            return jsonify(updated_paper)
    
    return jsonify({"error": "Paper not found"}), 404

@app.route('/api/papers/<int:paper_id>', methods=['DELETE'])
def delete_paper(paper_id):
    data = load_data()
    
    for i, paper in enumerate(data.get("papers", [])):
        if paper['id'] == paper_id:
            del data['papers'][i]
            save_data(data)
            return jsonify({"success": True})
    
    return jsonify({"error": "Paper not found"}), 404

@app.route('/api/parse_citation', methods=['POST'])
def api_parse_citation():
    data = request.get_json() or {}
    citation = data.get('citation', '')
    if not citation:
        return jsonify({'error':'No citation provided'}), 400
    parsed = parse_citation(citation)
    return jsonify(parsed)

app.run(debug=True, host='localhost', port=1717)
    