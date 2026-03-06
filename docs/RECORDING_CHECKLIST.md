# 🎬 Recording Preparation Checklist

## PRE-RECORDING SETUP

### Environment Setup
- [ ] Clean desktop (close unnecessary windows)
- [ ] Close personal/sensitive applications
- [ ] Set terminal font size: 16pt minimum
- [ ] Set VS Code zoom: 125-150%
- [ ] Test microphone levels (speak, clap, check volume)
- [ ] Test screen recording (30 sec test)
- [ ] Good lighting (face camera if using webcam)
- [ ] Water nearby (avoid coughing/dry throat)

### Application Setup
- [ ] API server NOT running (start fresh in video)
- [ ] Streamlit NOT running (start fresh in video)
- [ ] Docker containers stopped (start fresh in video)
- [ ] All terminals closed
- [ ] Browser tabs: only localhost:8000/docs
- [ ] VS Code open to project root

### Files to Prepare
- [ ] Sample clinical note in clipboard/notepad:
```
Patient John Doe (DOB: 11/04/1958) was admitted on Oct 12th for acute exacerbation of chronic obstructive pulmonary disease (COPD) and poorly controlled Type 2 Diabetes Mellitus. Patient was stabilized in the ICU. Upon discharge, patient is prescribed Metformin 500mg PO BID and an Albuterol HFA inhaler 2 puffs q4h PRN for wheezing.
```

- [ ] Questions to ask ready:
  - "What is the dosage of Metformin?"
  - "What is the patient's blood pressure?" (to show refusal)

- [ ] .env file ready with visible API key (can be dummy: `GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx`)

---

## RECORDING SOFTWARE SETUP

### Option 1: OBS Studio (Recommended for Quality)
```
Download: https://obsproject.com/
Settings:
- Video: 1920x1080, 30fps
- Audio: Desktop + Microphone
- Output: MP4, Quality preset
- Save to: Desktop/recording.mp4
```

### Option 2: Loom (Easiest)
```
Website: https://www.loom.com/
- Browser extension or desktop app
- "Screen + Camera" or "Screen Only"
- Auto-uploads to cloud
- Shareable link generated
```

### Option 3: Windows Game Bar (Built-in)
```
Press: Win + G
- Click Record button
- Saves to: Videos/Captures folder
- Simple, no setup needed
```

### Option 4: Zoom (If You Have It)
```
- Start meeting (alone)
- Share screen
- Start recording
- Downloads when you end meeting
```

---

## 🎬 RECORDING FLOW

### Part 1: Introduction (2 min)
```
SHOW: Project folder in VS Code
SAY: Full intro from script
SHOW: Hover over each folder/file
```

### Part 2: Technical Deep Dive (3 min)
```
OPEN: src/llm_service.py
SHOW: 
  - Line 50-70: JSON mode configuration
  - Line 100-120: System prompt
EXPLAIN: JSON stability + hallucination prevention
```

### Part 3: Live Demo (5 min)
```
TERMINAL 1:
  uvicorn src.api:app --reload

BROWSER:
  http://localhost:8000/docs
  - Test /extract endpoint
  - Test /query endpoint (both questions)

TERMINAL 2:
  streamlit run streamlit_app.py
  - Show UI
  - Paste note
  - Extract
  - Ask question

TERMINAL 3:
  docker build -t clinical-note-api .
  docker run -p 8000:8000 -e GROQ_API_KEY="..." clinical-note-api
  - Show running
  - Test /health endpoint
```

### Part 4: Architecture & Scaling (2 min)
```
SHOW: README.md scrolled to "Scaling" section
SAY: Key points from script
  - Horizontal scaling
  - Message queues
  - Caching
  - Cost estimates
```

### Part 5: Closing (1 min)
```
SHOW: Project root folder
SAY: Summary of deliverables
SAY: "Thank you, code available in repository"
```

---

## SPEAKING TIPS

### Pace & Clarity
- [ ] Speak 20% slower than normal (viewers may not be native English speakers)
- [ ] Pause 2 seconds between major points (helps with editing)
- [ ] If you mess up, pause 3 seconds, restart that sentence
- [ ] Smile while talking (people can hear it!)

### Technical Demos
- [ ] Say what you're about to do BEFORE doing it
- [ ] After executing, pause 2 seconds to let viewers read output
- [ ] Point with mouse cursor to highlight specific elements
- [ ] Zoom in (Ctrl++) if showing detailed code

### Energy Level
- [ ] Match energy to content:
  - Introduction: High energy
  - Code walkthrough: Moderate, focused
  - Demo: High energy, enthusiastic
  - Scaling discussion: Confident, professional

---

## POST-RECORDING CHECKLIST

### Immediately After Recording
- [ ] Watch the video once (check audio/video quality)
- [ ] Check: Is code readable at normal size?
- [ ] Check: Is audio clear throughout?
- [ ] Check: Did all demos work correctly?

### Editing (Optional but Recommended)
- [ ] Cut out long pauses (>5 seconds)
- [ ] Remove mistakes/restarts
- [ ] Add title slide (first 5 seconds):
```
Clinical Note Processing API
Technical Walkthrough
[Your Name]
```

- [ ] Add chapter markers (if platform supports it):
  - 0:00 Introduction
  - 2:00 Technical Decisions
  - 5:00 Live Demo
  - 10:00 Scaling Strategy
  - 12:00 Conclusion

### File Management
- [ ] Export as MP4 (H.264 codec for compatibility)
- [ ] File size: Aim for <500MB (easier to upload/download)
- [ ] Filename: `Clinical_Note_API_Technical_Walkthrough.mp4`
- [ ] Backup copy saved

---

## UPLOAD & SUBMISSION

### Where to Upload
- [ ] **Option 1:** Google Drive (set to "Anyone with link can view")
- [ ] **Option 2:** YouTube (unlisted)
- [ ] **Option 3:** Loom (auto-hosted)
- [ ] **Option 4:** Vimeo
- [ ] **Include link in README.md** under "Technical Explanation Recording"

### Add Video Link to README
```markdown
## Technical Explanation Recording

Watch the complete technical walkthrough: [Video Link](https://your-video-link-here)

**Topics Covered:**
- Architecture overview and code structure
- JSON stability and hallucination prevention
- Live demonstration (local, Streamlit, Docker)
- Scaling strategy for 10,000 notes/minute
- Production readiness features
```

---

## COMMON ISSUES & SOLUTIONS

### Issue: Audio too quiet
**Solution:** Speak closer to mic, or boost in post-production (Audacity free tool)

### Issue: Terminal text too small
**Solution:** Ctrl++ to zoom, or set font size to 18pt in terminal settings

### Issue: Demo fails during recording
**Solution:** Don't panic! Say "let me restart this", fix it, continue. Edit out in post.

### Issue: Forget what to say next
**Solution:** Have QUICK_TALKING_POINTS.md open on second monitor or printed

### Issue: Recording file is huge (>2GB)
**Solution:** 
- Lower resolution to 1280x720
- Or use HandBrake to compress after recording
- Or split into 2-3 shorter videos

---

## TIME BUDGET BY SECTION

Total Target: **12-15 minutes**

- Introduction & Overview: 2 min
- Technical Decisions: 3 min
- Live Demonstrations: 5 min
- Scaling Discussion: 2 min
- Wrap-up: 1 min
- **Buffer:** 2-3 min for slower pace

**Don't go over 18 minutes** - attention spans drop after 15 min.

---

## FINAL PRE-RECORD CHECK

Read this out loud right before hitting record:

**"I am recording a technical explanation of my Clinical Note Processing API. I will:**
1. Show the code structure
2. Explain JSON stability and hallucination prevention
3. Demonstrate the API working locally, in Streamlit, and in Docker
4. Discuss scaling to 10,000 notes per minute
5. Highlight production-readiness features

**My goal is to clearly communicate technical decisions and demonstrate a working, production-ready application."**

---

## 🎯 REMEMBER

✅ **Confidence!** You built a great project  
✅ **Clarity over speed** - speak slowly  
✅ **Show, don't just tell** - live demos are powerful  
✅ **It's okay to edit** - doesn't need to be perfect in one take  

---

## ⏱️ QUICK 5-MINUTE VERSION (If Time-Constrained)

If you only have time for a short video:

1. **(1 min)** Show folder structure, explain modular design
2. **(2 min)** Run API, show /docs, test both endpoints
3. **(1 min)** Quick Docker demo
4. **(1 min)** Explain JSON stability + scaling approach

Done! Better to have a short, focused video than no video.

---

**You've got this! 🎬**
