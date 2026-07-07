<div align="center">

# JobPilot

### Your locally hosted AI 'agent' for Resume Tailoring and Form Completion

![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![macOS](https://img.shields.io/badge/macOS-000000?style=for-the-badge&logo=apple&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-22+-339933?style=for-the-badge&logo=node.js&logoColor=white)
![Google Chrome](https://img.shields.io/badge/Google%20Chrome-4285F4?style=for-the-badge&logo=google-chrome&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-8F7EE7?style=for-the-badge&logo=google&logoColor=white)
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
- [Commands](#-commands-for-setup)
- [License](#-license)


## 📝 What does this application do?

Automated Resume Tailoring and Form Completion with the click of a button!

TBH: Resume tailor can be useful for similar job titles / skill swaps that are annoying to do. However can be extended with a better prompt if thats your use case. The form completion feature is where it shines though. I use that for every job application because it covers mostly everything past personal info that browsers can auto fill. Its not perfect but I have found it quite useful.

### Resume Tailoring
Tailor your resume by providing a job description and an upload of your .docx resume. Provide skills and the model will swap job titles and skills as you see fit.

### Form Completion
Fill in long application forms with the click of a button. Personal info, skills, experience, and all the other boring fields that each job application asks for.





## 💻 Requirements

**You are required** to run this locally and configure either a local Ollama model or a Cloud model (Gemini - free api). I suggest using Gemini as its simpler to setup.

**Be mindful** that while local models are data secure they require good hardware to run quickly. 

| System Requirements | Details |
|---|---|
| **OS** | Windows 10+ |
| **Python** | 3.10 or higher — [Download](https://www.python.org/downloads/) |
| **Node.js** | 22 or higher — [Download](https://nodejs.org/) |
| **Google Chrome** | Need Chromium on system for form automation library to function properly |

| Models | Details |
|---|---|
| **Local Model** | Ollama |
| --- | [Download & Install](https://ollama.com/download) |
| --- | A compatible LLM via Ollama (e.g. `llama3` or `qwen3:8b`) — [Browse Models](https://ollama.com/library) |
| **Cloud Model** | Gemini |
| --- | [Configure Gemini API](https://aistudio.google.com/) |

## Application Information

### Model Use
- As stated above, you have to use either a local or cloud model.
- *Cloud model support limited to free Gemnini 2.5 Fast*

### Open-Source
- You might want to add columns to the user_profile database table for more coverage on forms. Or anything else within the database schema.
- You can alter Model prompts for how tailoring or form completion model calls work.
- Anything else you can imagine.

### Default Model Configuration
- **Tailoring Model:** The Tailoring prompts are by default configured to swap out job titles and skills.
- **Form Model:** The Form prompts are by default configured to simply fill in all fields it has the information for, pulling from all database tables such as Profile, Skills and Experience.

### Data
- All data is stored locally via SQLite.



## 🚦 How to Use

**1.** Configure a model to use.

**2.** Clone this repo:
```bash
git clone https://github.com/Debugger3000/ResumeTailor
```

**3.** Setup Client and Server (See Commands below for system)

**5.** Open your browser to `http://127.0.0.1:8000`.

**5.** Configure Model, Skills, Experience and Profile data on webpage.

**6.** You're good to go! You can now tailor resumes and auto fill forms with the click of a button. 


## 🔧 Commands for Setup


### Install client JS dependencies:
```bash
npm install
```

### Install server Python dependencies:

#### Windows 

- Doesn't need .venv - Can skip Linux / Mac .venv setup

Install server-side Python:
```bash
pip install -r requirements.txt
```

Start the server / app:
```bash
hypercorn app:app -c hypercorn.toml
```

--- 

#### Linux / Mac 

- Virtual environment setup for hypercorn - Needed for Linux, Mac might not need it.

Create Virtual Environment:
```bash
python3 -m venv .venv
```

Activate Virtual Environment:
```bash
source .venv/bin/activate
```

Deactivate Virtual Environment:
```bash
deactivate
```

Install server-side Python:
```bash
pip install -r requirements.txt
```

Start the server / app:
```bash
hypercorn app:app -c hypercorn.toml
```




## 📜 License

MIT
