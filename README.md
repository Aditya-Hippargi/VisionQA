# VisionQA

**Automated Visual Quality Assurance powered by Gemini's Multimodal Vision**

VisionQA automates the expensive and time-consuming process of visual UI testing by combining browser automation with AI-powered visual analysis. Unlike traditional Selenium scripts that only check if code executes, VisionQA uses Gemini's vision capabilities to identify real visual bugs like overlapping elements, poor contrast, and hidden buttons.

## The Problem

Software companies spend millions on QA engineers to manually check if UIs look correct. Automated testing tools like Selenium can verify functionality but miss visual issues:
- "This button is covered by a pop-up"
- "This text is invisible against the background"
- "This animation is too slow"

## How It Works

1. **Browse**: Playwright automatically navigates your website and records a video session
2. **Analyze**: The video is sent to Gemini 1.5 Pro, which acts as a human QA engineer
3. **Report**: AI-generated bug reports with screenshots and timestamps in a clean HTML format

## Prerequisites

- Python 3.8 or higher
- A Google AI Studio API key ([Get one here](https://makersuite.google.com/app/apikey))
- Internet connection

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/VisionQA.git
cd VisionQA
```

2. **Create a virtual environment (recommended)**
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
playwright install
```

4. **Set up your API key**
Create a `.env` file in the project root:
```bash
GEMINI_API_KEY=your_actual_api_key_here
```

**CRITICAL**: Never commit your `.env` file to Git. It's already in `.gitignore`.

## 🎯 Quick Start

```bash
python main.py --url https://example.com
```

The tool will:
- Launch a headless browser
- Navigate to the URL and record the session
- Send the video to Gemini for analysis
- Generate an HTML report in `output/report.html`

## Project Structure

```
VisionQA/
├── .env                    # API keys (DO NOT COMMIT)
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── main.py                 # Entry point
├── agents/
│   ├── browser.py          # Playwright automation
│   └── analyst.py          # Gemini analysis
├── utils/
│   └── reporter.py         # HTML report generator
├── output/                 # Generated files
│   ├── session.mp4
│   └── report.html
└── templates/
    └── report_template.html # Report HTML template
```

## Features

- **Automated Browser Sessions**: Playwright captures full user journeys
- **AI Visual Analysis**: Gemini identifies visual bugs and UX issues
- **Professional Reports**: Clean HTML output with screenshots and timestamps
- **Error Handling**: Robust retry logic and timeout management
- **Configurable**: Adjust scroll speed, session duration, and analysis depth

## Example Output

The AI generates structured bug reports like:

```json
{
  "bugs": [
    {
      "timestamp": "00:03",
      "issue_type": "visibility",
      "description": "The 'Buy Now' button has insufficient contrast (white text on light gray background)"
    },
    {
      "timestamp": "00:07",
      "issue_type": "overlap",
      "description": "Cookie consent banner covers the main navigation menu"
    }
  ]
}
```

## Built For

This project was created for Google DeepMind Gemini 3 Hackathon, demonstrating the power of multimodal AI in software quality assurance.

## Acknowledgments

- Google Gemini for multimodal AI capabilities
- Playwright for browser automation
- The open-source community

**VisionQA - Because bugs should be caught before your users see them.**