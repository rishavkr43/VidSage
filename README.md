# 🎬 VidSage

VidSage is a Chrome extension + backend service that lets you **chat with YouTube videos**.  
It extracts transcripts, indexes them with FAISS, and uses **Google Gemini** to answer questions with context.

-*-*-*-*-*

## 🚀 Features
- Fetch YouTube transcripts automatically
- Split and embed transcripts using FAISS
- Ask contextual questions while watching a video
- Interactive Chrome extension UI (3D styled with Three.js)
- Maintains conversation history across questions

---

## 📂 Project Structure
```bash
VidSage/
│
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app
│   │   └── transcript.py              # Transcript fetching
│   │
│   ├── models/
│   │   └── schemas.py                 # Pydantic models
│   │── .env
│   └── rag.py                         # Embeddings + retrieval + Gemini
│
├── extension/
│   ├── assets/
│   │   ├── icons/                     # Avatar and icon images
│   │   │   ├── icon1.png
│   │   │   ├── icon2.png
│   │   │   └── icon16.png
│   │   └── backgrounds/
│   │
│   ├── libs/                          # Third-party libs (e.g. three.min.js)
│   │   └── three.min.js
│   │
│   ├── three-scenes/                  # Optional Three.js scene for visuals
│   │
│   ├── content-scripts.js             # Injects floating button into YouTube pages
│   │
│   ├── manifest.json                  # Extension manifest and permissions
│   │
│   ├── ui.css                         # Styles for the extension UI
│   │
│   ├── ui.html                        # UI markup (popup or full-tab page)
│   │
│   └── ui.js                          # Frontend logic and messaging
│
├── requirements.txt
|
├── .gitignore
└── README.md
```


-*-*-*-*-*

## 🛠️ Setup

### 1. Backend
# Install deps (To run Locally )
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
Server runs at: http://127.0.0.1:8000
Docs available at: http://127.0.0.1:8000/docs

2. Environment

Add your Gemini API key in .env inside backend Folder:

GEMINI_API_KEY="your-gemini-api-key-here"

3. Chrome Extension

Go to chrome://extensions/

Enable Developer mode

Click Load unpacked

Select the extension/ folder

Pin VidSage to toolbar

📌 Example Usage

Open a YouTube video

Click VidSage icon

Ask: “Summarize this video in 3 points”

Get contextual Gemini-powered answers 🎉

-*-*-*-*-*
## 🤖 How The AI Answers (and Why It’s Restricted)
VidSage is designed to answer questions *only* using information present in the video's transcript. The AI does not freely invent facts — this restriction prevents hallucinations and keeps answers grounded in the source material.

- **What the AI does:** When you ask a question, the system retrieves relevant transcript snippets, builds a context-aware prompt, and asks Gemini to generate an answer using that exact context.

- **What the AI does not do:** It will not fabricate answers from outside knowledge. If the transcript does not contain the requested information, the AI will respond that it cannot find an answer in the video rather than guessing.

Why this restriction matters
- Large language models (LLMs) are excellent at producing plausible-sounding text. Without strict grounding, they can confidently invent details ("hallucinate") that are not supported by the source.
- By constraining Gemini to only use retrieved transcript text, VidSage avoids presenting users with misleading or false claims.

What happens if you don’t restrict it

If you allow the AI to answer freely without grounding, it can and will fill gaps with plausible-sounding but potentially incorrect information. For example:

- Video topic: "AI in healthcare" (transcript discusses models, workflow, and ethics)
- User question: "What year did the iPhone launch?"

	- Without restrictions → the AI may still answer "2007" (a correct fact, but unrelated to the video), or worse, invent a wrong year with high confidence.
	- With restrictions → the AI should respond: "I don't know — the video transcript doesn't mention that." or "I can't find this information in the video."

This behavior protects users from being misled and preserves trust in the tool.

Best practices
- Phrase questions that are likely to be covered in the video (topics, names, events mentioned). If you need general knowledge beyond the video, ask explicitly that outside sources may be used.
- If a user needs external facts, build a separate QA flow that allows the model to consult broader sources (and clearly present that the answer used external knowledge).

-*-*-*-*-*
