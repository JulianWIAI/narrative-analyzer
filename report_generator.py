"""
Narrative Pattern Analyzer - Report Generator

Generates reports in various formats:
- Console output (text)
- JSON
- HTML
- PDF (requires reportlab)
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from models import Story, StoryCollection
from pattern_matcher import PatternMatcher, TropeMatch, SimilarityMatch, DiscoveredPattern
from config import KNOWN_TROPES


class ReportGenerator:
    """Generates analysis reports in various formats."""
    
    def __init__(self, collection: StoryCollection):
        self.collection = collection
        self.matcher = PatternMatcher()
        
        # Run analysis
        self.trope_matches = self.matcher.find_all_trope_matches(collection)
        self.similarities = self.matcher.find_all_similar_pairs(collection)
        self.discovered_patterns = self.matcher.discover_patterns(collection)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        total_characters = len(self.collection.get_all_characters())
        total_objects = len(self.collection.get_all_objects())
        total_arcs = len(self.collection.get_all_arcs())
        
        tropes_found = len([t for t in self.trope_matches if self.trope_matches[t]])
        total_trope_matches = sum(len(m) for m in self.trope_matches.values())
        
        return {
            "total_stories": len(self.collection.stories),
            "story_names": [s.title for s in self.collection.stories],
            "total_characters": total_characters,
            "total_objects": total_objects,
            "total_arcs": total_arcs,
            "tropes_found": tropes_found,
            "total_trope_matches": total_trope_matches,
            "similarity_pairs_found": len(self.similarities),
            "new_patterns_discovered": len(self.discovered_patterns),
        }
    
    def generate_text_report(self) -> str:
        """Generate a text report."""
        lines = []
        stats = self.get_summary_stats()
        
        # Header
        lines.append("=" * 70)
        lines.append("NARRATIVE PATTERN ANALYSIS REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 70)
        
        # Summary
        lines.append("\n## SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Stories Analyzed: {stats['total_stories']}")
        for name in stats['story_names']:
            lines.append(f"  - {name}")
        lines.append(f"Total Characters: {stats['total_characters']}")
        lines.append(f"Total Objects: {stats['total_objects']}")
        lines.append(f"Total Plot Arcs: {stats['total_arcs']}")
        lines.append(f"Known Tropes Found: {stats['tropes_found']}")
        lines.append(f"Cross-Story Similarities: {stats['similarity_pairs_found']}")
        lines.append(f"New Patterns Discovered: {stats['new_patterns_discovered']}")
        
        # Trope Matches
        lines.append("\n\n## TROPE MATCHES")
        lines.append("=" * 70)
        
        for trope_id, matches in sorted(self.trope_matches.items(), 
                                        key=lambda x: len(x[1]), reverse=True):
            if not matches:
                continue
            
            trope = KNOWN_TROPES.get(trope_id, {})
            lines.append(f"\n### {trope.get('name', trope_id)}")
            lines.append(f"    Category: {trope.get('category', 'unknown')}")
            lines.append(f"    Description: {trope.get('description', 'N/A')}")
            lines.append(f"    Matches Found: {len(matches)}")
            lines.append("")
            
            for match in matches[:10]:  # Top 10
                lines.append(f"    [{match.score:.0%}] {match.entity_name} ({match.story})")
                if match.matched_traits:
                    lines.append(f"          Matched: {', '.join(match.matched_traits[:5])}")
        
        # Cross-Story Similarities
        lines.append("\n\n## CROSS-STORY SIMILARITIES")
        lines.append("=" * 70)
        lines.append("\nCharacters from different stories that share traits/roles:\n")
        
        for sim in self.similarities[:20]:  # Top 20
            lines.append(f"  [{sim.score:.0%}] {sim.entity1_name} ({sim.entity1_story})")
            lines.append(f"         ↔ {sim.entity2_name} ({sim.entity2_story})")
            if sim.shared_traits:
                lines.append(f"         Shared: {', '.join(sim.shared_traits[:5])}")
            if sim.shared_tropes:
                lines.append(f"         Tropes: {', '.join(sim.shared_tropes)}")
            lines.append("")
        
        # Discovered Patterns
        lines.append("\n\n## DISCOVERED PATTERNS (NEW!)")
        lines.append("=" * 70)
        lines.append("\nPatterns found across multiple stories that aren't known tropes:\n")
        
        for pattern in self.discovered_patterns[:15]:
            lines.append(f"\n  ★ {pattern.pattern_name}")
            lines.append(f"    Frequency: {pattern.frequency} characters across {pattern.confidence:.0%} of stories")
            lines.append(f"    Traits: {', '.join(pattern.shared_traits)}")
            lines.append(f"    Examples:")
            for ex in pattern.examples[:5]:
                lines.append(f"      - {ex['name']} ({ex['story']})")
        
        # Per-Story Breakdown
        lines.append("\n\n## PER-STORY BREAKDOWN")
        lines.append("=" * 70)
        
        for story in self.collection.stories:
            lines.append(f"\n### {story.title}")
            lines.append("-" * 40)
            
            # Characters with tropes
            story_chars = [c for c in story.characters]
            chars_with_tropes = []
            
            for char in story_chars:
                char_tropes = []
                for trope_id, matches in self.trope_matches.items():
                    for match in matches:
                        if match.entity_name == char.name and match.story == story.title:
                            char_tropes.append((KNOWN_TROPES[trope_id]["name"], match.score))
                if char_tropes:
                    chars_with_tropes.append((char.name, char_tropes))
            
            if chars_with_tropes:
                lines.append("\n  Characters & Their Tropes:")
                for char_name, tropes in chars_with_tropes:
                    trope_str = ", ".join([f"{t[0]} ({t[1]:.0%})" for t in tropes[:3]])
                    lines.append(f"    {char_name}: {trope_str}")
            
            # Objects with tropes
            obj_tropes = []
            for obj in story.objects:
                for trope_id, matches in self.trope_matches.items():
                    for match in matches:
                        if match.entity_name == obj.name and match.story == story.title:
                            obj_tropes.append((obj.name, KNOWN_TROPES[trope_id]["name"], match.score))
            
            if obj_tropes:
                lines.append("\n  Objects & Their Tropes:")
                for obj_name, trope_name, score in obj_tropes:
                    lines.append(f"    {obj_name}: {trope_name} ({score:.0%})")
        
        lines.append("\n\n" + "=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def generate_json_report(self) -> Dict[str, Any]:
        """Generate a JSON report."""
        return {
            "generated": datetime.now().isoformat(),
            "summary": self.get_summary_stats(),
            "trope_matches": {
                trope_id: [m.to_dict() for m in matches]
                for trope_id, matches in self.trope_matches.items()
                if matches
            },
            "similarities": [s.to_dict() for s in self.similarities[:50]],
            "discovered_patterns": [p.to_dict() for p in self.discovered_patterns],
            "stories": [s.to_dict() for s in self.collection.stories]
        }
    
    def generate_html_report(self) -> str:
        """Generate an HTML report."""
        stats = self.get_summary_stats()
        
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Narrative Pattern Analysis Report</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #2980b9; margin-top: 30px; }
        h3 { color: #27ae60; }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number { font-size: 2em; font-weight: bold; }
        .stat-label { opacity: 0.9; }
        .trope-card {
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin: 15px 0;
        }
        .match-item {
            background: #ecf0f1;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
        }
        .score {
            display: inline-block;
            background: #27ae60;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.85em;
        }
        .score.medium { background: #f39c12; }
        .score.low { background: #e74c3c; }
        .similarity-pair {
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 15px;
            background: #fff;
            margin: 10px 0;
            border-radius: 8px;
            border: 1px solid #ddd;
        }
        .character-name { font-weight: bold; color: #2c3e50; }
        .story-name { color: #7f8c8d; font-size: 0.9em; }
        .arrow { font-size: 1.5em; color: #3498db; }
        .traits-list {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 5px;
        }
        .trait-tag {
            background: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
        }
        .pattern-card {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
        }
        .pattern-card h4 { margin-top: 0; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        tr:hover { background: #f5f5f5; }
    </style>
</head>
<body>
    <h1>🎭 Narrative Pattern Analysis Report</h1>
    <p><em>Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M') + """</em></p>
    
    <h2>📊 Summary</h2>
    <div class="stat-grid">
        <div class="stat-box">
            <div class="stat-number">""" + str(stats['total_stories']) + """</div>
            <div class="stat-label">Stories Analyzed</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">""" + str(stats['total_characters']) + """</div>
            <div class="stat-label">Characters</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">""" + str(stats['tropes_found']) + """</div>
            <div class="stat-label">Tropes Found</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">""" + str(stats['similarity_pairs_found']) + """</div>
            <div class="stat-label">Similar Pairs</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">""" + str(stats['new_patterns_discovered']) + """</div>
            <div class="stat-label">New Patterns</div>
        </div>
    </div>
    
    <div class="card">
        <h3>Stories Included:</h3>
        <ul>
"""
        for name in stats['story_names']:
            html += f"            <li>{name}</li>\n"
        
        html += """        </ul>
    </div>
    
    <h2>🎯 Trope Matches</h2>
"""
        
        for trope_id, matches in sorted(self.trope_matches.items(), 
                                        key=lambda x: len(x[1]), reverse=True):
            if not matches:
                continue
            
            trope = KNOWN_TROPES.get(trope_id, {})
            html += f"""
    <div class="card trope-card">
        <h3>{trope.get('name', trope_id)}</h3>
        <p><strong>Category:</strong> {trope.get('category', 'unknown')} | 
           <strong>Matches:</strong> {len(matches)}</p>
        <p>{trope.get('description', '')}</p>
"""
            for match in matches[:8]:
                score_class = "low" if match.score < 0.5 else ("medium" if match.score < 0.7 else "")
                html += f"""
        <div class="match-item">
            <span class="score {score_class}">{match.score:.0%}</span>
            <span class="character-name">{match.entity_name}</span>
            <span class="story-name">({match.story})</span>
            <div class="traits-list">
"""
                for trait in match.matched_traits[:5]:
                    html += f'                <span class="trait-tag">{trait}</span>\n'
                html += """            </div>
        </div>
"""
            html += "    </div>\n"
        
        # Similarities
        html += """
    <h2>🔗 Cross-Story Similarities</h2>
    <p>Characters from different stories that share significant traits:</p>
"""
        for sim in self.similarities[:15]:
            score_class = "low" if sim.score < 0.5 else ("medium" if sim.score < 0.7 else "")
            html += f"""
    <div class="similarity-pair">
        <div>
            <div class="character-name">{sim.entity1_name}</div>
            <div class="story-name">{sim.entity1_story}</div>
        </div>
        <div class="arrow">↔</div>
        <div>
            <div class="character-name">{sim.entity2_name}</div>
            <div class="story-name">{sim.entity2_story}</div>
        </div>
        <div>
            <span class="score {score_class}">{sim.score:.0%}</span>
            <div class="traits-list">
"""
            for trait in sim.shared_traits[:4]:
                html += f'                <span class="trait-tag">{trait}</span>\n'
            html += """            </div>
        </div>
    </div>
"""
        
        # Discovered Patterns
        html += """
    <h2>✨ Discovered Patterns</h2>
    <p>New patterns found that aren't known tropes:</p>
"""
        for pattern in self.discovered_patterns[:10]:
            html += f"""
    <div class="pattern-card">
        <h4>★ {pattern.pattern_name}</h4>
        <p>Found in {pattern.frequency} characters across {pattern.confidence:.0%} of stories</p>
        <p><strong>Traits:</strong> {', '.join(pattern.shared_traits)}</p>
        <p><strong>Examples:</strong></p>
        <ul>
"""
            for ex in pattern.examples[:5]:
                html += f"            <li>{ex['name']} ({ex['story']})</li>\n"
            html += """        </ul>
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html
    
    def save_text_report(self, filepath: str):
        """Save text report to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_text_report())
        print(f"Text report saved to: {filepath}")
    
    def save_json_report(self, filepath: str):
        """Save JSON report to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.generate_json_report(), f, indent=2, ensure_ascii=False)
        print(f"JSON report saved to: {filepath}")
    
    def save_html_report(self, filepath: str):
        """Save HTML report to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_html_report())
        print(f"HTML report saved to: {filepath}")
    
    def save_all_reports(self, output_dir: str):
        """Save all report formats."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        self.save_text_report(str(output_path / "narrative_analysis_report.txt"))
        self.save_json_report(str(output_path / "narrative_analysis_report.json"))
        self.save_html_report(str(output_path / "narrative_analysis_report.html"))
        
        print(f"\nAll reports saved to: {output_path.absolute()}")
