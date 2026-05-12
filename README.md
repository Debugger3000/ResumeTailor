<div align="center">

# JobPilot

### Your local AI agent for Resume Tailoring and Form Completion

![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-22+-339933?style=for-the-badge&logo=node.js&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

*Save time. Save clicks. Save your sanity.*

</div>

---

## 📖 Chapters
- [What does this application do?](#-what-does-this-application-do)
- [Why use this?](#-why-use-this)
- [Requirements](#-requirements)
- [How to Use](#-how-to-use)
- [Commands](#-commands)
- [Performance & Benchmarks](#-performance--benchmarks)
- [Notes](#-notes)
- [License](#-license)


## 📝 What does this application do?

Automate Resume Tailoring and Form Completion for job applications.

### Resume Tailoring
Give your resume and a job description, and let the model do the work. Swapping skills and synonymous job titles, so you don't have to.

### Form Completion
Navigate to a page with form fields and let the model fill in everything for you.


## 💡 Why use this?

If you find the job application process stressful and painful, and want to make it easier for yourself.

> **The main takeaway** — it's a numbers game. Across tens or hundreds of applications, this saves you hours of time and thousands of keystrokes and clicks. Automate the repetitive tasks such as tailoring a new resume for each job, and filling out the same forms again and again.

| | |
|---|---|
| **Free** | No monthly fees or token costs |
| **Open Source** | Change the model prompts, swap models, add features — make it yours |
| **Save Time** | Cut down each application's time with minimal grunt work |
| **Save Clicks** | Click once and let the work be done for you |
| **Save Sanity** | Automate the tedious parts of applying |


## 💻 Requirements

Hardware dependent since this project mainly utilizes a local model, which needs a decent computer.

> **Cloud model connection coming soon...**

| Requirement | Details |
|---|---|
| **OS** | Windows 10+ |
| **System Specs** | [Ollama System Requirements Guide](https://localaimaster.com/blog/ollama-system-requirements) |
| **Ollama** | [Download & Install](https://ollama.com/download) |
| **Local Model** | A compatible LLM via Ollama (e.g. `llama3` or `qwen3:8b`) — [Browse Models](https://ollama.com/library) |
| **Python** | 3.10 or higher — [Download](https://www.python.org/downloads/) |
| **Node.js** | 22 or higher — [Download](https://nodejs.org/) |



## 🚦 How to Use

**1.** Install Ollama and pull your preferred model (see Requirements).

**2.** Clone this repo:
```bash
git clone https://github.com/Debugger3000/ResumeTailor
```

**3.** Install dependencies (see Commands below).

**4.** Run the server (see Commands below).

**5.** Open your browser to `http://127.0.0.1:8000`.

**6.** Select the model you pulled in config — and voilà, you're good to go! 🎉



## 🔧 Commands

### Ollama

Download an Ollama model (pick one that fits your system):
```bash
ollama pull qwen3:8b
```

### Setup & Run

Install client-side JS dependencies:
```bash
npm install
```

Install server-side Python dependencies:
```bash
pip install -r requirements.txt
```

Start the server / app:
```bash
hypercorn app:app -c hypercorn.toml
```



## 📊 Performance & Benchmarks

Performance varies based on your hardware and chosen model. Below are benchmarks from my own development machine.

### Model Completion Times

| Model | Resume Tailoring | Form Completion | Notes |
|-------|:---:|:---:|-------|
| `qwen3:8b` | ~25s | ~22s | **Recommended** — best balance of speed and quality |
| `llama3:8b` | ~30s | ~28s | Faster, slightly less accurate on technical resumes |
| `qwen3:14b` | ~35s | ~20s | Higher quality output, needs more VRAM |
| `mistral:7b` | ~24s | ~23s | Fastest, lighter quality |


## 📌 Notes

- **Resume format:** Multi-column resumes have not been tested and likely won't work well. A single-column layout is recommended (for this app, and in general).
- **Model completion times can vary due to:**
  - Local model used — reasoning models are recommended
  - Long job descriptions — paste only what the model needs (job title, skills, etc.)
  - Large webpages with many form fields
- **Tested on Windows 11.** Not currently supported on macOS or Linux.


## 📜 License

MIT
