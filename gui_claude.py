#!/usr/bin/env python3
"""
Narrative Pattern Analyzer - Web GUI

A Flask-based web interface for analyzing story patterns and tropes.

Usage:
------
python gui.py

Then open http://localhost:5000 in your browser.
"""

import json
import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

from models import Story, StoryCollection
from pattern_matcher import PatternMatcher, ArchetypeMatcher
from report_generator import ReportGenerator
from config import KNOWN_TROPES, CHARACTER_ARCHETYPES
from story_generator import STORY_TEMPLATES

app = Flask(__name__)
app.config['SECRET_KEY'] = 'narrative-analyzer-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Ensure folders exist
Path('uploads').mkdir(exist_ok=True)
Path('output').mkdir(exist_ok=True)
Path('data').mkdir(exist_ok=True)

# Global storage for current analysis
current_analysis = {
    'collection': None,
    'report_generator': None,
    'loaded_stories': []
}


def get_available_stories():
    """Get list of available story files."""
    stories = []
    
    # Check data folder
    data_path = Path('data')
    if data_path.exists():
        for f in data_path.glob('*.json'):
            stories.append({'name': f.stem, 'path': str(f), 'source': 'data'})
    
    # Check uploads folder
    uploads_path = Path('uploads')
    if uploads_path.exists():
        for f in uploads_path.glob('*.json'):
            stories.append({'name': f.stem, 'path': str(f), 'source': 'uploads'})
    
    return stories


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/templates')
def get_templates():
    """Get available story templates."""
    templates = []
    for key, template in STORY_TEMPLATES.items():
        templates.append({
            'id': key,
            'title': template['title'],
            'characters': len(template.get('characters', [])),
            'category': template.get('category', 'anime')
        })
    return jsonify(templates)


@app.route('/api/templates/<template_id>')
def get_template(template_id):
    """Get a specific template."""
    if template_id in STORY_TEMPLATES:
        return jsonify(STORY_TEMPLATES[template_id])
    return jsonify({'error': 'Template not found'}), 404


@app.route('/api/templates/<template_id>/save', methods=['POST'])
def save_template(template_id):
    """Save a template to the data folder."""
    if template_id not in STORY_TEMPLATES:
        return jsonify({'error': 'Template not found'}), 404
    
    story = STORY_TEMPLATES[template_id].copy()
    
    # Add story name to characters
    for char in story.get('characters', []):
        char['story'] = story['title']
    
    output_path = Path('data') / f"{template_id}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(story, f, indent=2, ensure_ascii=False)
    
    return jsonify({'success': True, 'path': str(output_path)})


@app.route('/api/stories')
def get_stories():
    """Get list of available story files."""
    return jsonify(get_available_stories())


@app.route('/api/stories/upload', methods=['POST'])
def upload_story():
    """Upload a story JSON file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith('.json'):
        filename = secure_filename(file.filename)
        filepath = Path('uploads') / filename
        file.save(filepath)
        
        # Validate JSON
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'title' not in data:
                os.remove(filepath)
                return jsonify({'error': 'Invalid story format - missing title'}), 400
        except json.JSONDecodeError:
            os.remove(filepath)
            return jsonify({'error': 'Invalid JSON file'}), 400
        
        return jsonify({'success': True, 'filename': filename})
    
    return jsonify({'error': 'Invalid file type - must be .json'}), 400


@app.route('/api/tropes')
def get_tropes():
    """Get all known tropes."""
    tropes = []
    for trope_id, trope in KNOWN_TROPES.items():
        tropes.append({
            'id': trope_id,
            'name': trope['name'],
            'description': trope['description'],
            'category': trope['category'],
            'required_traits': trope.get('required_traits', []),
            'examples': trope.get('examples', [])
        })
    return jsonify(tropes)


@app.route('/api/archetypes')
def get_archetypes():
    """Get character archetypes."""
    archetypes = []
    for arch_id, arch in CHARACTER_ARCHETYPES.items():
        archetypes.append({
            'id': arch_id,
            'name': arch['name'],
            'traits': arch['traits'],
            'backgrounds': arch.get('common_backgrounds', [])
        })
    return jsonify(archetypes)


@app.route('/api/analyze', methods=['POST'])
def analyze_stories():
    """Analyze selected stories."""
    data = request.get_json()
    story_paths = data.get('stories', [])
    
    if not story_paths:
        return jsonify({'error': 'No stories selected'}), 400
    
    # Load stories
    collection = StoryCollection(name="Analysis")
    loaded = []
    
    for path in story_paths:
        try:
            story = Story.load(path)
            collection.add_story(story)
            loaded.append(story.title)
        except Exception as e:
            return jsonify({'error': f'Error loading {path}: {str(e)}'}), 400
    
    # Run analysis
    try:
        generator = ReportGenerator(collection)
        
        # Store for later use
        current_analysis['collection'] = collection
        current_analysis['report_generator'] = generator
        current_analysis['loaded_stories'] = loaded
        
        # Get results
        stats = generator.get_summary_stats()
        
        # Format trope matches
        trope_matches = {}
        for trope_id, matches in generator.trope_matches.items():
            if matches:
                trope_matches[trope_id] = {
                    'name': KNOWN_TROPES[trope_id]['name'],
                    'category': KNOWN_TROPES[trope_id]['category'],
                    'matches': [m.to_dict() for m in matches[:10]]
                }
        
        # Format similarities
        similarities = [s.to_dict() for s in generator.similarities[:20]]
        
        # Format discovered patterns
        patterns = [p.to_dict() for p in generator.discovered_patterns[:15]]
        
        return jsonify({
            'success': True,
            'stats': stats,
            'trope_matches': trope_matches,
            'similarities': similarities,
            'discovered_patterns': patterns
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis error: {str(e)}'}), 500


@app.route('/api/analyze/character', methods=['POST'])
def analyze_character():
    """Analyze a specific character."""
    data = request.get_json()
    story_path = data.get('story')
    char_name = data.get('character')
    
    if not story_path or not char_name:
        return jsonify({'error': 'Story and character name required'}), 400
    
    try:
        story = Story.load(story_path)
        
        # Find character
        char = None
        for c in story.characters:
            if c.name.lower() == char_name.lower():
                char = c
                break
        
        if not char:
            return jsonify({'error': f'Character "{char_name}" not found'}), 404
        
        # Analyze
        matcher = PatternMatcher()
        arch_matcher = ArchetypeMatcher()
        
        # Get archetypes
        archetypes = arch_matcher.match_character_to_archetype(char)
        
        # Get tropes
        trope_matches = []
        for trope_id in KNOWN_TROPES:
            match = matcher.match_character_to_trope(char, trope_id)
            if match:
                trope_matches.append({
                    'trope': KNOWN_TROPES[trope_id]['name'],
                    'score': match.score,
                    'matched_traits': match.matched_traits
                })
        
        return jsonify({
            'character': char.to_dict(),
            'all_traits': char.get_all_traits(),
            'archetypes': [{'name': a[0], 'score': a[1]} for a in archetypes[:5]],
            'tropes': sorted(trope_matches, key=lambda x: -x['score'])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compare', methods=['POST'])
def compare_stories():
    """Compare two stories."""
    data = request.get_json()
    story1_path = data.get('story1')
    story2_path = data.get('story2')
    
    if not story1_path or not story2_path:
        return jsonify({'error': 'Two stories required'}), 400
    
    try:
        story1 = Story.load(story1_path)
        story2 = Story.load(story2_path)
        
        collection = StoryCollection(name="Comparison")
        collection.add_story(story1)
        collection.add_story(story2)
        
        matcher = PatternMatcher()
        trope_matches = matcher.find_all_trope_matches(collection)
        similarities = matcher.find_all_similar_pairs(collection, cross_story_only=True)
        
        # Find shared tropes
        shared_tropes = []
        for trope_id, matches in trope_matches.items():
            s1_matches = [m for m in matches if m.story == story1.title]
            s2_matches = [m for m in matches if m.story == story2.title]
            
            if s1_matches and s2_matches:
                shared_tropes.append({
                    'trope': KNOWN_TROPES[trope_id]['name'],
                    'story1_chars': [m.entity_name for m in s1_matches[:3]],
                    'story2_chars': [m.entity_name for m in s2_matches[:3]]
                })
        
        return jsonify({
            'story1': {'title': story1.title, 'characters': len(story1.characters)},
            'story2': {'title': story2.title, 'characters': len(story2.characters)},
            'shared_tropes': shared_tropes,
            'similar_characters': [s.to_dict() for s in similarities[:15]]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/<format>')
def export_report(format):
    """Export analysis report."""
    if not current_analysis['report_generator']:
        return jsonify({'error': 'No analysis to export. Run analysis first.'}), 400
    
    generator = current_analysis['report_generator']
    
    try:
        if format == 'json':
            output_path = Path('output') / 'analysis_report.json'
            generator.save_json_report(str(output_path))
            return send_file(output_path, as_attachment=True)
        
        elif format == 'html':
            output_path = Path('output') / 'analysis_report.html'
            generator.save_html_report(str(output_path))
            return send_file(output_path, as_attachment=True)
        
        elif format == 'txt':
            output_path = Path('output') / 'analysis_report.txt'
            generator.save_text_report(str(output_path))
            return send_file(output_path, as_attachment=True)
        
        else:
            return jsonify({'error': 'Invalid format'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Narrative Pattern Analyzer</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        :root {
            --bg-dark: #1a1a2e;
            --bg-card: #16213e;
            --bg-light: #0f3460;
            --accent: #e94560;
            --accent-light: #ff6b6b;
            --text: #eaeaea;
            --text-dim: #a0a0a0;
            --success: #00d26a;
            --warning: #ffc107;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
        }
        
        /* Header */
        header {
            background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-light) 100%);
            padding: 20px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 2px solid var(--accent);
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .logo-icon {
            font-size: 2.5em;
        }
        
        .logo h1 {
            font-size: 1.8em;
            background: linear-gradient(90deg, var(--accent), var(--accent-light));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .logo p {
            color: var(--text-dim);
            font-size: 0.9em;
        }
        
        /* Navigation */
        nav {
            display: flex;
            gap: 10px;
        }
        
        nav button {
            background: var(--bg-light);
            border: 1px solid var(--accent);
            color: var(--text);
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        nav button:hover, nav button.active {
            background: var(--accent);
        }
        
        /* Main Content */
        main {
            display: flex;
            height: calc(100vh - 90px);
        }
        
        /* Sidebar */
        .sidebar {
            width: 300px;
            background: var(--bg-card);
            padding: 20px;
            overflow-y: auto;
            border-right: 1px solid var(--bg-light);
        }
        
        .sidebar h3 {
            color: var(--accent);
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--bg-light);
        }
        
        .story-list {
            list-style: none;
        }
        
        .story-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px;
            margin-bottom: 8px;
            background: var(--bg-dark);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .story-item:hover {
            background: var(--bg-light);
        }
        
        .story-item.selected {
            border: 2px solid var(--accent);
        }
        
        .story-item input[type="checkbox"] {
            accent-color: var(--accent);
            width: 18px;
            height: 18px;
        }
        
        .story-item .story-info {
            flex: 1;
        }
        
        .story-item .story-name {
            font-weight: 600;
        }
        
        .story-item .story-meta {
            font-size: 0.8em;
            color: var(--text-dim);
        }
        
        /* Content Area */
        .content {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
        }
        
        /* Panels */
        .panel {
            display: none;
        }
        
        .panel.active {
            display: block;
        }
        
        /* Cards */
        .card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
        }
        
        .card h2 {
            color: var(--accent);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-box {
            background: linear-gradient(135deg, var(--bg-light) 0%, var(--bg-card) 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid var(--bg-light);
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: var(--accent);
        }
        
        .stat-label {
            color: var(--text-dim);
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        /* Buttons */
        .btn {
            background: var(--accent);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn:hover {
            background: var(--accent-light);
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            background: var(--text-dim);
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: var(--bg-light);
            border: 1px solid var(--accent);
        }
        
        .btn-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        /* Trope Cards */
        .trope-card {
            background: var(--bg-dark);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid var(--accent);
        }
        
        .trope-card h4 {
            color: var(--accent-light);
            margin-bottom: 10px;
        }
        
        .trope-card .category {
            display: inline-block;
            background: var(--bg-light);
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-bottom: 10px;
        }
        
        .match-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            background: var(--bg-card);
            border-radius: 6px;
            margin-top: 8px;
        }
        
        .match-score {
            background: var(--accent);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        .match-score.high { background: var(--success); }
        .match-score.medium { background: var(--warning); color: #333; }
        
        /* Similarity Pairs */
        .similarity-pair {
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 15px;
            background: var(--bg-dark);
            border-radius: 10px;
            margin-bottom: 10px;
        }
        
        .similarity-pair .character {
            flex: 1;
        }
        
        .similarity-pair .character-name {
            font-weight: bold;
            color: var(--accent-light);
        }
        
        .similarity-pair .story-name {
            font-size: 0.85em;
            color: var(--text-dim);
        }
        
        .similarity-pair .arrow {
            font-size: 1.5em;
            color: var(--accent);
        }
        
        .traits-list {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 8px;
        }
        
        .trait-tag {
            background: var(--bg-light);
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.8em;
        }
        
        /* Templates Grid */
        .templates-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .template-card {
            background: var(--bg-dark);
            border-radius: 10px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
        }
        
        .template-card:hover {
            border-color: var(--accent);
            transform: translateY(-3px);
        }
        
        .template-card h4 {
            color: var(--text);
            margin-bottom: 5px;
        }
        
        .template-card .meta {
            color: var(--text-dim);
            font-size: 0.85em;
        }
        
        /* Loading */
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        
        .loading.active {
            display: block;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid var(--bg-light);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Tropes Reference */
        .tropes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }
        
        .trope-ref-card {
            background: var(--bg-dark);
            border-radius: 10px;
            padding: 15px;
        }
        
        .trope-ref-card h4 {
            color: var(--accent-light);
            margin-bottom: 8px;
        }
        
        .trope-ref-card p {
            font-size: 0.9em;
            color: var(--text-dim);
            margin-bottom: 10px;
        }
        
        .trope-ref-card .examples {
            font-size: 0.85em;
            color: var(--text);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            main {
                flex-direction: column;
            }
            
            .sidebar {
                width: 100%;
                height: auto;
                max-height: 40vh;
            }
            
            header {
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }
            
            nav {
                flex-wrap: wrap;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">
            <span class="logo-icon">🎭</span>
            <div>
                <h1>Narrative Pattern Analyzer</h1>
                <p>Find story tropes and patterns across narratives</p>
            </div>
        </div>
        <nav>
            <button class="active" data-panel="analyze">📊 Analyze</button>
            <button data-panel="templates">📚 Templates</button>
            <button data-panel="tropes">🎯 Tropes</button>
            <button data-panel="compare">⚖️ Compare</button>
        </nav>
    </header>
    
    <main>
        <aside class="sidebar">
            <h3>📁 Available Stories</h3>
            <ul class="story-list" id="storyList">
                <li class="story-item" style="justify-content: center; color: var(--text-dim);">
                    Loading stories...
                </li>
            </ul>
            <button class="btn" style="width: 100%; margin-top: 15px;" onclick="refreshStories()">
                🔄 Refresh List
            </button>
        </aside>
        
        <div class="content">
            <!-- Analyze Panel -->
            <div class="panel active" id="panel-analyze">
                <div class="card">
                    <h2>📊 Analyze Stories</h2>
                    <p style="margin-bottom: 20px; color: var(--text-dim);">
                        Select stories from the sidebar, then click Analyze to find patterns and tropes.
                    </p>
                    <div class="btn-group">
                        <button class="btn" onclick="runAnalysis()">🔍 Analyze Selected</button>
                        <button class="btn btn-secondary" onclick="selectAllStories()">✓ Select All</button>
                        <button class="btn btn-secondary" onclick="deselectAllStories()">✗ Deselect All</button>
                    </div>
                </div>
                
                <div class="loading" id="analysisLoading">
                    <div class="spinner"></div>
                    <p>Analyzing stories...</p>
                </div>
                
                <div id="analysisResults"></div>
            </div>
            
            <!-- Templates Panel -->
            <div class="panel" id="panel-templates">
                <div class="card">
                    <h2>📚 Story Templates</h2>
                    <p style="margin-bottom: 20px; color: var(--text-dim);">
                        Pre-built story data for popular franchises. Click to add to your collection.
                    </p>
                    <div class="templates-grid" id="templatesGrid">
                        <!-- Filled by JS -->
                    </div>
                </div>
            </div>
            
            <!-- Tropes Panel -->
            <div class="panel" id="panel-tropes">
                <div class="card">
                    <h2>🎯 Known Tropes Reference</h2>
                    <p style="margin-bottom: 20px; color: var(--text-dim);">
                        These are the story patterns the analyzer looks for.
                    </p>
                    <div class="tropes-grid" id="tropesGrid">
                        <!-- Filled by JS -->
                    </div>
                </div>
            </div>
            
            <!-- Compare Panel -->
            <div class="panel" id="panel-compare">
                <div class="card">
                    <h2>⚖️ Compare Two Stories</h2>
                    <p style="margin-bottom: 20px; color: var(--text-dim);">
                        Select exactly two stories from the sidebar to compare them.
                    </p>
                    <button class="btn" onclick="compareStories()">🔄 Compare Selected</button>
                </div>
                
                <div id="compareResults"></div>
            </div>
        </div>
    </main>
    
    <script>
        // State
        let stories = [];
        let templates = [];
        let tropes = [];
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            loadStories();
            loadTemplates();
            loadTropes();
            setupNavigation();
        });
        
        // Navigation
        function setupNavigation() {
            document.querySelectorAll('nav button').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    
                    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
                    document.getElementById('panel-' + btn.dataset.panel).classList.add('active');
                });
            });
        }
        
        // Load stories
        async function loadStories() {
            try {
                const response = await fetch('/api/stories');
                stories = await response.json();
                renderStoryList();
            } catch (err) {
                console.error('Failed to load stories:', err);
            }
        }
        
        function renderStoryList() {
            const list = document.getElementById('storyList');
            
            if (stories.length === 0) {
                list.innerHTML = `
                    <li class="story-item" style="flex-direction: column; text-align: center;">
                        <p>No stories found</p>
                        <small style="color: var(--text-dim)">Add templates or upload JSON files</small>
                    </li>
                `;
                return;
            }
            
            list.innerHTML = stories.map((s, i) => `
                <li class="story-item" data-path="${s.path}">
                    <input type="checkbox" id="story-${i}">
                    <div class="story-info">
                        <div class="story-name">${s.name}</div>
                        <div class="story-meta">${s.source}</div>
                    </div>
                </li>
            `).join('');
        }
        
        function refreshStories() {
            loadStories();
        }
        
        function selectAllStories() {
            document.querySelectorAll('.story-item input[type="checkbox"]').forEach(cb => {
                cb.checked = true;
            });
        }
        
        function deselectAllStories() {
            document.querySelectorAll('.story-item input[type="checkbox"]').forEach(cb => {
                cb.checked = false;
            });
        }
        
        function getSelectedStories() {
            const selected = [];
            document.querySelectorAll('.story-item').forEach(item => {
                const cb = item.querySelector('input[type="checkbox"]');
                if (cb && cb.checked) {
                    selected.push(item.dataset.path);
                }
            });
            return selected;
        }
        
        // Load templates
        async function loadTemplates() {
            try {
                const response = await fetch('/api/templates');
                templates = await response.json();
                renderTemplates();
            } catch (err) {
                console.error('Failed to load templates:', err);
            }
        }
        
        function renderTemplates() {
            const grid = document.getElementById('templatesGrid');
            grid.innerHTML = templates.map(t => `
                <div class="template-card" onclick="addTemplate('${t.id}')">
                    <h4>${t.title}</h4>
                    <div class="meta">${t.characters} characters • ${t.category}</div>
                </div>
            `).join('');
        }
        
        async function addTemplate(templateId) {
            try {
                const response = await fetch(`/api/templates/${templateId}/save`, {
                    method: 'POST'
                });
                const result = await response.json();
                
                if (result.success) {
                    alert(`Added "${templateId}" to your stories!`);
                    loadStories();
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (err) {
                alert('Failed to add template');
            }
        }
        
        // Load tropes
        async function loadTropes() {
            try {
                const response = await fetch('/api/tropes');
                tropes = await response.json();
                renderTropes();
            } catch (err) {
                console.error('Failed to load tropes:', err);
            }
        }
        
        function renderTropes() {
            const grid = document.getElementById('tropesGrid');
            grid.innerHTML = tropes.map(t => `
                <div class="trope-ref-card">
                    <span class="category">${t.category}</span>
                    <h4>${t.name}</h4>
                    <p>${t.description}</p>
                    ${t.examples.length ? `<div class="examples">Examples: ${t.examples.join(', ')}</div>` : ''}
                </div>
            `).join('');
        }
        
        // Analysis
        async function runAnalysis() {
            const selected = getSelectedStories();
            
            if (selected.length === 0) {
                alert('Please select at least one story to analyze');
                return;
            }
            
            document.getElementById('analysisLoading').classList.add('active');
            document.getElementById('analysisResults').innerHTML = '';
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({stories: selected})
                });
                
                const result = await response.json();
                
                if (result.error) {
                    alert('Error: ' + result.error);
                    return;
                }
                
                renderAnalysisResults(result);
                
            } catch (err) {
                alert('Analysis failed: ' + err.message);
            } finally {
                document.getElementById('analysisLoading').classList.remove('active');
            }
        }
        
        function renderAnalysisResults(result) {
            const container = document.getElementById('analysisResults');
            
            // Stats
            let html = `
                <div class="card">
                    <h2>📈 Summary</h2>
                    <div class="stats-grid">
                        <div class="stat-box">
                            <div class="stat-number">${result.stats.total_stories}</div>
                            <div class="stat-label">Stories</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">${result.stats.total_characters}</div>
                            <div class="stat-label">Characters</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">${result.stats.tropes_found}</div>
                            <div class="stat-label">Tropes Found</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">${result.stats.similarity_pairs_found}</div>
                            <div class="stat-label">Similar Pairs</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">${result.stats.new_patterns_discovered}</div>
                            <div class="stat-label">New Patterns</div>
                        </div>
                    </div>
                    <div class="btn-group">
                        <button class="btn btn-secondary" onclick="exportReport('html')">📄 Export HTML</button>
                        <button class="btn btn-secondary" onclick="exportReport('json')">📊 Export JSON</button>
                        <button class="btn btn-secondary" onclick="exportReport('txt')">📝 Export Text</button>
                    </div>
                </div>
            `;
            
            // Trope Matches
            const tropeIds = Object.keys(result.trope_matches);
            if (tropeIds.length > 0) {
                html += `<div class="card"><h2>🎯 Trope Matches</h2>`;
                
                tropeIds.slice(0, 10).forEach(tropeId => {
                    const trope = result.trope_matches[tropeId];
                    html += `
                        <div class="trope-card">
                            <span class="category">${trope.category}</span>
                            <h4>${trope.name}</h4>
                            <div class="matches">
                                ${trope.matches.slice(0, 5).map(m => `
                                    <div class="match-item">
                                        <span class="match-score ${m.score >= 0.7 ? 'high' : m.score >= 0.5 ? 'medium' : ''}">${Math.round(m.score * 100)}%</span>
                                        <span><strong>${m.entity_name}</strong> (${m.story})</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                });
                
                html += `</div>`;
            }
            
            // Similar Characters
            if (result.similarities.length > 0) {
                html += `<div class="card"><h2>🔗 Similar Characters Across Stories</h2>`;
                
                result.similarities.slice(0, 10).forEach(sim => {
                    html += `
                        <div class="similarity-pair">
                            <div class="character">
                                <div class="character-name">${sim.entity1.name}</div>
                                <div class="story-name">${sim.entity1.story}</div>
                            </div>
                            <div class="arrow">↔</div>
                            <div class="character">
                                <div class="character-name">${sim.entity2.name}</div>
                                <div class="story-name">${sim.entity2.story}</div>
                            </div>
                            <span class="match-score ${sim.score >= 0.7 ? 'high' : sim.score >= 0.5 ? 'medium' : ''}">${Math.round(sim.score * 100)}%</span>
                        </div>
                        <div class="traits-list" style="margin-bottom: 15px;">
                            ${sim.shared_traits.slice(0, 6).map(t => `<span class="trait-tag">${t}</span>`).join('')}
                        </div>
                    `;
                });
                
                html += `</div>`;
            }
            
            // Discovered Patterns
            if (result.discovered_patterns.length > 0) {
                html += `<div class="card"><h2>✨ Discovered Patterns (New!)</h2>
                    <p style="color: var(--text-dim); margin-bottom: 20px;">
                        These patterns were found across multiple stories but aren't known tropes.
                    </p>`;
                
                result.discovered_patterns.slice(0, 8).forEach(pattern => {
                    html += `
                        <div class="trope-card">
                            <h4>★ ${pattern.pattern_name}</h4>
                            <p style="color: var(--text-dim); font-size: 0.9em; margin-bottom: 10px;">
                                Found in ${pattern.frequency} characters across ${Math.round(pattern.confidence * 100)}% of stories
                            </p>
                            <div class="traits-list">
                                ${pattern.shared_traits.map(t => `<span class="trait-tag">${t}</span>`).join('')}
                            </div>
                            <p style="margin-top: 10px; font-size: 0.9em;">
                                Examples: ${pattern.examples.slice(0, 4).map(e => `${e.name} (${e.story})`).join(', ')}
                            </p>
                        </div>
                    `;
                });
                
                html += `</div>`;
            }
            
            container.innerHTML = html;
        }
        
        async function exportReport(format) {
            window.location.href = `/api/export/${format}`;
        }
        
        // Compare
        async function compareStories() {
            const selected = getSelectedStories();
            
            if (selected.length !== 2) {
                alert('Please select exactly 2 stories to compare');
                return;
            }
            
            try {
                const response = await fetch('/api/compare', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({story1: selected[0], story2: selected[1]})
                });
                
                const result = await response.json();
                
                if (result.error) {
                    alert('Error: ' + result.error);
                    return;
                }
                
                renderCompareResults(result);
                
            } catch (err) {
                alert('Comparison failed: ' + err.message);
            }
        }
        
        function renderCompareResults(result) {
            const container = document.getElementById('compareResults');
            
            let html = `
                <div class="card">
                    <h2>${result.story1.title} vs ${result.story2.title}</h2>
                    <div class="stats-grid">
                        <div class="stat-box">
                            <div class="stat-number">${result.story1.characters}</div>
                            <div class="stat-label">${result.story1.title} Characters</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">${result.story2.characters}</div>
                            <div class="stat-label">${result.story2.title} Characters</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">${result.shared_tropes.length}</div>
                            <div class="stat-label">Shared Tropes</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">${result.similar_characters.length}</div>
                            <div class="stat-label">Similar Characters</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Shared tropes
            if (result.shared_tropes.length > 0) {
                html += `<div class="card"><h2>🎯 Shared Tropes</h2>`;
                
                result.shared_tropes.forEach(trope => {
                    html += `
                        <div class="trope-card">
                            <h4>${trope.trope}</h4>
                            <p><strong>${result.story1.title}:</strong> ${trope.story1_chars.join(', ')}</p>
                            <p><strong>${result.story2.title}:</strong> ${trope.story2_chars.join(', ')}</p>
                        </div>
                    `;
                });
                
                html += `</div>`;
            }
            
            // Similar characters
            if (result.similar_characters.length > 0) {
                html += `<div class="card"><h2>🔗 Similar Characters</h2>`;
                
                result.similar_characters.forEach(sim => {
                    html += `
                        <div class="similarity-pair">
                            <div class="character">
                                <div class="character-name">${sim.entity1.name}</div>
                                <div class="story-name">${sim.entity1.story}</div>
                            </div>
                            <div class="arrow">↔</div>
                            <div class="character">
                                <div class="character-name">${sim.entity2.name}</div>
                                <div class="story-name">${sim.entity2.story}</div>
                            </div>
                            <span class="match-score">${Math.round(sim.score * 100)}%</span>
                        </div>
                        <div class="traits-list" style="margin-bottom: 15px;">
                            ${sim.shared_traits.slice(0, 6).map(t => `<span class="trait-tag">${t}</span>`).join('')}
                        </div>
                    `;
                });
                
                html += `</div>`;
            }
            
            container.innerHTML = html;
        }
    </script>
</body>
</html>
'''

# Create templates folder and save the HTML template
@app.route('/templates/<path:filename>')
def serve_template(filename):
    return render_template(filename)


# Override render_template to use our inline template
from flask import Response

@app.route('/')
def index():
    return Response(HTML_TEMPLATE, mimetype='text/html')


if __name__ == '__main__':
    print("=" * 60)
    print("NARRATIVE PATTERN ANALYZER - Web GUI")
    print("=" * 60)
    print("\nStarting server...")
    print("Open http://localhost:5000 in your browser")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
