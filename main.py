import asyncio
import argparse
import sys
import json
import re
from pathlib import Path
from agents.browser import BrowserRecorder
from agents.analyst import GeminiAnalyst
from utils.reporter import HTMLReporter  # Makes sure utils/reporter.py exists

import webbrowser

def print_header():
    print("\n" + "="*60)
    print("     VisionQA: AI-Powered UX Auditor")
    print("       Uses by Gemini 3 Flash & Playwright")
    print("="*60 + "\n")

def print_console_summary(data):
    """Prints the 'Roast' to the terminal"""
    print("\n" + "-" * 60)
    print(f" UX SCORE: {data.get('ux_score', '?')}/10")
    print(f" SUMMARY: {data.get('description', 'N/A')}")
    print("-" * 60)
    
    issues = data.get('issues', [])
    if not issues:
        print(" No major issues found.")
    else:
        # Sort by severity
        severity_map = {"High": 0, "Medium": 1, "Low": 2}
        issues.sort(key=lambda x: severity_map.get(x.get('severity', 'Low'), 3))
        
        print(f" DETECTED ISSUES ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            sev = issue.get('severity', 'Low')
            icon = "🔴" if sev == "High" else "🟡" if sev == "Medium" else "🟢"
            print(f"   {i}. {icon} [{sev}] {issue.get('issue', 'Issue')}")
            print(f"      ↳ {issue.get('details', '')}")
    print("-" * 60)

async def run_audit(url):
    print_header()

    # 1. SETUP
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 2. RECORDING PHASE
    print(f" PHASE 1: DATA COLLECTION")
    print(f"   Target: {url}")
    
    recorder = BrowserRecorder(output_dir=output_dir)
    video_path = await recorder.record_session(url)
    
    if not video_path:
        print(" Fatal Error: Browser failed to record video.")
        return

    # 3. ANALYSIS PHASE
    print(f"\n PHASE 2: AI ANALYSIS")
    
    try:
        analyst = GeminiAnalyst()
        video_file = analyst.upload_video(video_path)
        raw_result = analyst.analyze_video_full(video_file)
        
        # Parse JSON (Handle Markdown wrapping)
        clean_json = raw_result.strip()
        if clean_json.startswith('```'):
            clean_json = re.sub(r'^```(?:json)?\s*', '', clean_json)
            clean_json = re.sub(r'\s*```$', '', clean_json)
        
        data = json.loads(clean_json)
        
        # 4. REPORTING PHASE
        if data:
            # A. Console Output (Instant Gratification)
            print_console_summary(data)
            
            # B. HTML Artifact (The "Vibe Engineering" Proof)
            reporter = HTMLReporter(output_dir=output_dir)
            report_path = reporter.generate_report(data, Path(video_path).name)
            
            print(f"\n SUCCESS: Report Generated!")
            print(f" Open this file: {report_path.absolute()}")

            webbrowser.open(f"file://{report_path.absolute()}")
            
    except Exception as e:
        print(f"\n Error during analysis phase: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="VisionQA - AI Automated UX Testing")
    parser.add_argument("url", help="The website URL to audit")
    args = parser.parse_args()
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        asyncio.run(run_audit(args.url))
    except KeyboardInterrupt:
        print("\n\n Audit interrupted by user.")

if __name__ == "__main__":
    main()