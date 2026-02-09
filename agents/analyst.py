"""
VisionQA Analyst Agent
Working version with correct Gemini model names (January 2026)
"""

import os
import time
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# --- CORRECT MODEL NAMES (as of January 2026) ---
MODEL_FALLBACK_CHAIN = [
    "gemini-1.5-flash",          # Best for JSON structure & strict instructions
    "gemini-2.0-flash",          # Good backup
    "gemini-3-flash-preview",     # Fast but sometimes ignores complex instructions
]

class GeminiAnalyst:
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("❌ GEMINI_API_KEY not found in .env file")
        
        # Set a long timeout to prevent "503 Overloaded" on client side
        self.client = genai.Client(
            api_key=self.api_key,
            http_options={'timeout': 600000}  # 10 minutes
        )
    
    def upload_video(self, video_path):
        video_path = Path(video_path)
        print(f"📤 Uploading: {video_path.name}...")
        
        uploaded_file = self.client.files.upload(file=str(video_path))
        
        while uploaded_file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(2)
            uploaded_file = self.client.files.get(name=uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise Exception("❌ Video processing failed.")

        print(f"\n✅ Video Active: {uploaded_file.name}")
        
        # CRITICAL: Wait for file propagation across Google's regions
        print("⏳ Letting file propagate (10s)...")
        time.sleep(10) 
        
        return uploaded_file

    def analyze_video_full(self, video_file):
        """
        Analyzes video with aggressive backoff and STRICT JSON enforcement
        """
        print(f"🔍 Analyzing video content...")
        
        # --- THE BRUTAL PROMPT ---
        prompt = """
        You are a strict UI/UX Lead Auditor. Your job is to critique the user interface in this video.
        Do NOT just look for functional crashes. Look for VISUAL CLUTTER, BAD ALIGNMENT, and DATED DESIGN.

        Analyze the video against these "Usability Heuristics":
        1. Aesthetic and Minimalist Design: Is the screen cluttered? Is there too much information?
        2. Consistency: Do fonts and colors clash?
        3. Visibility: Is text too small or low contrast?

        If the website looks chaotic, dated, or overwhelming (like a catalog from the 1990s), FLAG IT AS A HIGH SEVERITY ISSUE.

        Return valid JSON with this EXACT structure:
        {
            "description": "A 1-sentence summary of what the site is",
            "ux_score": 5,  // Integer 1-10 (1 is unreadable, 10 is perfect)
            "issues": [
                {
                    "timestamp": "00:05",
                    "severity": "High",
                    "issue": "Brief name of issue",
                    "details": "Explanation of why this is bad"
                }
            ]
        }
        """

        for i, model_name in enumerate(MODEL_FALLBACK_CHAIN):
            try:
                print(f"   Attempting with {model_name}...")
                
                # FORCE JSON MODE
                # This config tells Gemini: "Output ONLY JSON. No Markdown."
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_uri(
                            file_uri=video_file.uri,
                            mime_type=video_file.mime_type
                        ),
                        prompt
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json"  # <--- THE MAGIC FIX
                    )
                )
                print(f"   ✅ Success with {model_name}!")
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                print(f"   ⚠️ {model_name} failed.")
                
                # Handle Rate Limits (429)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    print(f"      ↳ Quota limit hit. Sleeping 30s...")
                    time.sleep(30)
                
                # Handle Overload (503)
                elif "503" in error_msg or "overloaded" in error_msg:
                    print(f"      ↳ Server overloaded. Sleeping 5s...")
                    time.sleep(5)
                
                # If last model, crash
                if i == len(MODEL_FALLBACK_CHAIN) - 1:
                    raise Exception(f"❌ All models failed. Last error: {error_msg}")
                
                print("      ↳ Switching to next model...")
                continue

        return None

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m agents.analyst <video_path>")
        return
    
    video_path = sys.argv[1]
    
    try:
        analyst = GeminiAnalyst()
        video_file = analyst.upload_video(video_path)
        result_text = analyst.analyze_video_full(video_file)
        
        # Clean up Markdown just in case (though JSON mode usually prevents it)
        clean_json = result_text.strip()
        if clean_json.startswith('```'):
            clean_json = re.sub(r'^```(?:json)?\s*', '', clean_json)
            clean_json = re.sub(r'\s*```$', '', clean_json)
        
        # Parse Results
        data = json.loads(clean_json)
        
        print("\n" + "=" * 70)
        print("📊 VISIONQA ANALYSIS REPORT")
        print("=" * 70)
        
        print(f"\n📄 Description: {data.get('description', 'N/A')}")
        print(f"⭐ UX Score: {data.get('ux_score', '?')}/10")
        
        # NOTE: We look for 'issues' now, matching the new prompt
        issues = data.get('issues', [])
        print(f"\n🐛 Issues Found: {len(issues)}")
        
        if issues:
            # Sort by severity (High first)
            severity_order = {"High": 0, "Medium": 1, "Low": 2}
            issues.sort(key=lambda x: severity_order.get(x.get('severity', 'Low'), 3))

            for i, issue in enumerate(issues, 1):
                sev = issue.get('severity', 'Low')
                icon = "🔴" if sev == "High" else "🟡" if sev == "Medium" else "🟢"
                
                print(f"\n   {i}. {icon} [{sev.upper()}] {issue.get('issue', 'Unknown Issue')}")
                print(f"      Timestamp: {issue.get('timestamp', 'N/A')}")
                print(f"      ↳ {issue.get('details', '')}")
        else:
            print("\n   ✅ No issues detected. (If this is Arngren.net, something is wrong!)")
        
        print("\n" + "=" * 70)
        
        # Save Report
        output_file = Path(video_path).stem + "_qa_report.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()