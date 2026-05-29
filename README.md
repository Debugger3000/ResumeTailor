<div align="center">

# JobPilot

### Your AI agent for Resume Tailoring and Form Completion

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
- [Requirements](#-requirements)
- [Application Information](#application-information)
- [How to Use](#-how-to-use)
- [Commands](#-commands)
- [Notes](#-notes)
- [License](#-license)


## 📝 What does this application do?

Automate Resume Tailoring and Form Completion with the click of a button!

### Resume Tailoring
Tailor your resume by providing a job description and an upload of your .docx resume. Provide skills and the model will swap job titles and skills as you see fit.

### Form Completion
Fill in long application forms with the click of a button. Personal info, skills, experience, and all the other boring fields that each job application asks for.





## 💻 Requirements

**You are required** to configure either a local Ollama model or a Cloud model (Gemini - free api).

**Be mindful** that while local models are data secure they require good hardware to run quickly. 

| System Requirements | Details |
|---|---|
| **OS** | Windows 10+ |
| **Python** | 3.10 or higher — [Download](https://www.python.org/downloads/) |
| **Node.js** | 22 or higher — [Download](https://nodejs.org/) |

| Models | Details |
|---|---|
| **Local Model** | --- |
| --- | [Download & Install](https://ollama.com/download) |
| --- | A compatible LLM via Ollama (e.g. `llama3` or `qwen3:8b`) — [Browse Models](https://ollama.com/library) |
| **Cloud Model** | --- |
| --- | [Configure Gemini API](https://aistudio.google.com/) |

## Application Information

### Model Use
- As stated above, you have to use either a local or cloud model.
- *Cloud model support limited to free Gemnini 2.5 Fast*

### Open-Source
- You might want to add columns to the user_profile database table for more coverage on forms. Or anything else within the database schema.
- You can alter Model prompts for how tailoring or apply model calls work.
- Anything else you want.

### Default Model Configuration
- *You can alter these prompts to tell the model what logic you want it to execute*
- **Tailoring Model:** The Tailoring prompts are by default configured to swap out job titles and skills.
- **Form/Apply Model:** The Apply/Form prompts are by default configured to simply fill in all fields it has the information for, pulling from personal

### Data
- All data is stored locally via SQLite.



## 🚦 How to Use

**1.** Configure a model to use.

**2.** Clone this repo:
```bash
git clone https://github.com/Debugger3000/ResumeTailor
```

**3.** Install dependencies (see Commands below).

**4.** Run the server (see Commands below).

**5.** Open your browser to `http://127.0.0.1:8000`.

**5.** Configure model, skills, and personal info on web page.

**6.** You're good to go! You can now tailor resumes and auto fill forms with the click of a button. 


## 🔧 Commands

### Dependencies and Run

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



## 📌 Notes

- **Resume format:** Multi-column resumes have not been tested and likely won't work well. A single-column layout is recommended.
- **Model completion times can vary due to:**
  - Local model used — reasoning models are recommended
  - Long job descriptions — paste only what the model needs (job title, skills, etc.)
  - Large webpages with many form fields
- **Tested on Windows 11.** Not currently supported on macOS or Linux.

### Model Config (What you can change)
- **You can alter these prompts to tell the model what logic you want it to execute**
- **Tailoring Model:** The Tailoring prompts are by default configured to swap out job titles and skills.
- **Form/Apply Model:** The Apply/Form prompts are by default configured to simply fill in all fields it has the information for, pulling from personal 




## 📜 License

MIT
