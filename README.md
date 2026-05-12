# JobPilot

> Your local AI agent for Resume Tailoring and Form Completion Automation

---

## Chapters
- [What does this application do?](#what-does-this-application-do)
- [Why use this?](#why-use-this)
- [Requirements](#requirements)
- [How to Use](#how-to-use)
- [Commands](#commands)
- [Performance & Benchmarks](#performance--benchmarks)
- [License](#license)

## What does this application do?

JobPilot automates out the tedious tasks that comes with applying to jobs. Tailoring your resume, and filling out forms.

1. **Resume Tailoring**
- Give your resume and a job description, and let the model do the work. Swapping skills and job titles, so you don't have too.

2. **Form Completion**
- Navigate to a page with form fields and let the model fill in everything for you

---

## Why use this?

If you want to **save time** and **your sanity** applying to jobs

If you're asking yourself "does this actually make a difference?", well good question. I had the same thought before I started developing this.

**The main take away**, is that this is saving you minutes, reducing stress and reducing clicks for every application. As mentioned, its a numbers game. Across tens or over hundreds of applications, this is saving you hours of your time, and of course making the process a lot less painful.
Sure you can copy and paste the same information again and again if you want. But I would much rather click once and protect my mental.

- **Free** — no monthly fees or token costs
- **Open Source** - change the model prompts, tailor again temperature, add in whatever feature you want. Make it yours.
- **Save Time** — cut down each application time with minimal hands on grunt work
- **Save Sanity** — Automate the tedious and boring tasks that comes with applying to jobs

---


## Requirements

Hardware dependent since this project mainly utilizes a local model, which of course needs a decent computer.

** Cloud model connection coming soon...**

- **OS:** Windows 11
- **RAM:** 16GB minimum
- **Ollama:** [Download & install Ollama](https://ollama.com/download)
- **Local model:** A compatible LLM pulled via Ollama (e.g. `llama3` or `qwen3:8b`)
- **Python:** 3.10 or higher — [Download Python](https://www.python.org/downloads/)
- **Node.js:** 22 or higher — [Download Node.js](https://nodejs.org/)

---



## How to Use

1. **Install Ollama** and pull your preferred model (see Requirements).
2. **Clone this repo:**
```git clone https://github.com/Debugger3000/ResumeTailor```
3. **Install dependencies:** (see Commands below).
5. **Run the server** (see Commands below).
6. Open your browser to `"http://127.0.0.1:8000"`.
7. Select model you pulled in config, and voila, your good to go !

---

## Commands

### Ollama
| Command | Description |
|---------|-------------|
| `ollama pull qwen3:8b` | Download the Qwen3 8B model (recommended) |

### Setup & Run
| Command | Description |
|---------|-------------|
| `npm install` | Install client side JS dependencies |
| `pip install -r requirements.txt` | Install server side python dependencies |
| `hypercorn app:app -c hypercorn.toml` | Start the server / app |

---

## Performance & Benchmarks

Performance varies based on your hardware and chosen model. Below are benchmarks from my own development machine.

### Test Machine
- **CPU:** [AMD Ryzen 7 5800X 8-Core Processor, 3.8 Ghz, 8 Core]
- **GPU:** [NVIDIA RTX 3070, 8GB VRAM]
- **RAM:** [32GB DDR4]
- **OS:** Windows 11

### Model Completion Times

| Model | Resume Tailoring | Form Completion | Notes |
|-------|------------------|-----------------|-------|
| `qwen3:8b` | ~25s | ~22s | Recommended — best balance of speed and quality |
| `llama3:8b` | ~12s | ~6s | Faster, slightly less accurate on technical resumes |
| `qwen3:14b` | ~35s | ~20s | Higher quality output, needs more VRAM |
| `mistral:7b` | ~10s | ~5s | Fastest, lighter quality |


## License

MIT
