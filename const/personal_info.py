
from const.approved_skills import approved_skills

PROFILE = {
    "personal": {
        "first_name": "John",
        "middle_name": "Michael",
        "last_name": "Doe",
        "full_name": "John Doe",
        "preferred_name": "John",
        "pronouns": "he/him",
        "email": "john.doe@example.com",
        "phone": "+1-416-555-0142",
        "date_of_birth": "1995-04-12",
    },

    "new_account": {
        "password": "PacmaN83$",
        "confirm_password": "PacmaN83$",
    },

    "address": {
        "street": "742 Evergreen Terrace",
        "city": "Toronto",
        "state_province": "Ontario",
        "postal_code": "M5V 2T6",
        "country": "Canada",
    },

    "links": {
        "linkedin": "https://linkedin.com/in/johndoe",
        "github": "https://github.com/johndoe",
        "portfolio": "https://johndoe.dev",
    },

    "work_authorization": {
        "country": "Canada",
        "status": "Canadian citizen",
        "requires_sponsorship_now": False,
        "requires_sponsorship_future": False,
        "authorized_countries": ["Canada"],
    },

    "preferences": {
        "desired_salary": "95000",
        "desired_salary_currency": "CAD",
        "willing_to_relocate": True,
        "preferred_locations": ["Toronto, ON", "Remote"],
        "open_to_travel": True,
        "employment_types": ["full-time", "contract"],
    },

    "experience": [
        {
            "company": "Acme Software Inc.",
            "title": "Senior Software Engineer",
            "location": "Toronto, ON",
            "start_date": "2023-03",
            "end_date": "present",
            "current": True,
            "summary": "Lead developer on the platform team. Built and shipped a real-time data pipeline processing 2M events/day. Mentor two junior engineers.",
            "tech_stack": ["Python", "TypeScript", "PostgreSQL", "Kafka", "AWS"],
        },
        {
            "company": "Globex Corporation",
            "title": "Software Engineer",
            "location": "Toronto, ON",
            "start_date": "2020-07",
            "end_date": "2023-02",
            "current": False,
            "summary": "Full-stack developer on the customer dashboard. Reduced page load times by 60% through query optimization and caching.",
            "tech_stack": ["JavaScript", "React", "Node.js", "MongoDB"],
        },
    ],

    "education": [
        {
            "institution": "University of Toronto",
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "start_date": "2016-09",
            "end_date": "2020-05",
            "gpa": "3.8",
        },
    ],

    "skills": approved_skills,

    "languages_spoken": [
        {"language": "English", "proficiency": "native"},
    ],

    "demographics_voluntary": {
        "gender": "Male",
        "race_ethnicity": "Prefer not to say",
        "veteran_status": "I am not a veteran",
        "disability_status": "I do not have a disability",
        "lgbtq": "Prefer not to say",
    },

    "compliance": {
        "is_18_or_older": True,
        "can_provide_work_documents": True,
        "non_compete_active": False,
        "previously_employed_here": False,
        "referred_by": None,
        "referral_source": "LinkedIn",
    },

    "open_questions": {
        "why_this_company": "I'm drawn to companies that take engineering quality seriously while shipping at pace, and your public engineering blog suggests you do both. I want to grow as an engineer in an environment where I can both contribute to and learn from the team.",
        "why_this_role": "The role aligns well with my background in distributed systems and my interest in developer-facing infrastructure. I want to build tools that make other engineers more effective.",
        "greatest_strength": "I default to writing things down. Design docs, postmortems, decision records — they save the team time and keep me honest about my reasoning.",
        "biggest_weakness": "I tend to over-invest in tooling early in a project. I've gotten better at recognizing when a manual workaround is the right call.",
    },
}