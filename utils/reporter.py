import json
import os
from pathlib import Path
from datetime import datetime

class HTMLReporter:
    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def _get_grade(self, score):
        if score >= 9: return "A+", "text-green-600 bg-green-50"
        if score >= 8: return "A", "text-green-500 bg-green-50"
        if score >= 6: return "B", "text-blue-500 bg-blue-50"
        if score >= 4: return "C", "text-yellow-600 bg-yellow-50"
        return "F", "text-red-600 bg-red-50"

    def generate_report(self, json_data, video_filename):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        score = json_data.get('ux_score', 0)
        grade, grade_color = self._get_grade(score)
        issues = json_data.get('issues', [])
        
        # Sort issues: High -> Medium -> Low
        priority_map = {"High": 0, "Medium": 1, "Low": 2}
        issues.sort(key=lambda x: priority_map.get(x.get('severity', 'Low'), 3))

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>VisionQA Audit Report</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Inter', sans-serif; background-color: #F3F4F6; }}
                .glass {{ background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }}
            </style>
        </head>
        <body class="p-8">
            <div class="max-w-4xl mx-auto space-y-6">
                
                <div class="glass rounded-2xl p-8 shadow-sm border border-gray-200 flex justify-between items-center">
                    <div>
                        <h1 class="text-3xl font-bold text-gray-900 tracking-tight">VisionQA <span class="text-indigo-600">Audit</span></h1>
                        <p class="text-gray-500 mt-2">Generated on {timestamp}</p>
                    </div>
                    <div class="text-right">
                        <div class="text-sm font-semibold text-gray-400 uppercase tracking-wider">UX Score</div>
                        <div class="text-6xl font-black {grade_color.split()[0]}">{score}<span class="text-3xl text-gray-300">/10</span></div>
                        <div class="inline-block px-3 py-1 rounded-full text-xs font-bold mt-2 {grade_color}">{grade} GRADE</div>
                    </div>
                </div>

                <div class="glass rounded-2xl p-8 shadow-sm border border-gray-200">
                    <h2 class="text-lg font-bold text-gray-900 mb-4 flex items-center">
                        <svg class="w-5 h-5 mr-2 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
                        Verification Artifact (Video)
                    </h2>
                    <div class="aspect-w-16 aspect-h-9 bg-gray-900 rounded-lg overflow-hidden">
                        <video controls class="w-full h-full object-contain">
                            <source src="{video_filename}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                </div>

                <div class="glass rounded-2xl p-8 shadow-sm border border-gray-200">
                    <h2 class="text-lg font-bold text-gray-900 mb-2">Executive Summary</h2>
                    <p class="text-gray-700 leading-relaxed text-lg">{json_data.get('description', 'No summary provided.')}</p>
                </div>

                <div class="space-y-4">
                    <h2 class="text-xl font-bold text-gray-900 ml-1">Detected Issues ({len(issues)})</h2>
                    
                    {''.join([self._render_issue(i) for i in issues])}
                    
                    { '<div class="p-8 text-center text-gray-500 italic">✨ Clean Bill of Health! No significant issues found.</div>' if not issues else '' }
                </div>

            </div>
        </body>
        </html>
        """
        
        # Save HTML file
        report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        report_path = self.output_dir / report_filename
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return report_path

    def _render_issue(self, issue):
        severity = issue.get('severity', 'Low')
        
        colors = {
            "High": "border-l-4 border-red-500 bg-white",
            "Medium": "border-l-4 border-yellow-500 bg-white",
            "Low": "border-l-4 border-blue-500 bg-white"
        }
        
        badge_colors = {
            "High": "bg-red-100 text-red-800",
            "Medium": "bg-yellow-100 text-yellow-800",
            "Low": "bg-blue-100 text-blue-800"
        }

        return f"""
        <div class="p-6 rounded-lg shadow-sm {colors.get(severity, 'bg-white')} transition hover:shadow-md">
            <div class="flex justify-between items-start">
                <div class="flex items-center space-x-3">
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-medium {badge_colors.get(severity)}">
                        {severity.upper()}
                    </span>
                    <span class="text-sm text-gray-400 font-mono">{issue.get('timestamp', '00:00')}</span>
                </div>
            </div>
            <h3 class="mt-2 text-lg font-bold text-gray-900">{issue.get('issue', 'Unknown Issue')}</h3>
            <p class="mt-1 text-gray-600">{issue.get('details', '')}</p>
        </div>
        """