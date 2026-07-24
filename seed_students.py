"""
Seed script: complete student profiles for AI skill match.
- Updates existing students with full profile (education, skills, tech stack, experiences, etc.)
- Creates 5 new students with different specializations:
  1. Backend Engineer
  2. Frontend Developer
  3. Data Analyst/Scientist
  4. Mobile Developer
  5. Fullstack Developer
Run: venv\Scripts\python.exe seed_students.py
"""
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models.identity import UserAccount, StudentProfile
from app.models.student import (
    StudentEducationRecord,
    StudentSkill,
    StudentTechStackItem,
    StudentExperience,
    StudentOrganization,
    StudentPortfolio,
    StudentGithubProfile,
    StudentLinkedinProfile,
)
from app.models.master import Skill, TechStackItem
from app.models.lookups import UserAccountStatus

app = create_app()

# ── Helper ────────────────────────────────────────────────────────
def get_or_create(model, defaults=None, **kwargs):
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    db.session.add(instance)
    db.session.flush()
    return instance, True

def date_years_ago(years, months=0):
    return date.today() - timedelta(days=365*years + 30*months)

# ── 5 New Student Personas ────────────────────────────────────────
NEW_STUDENTS = [
    {
        "email": "budi.backend@student.telkomuniversity.ac.id",
        "display_name": "Budi Santoso",
        "password": "Student123!",
        "bio": "Backend engineer passionate about building scalable microservices and RESTful APIs. Experienced with Java Spring Boot, PostgreSQL, and Docker. Love solving complex system design problems.",
        "phone": "081234567890",
        "dob": date(2002, 3, 15),
        "gender": "Laki-laki",
        "education": {
            "degree": "S1",
            "field": "Teknik Informatika",
            "institution": "Telkom University",
            "start": date(2020, 8, 1),
            "end": None,
            "grade": "3.65"
        },
        "skills": [
            ("PROBLEM_SOLVING", "Advanced", 2),
            ("ANALYTICAL_THINKING", "Intermediate", 2),
            ("COMMUNICATION", "Intermediate", 1),
        ],
        "tech_stacks": [
            ("JAVA_SPRING", "Advanced"),
            ("POSTGRESQL", "Advanced"),
            ("MYSQL", "Intermediate"),
            ("DOCKER", "Intermediate"),
            ("KAFKA", "Beginner"),
            ("NODEJS", "Beginner"),
        ],
        "experiences": [
            {
                "title": "Backend Developer Intern",
                "org": "PT Maju Teknologi",
                "desc": "Developed RESTful API for e-commerce platform using Spring Boot. Implemented caching with Redis and message queue with RabbitMQ.",
                "start": date(2023, 6, 1),
                "end": date(2023, 9, 30),
            }
        ],
        "organizations": [
            {
                "name": "Google Developer Student Club Telkom",
                "role": "Backend Lead",
                "desc": "Lead backend team for university hackathon projects and mentoring junior members.",
                "start": date(2022, 9, 1),
                "end": date(2023, 8, 31),
            }
        ],
        "portfolios": [
            {
                "title": "E-Commerce REST API",
                "url": "https://github.com/budisantoso/ecommerce-api",
                "desc": "Scalable e-commerce backend with Spring Boot, PostgreSQL, Redis cache, and JWT authentication. Supports product catalog, shopping cart, and order management.",
            },
            {
                "title": "Microservices Blog Platform",
                "url": "https://github.com/budisantoso/blog-microservices",
                "desc": "Blog platform built with microservices architecture (User service, Post service, Comment service) using Docker Compose and API Gateway pattern.",
            }
        ],
        "github": "budisantoso",
        "linkedin": "https://linkedin.com/in/budi-santoso-backend",
    },
    {
        "email": "sari.frontend@student.telkomuniversity.ac.id",
        "display_name": "Sari Dewi Lestari",
        "password": "Student123!",
        "bio": "Frontend developer with a passion for pixel-perfect UI and smooth user experiences. Skilled in React.js, TypeScript, and TailwindCSS. Loves translating Figma designs into clean, accessible code.",
        "phone": "082345678901",
        "dob": date(2002, 7, 22),
        "gender": "Perempuan",
        "education": {
            "degree": "S1",
            "field": "Sistem Informasi",
            "institution": "Telkom University",
            "start": date(2020, 8, 1),
            "end": None,
            "grade": "3.78"
        },
        "skills": [
            ("UI_IMPLEMENTATION", "Advanced", 2),
            ("CREATIVITY", "Advanced", 3),
            ("COMMUNICATION", "Advanced", 2),
        ],
        "tech_stacks": [
            ("REACT_JS", "Advanced"),
            ("TYPESCRIPT", "Intermediate"),
            ("TAILWIND_CSS", "Advanced"),
            ("FIGMA", "Intermediate"),
            ("NODEJS", "Beginner"),
            ("ADOBE_XD", "Beginner"),
        ],
        "experiences": [
            {
                "title": "Frontend Developer Intern",
                "org": "Startup Kreatif Digital",
                "desc": "Developed React components for a SaaS dashboard application. Improved Lighthouse performance score from 62 to 91 through lazy loading and code splitting.",
                "start": date(2023, 7, 1),
                "end": date(2023, 10, 31),
            }
        ],
        "organizations": [
            {
                "name": "UI/UX Community Telkom University",
                "role": "Ketua Divisi Frontend",
                "desc": "Organized frontend workshops and design system talks for 200+ students.",
                "start": date(2022, 10, 1),
                "end": date(2023, 9, 30),
            }
        ],
        "portfolios": [
            {
                "title": "Dashboard Analytics UI",
                "url": "https://github.com/saridewi/analytics-dashboard",
                "desc": "Interactive analytics dashboard built with React, TypeScript, and Recharts. Features dark mode, responsive layout, and real-time data visualization.",
            },
            {
                "title": "E-Commerce Frontend (Next.js)",
                "url": "https://sari-shop.vercel.app",
                "desc": "Full e-commerce storefront using Next.js 14 App Router, TailwindCSS, and Zustand state management. Optimized for Core Web Vitals.",
            }
        ],
        "github": "saridewilestari",
        "linkedin": "https://linkedin.com/in/sari-dewi-frontend",
    },
    {
        "email": "rizki.data@student.telkomuniversity.ac.id",
        "display_name": "Rizki Permana",
        "password": "Student123!",
        "bio": "Data analyst with strong foundation in statistics and machine learning. Experienced in Python (Pandas, Scikit-learn), SQL, and Tableau. Passionate about turning raw data into actionable business insights.",
        "phone": "083456789012",
        "dob": date(2001, 11, 5),
        "gender": "Laki-laki",
        "education": {
            "degree": "S1",
            "field": "Ilmu Komputasi",
            "institution": "Telkom University",
            "start": date(2019, 8, 1),
            "end": None,
            "grade": "3.82"
        },
        "skills": [
            ("ANALYTICAL_THINKING", "Advanced", 3),
            ("PROBLEM_SOLVING", "Advanced", 3),
            ("COMMUNICATION", "Intermediate", 2),
        ],
        "tech_stacks": [
            ("PYTHON", "Advanced"),
            ("SCIKIT_LEARN", "Intermediate"),
            ("TABLEAU", "Advanced"),
            ("POSTGRESQL", "Intermediate"),
            ("AIRFLOW", "Beginner"),
            ("GOOGLE_ANALYTICS", "Intermediate"),
        ],
        "experiences": [
            {
                "title": "Data Analyst Intern",
                "org": "PT Retailindo Data",
                "desc": "Analyzed 2M+ transaction records to identify buying patterns. Built automated weekly reports reducing analyst manual work by 60%. Created Tableau dashboards for C-suite.",
                "start": date(2023, 1, 1),
                "end": date(2023, 6, 30),
            }
        ],
        "organizations": [
            {
                "name": "Data Science Club Telkom University",
                "role": "Vice President",
                "desc": "Organized weekly kaggle competition discussions, data literacy bootcamp, and data science talks with industry practitioners.",
                "start": date(2022, 8, 1),
                "end": date(2023, 7, 31),
            }
        ],
        "portfolios": [
            {
                "title": "Customer Churn Prediction Model",
                "url": "https://github.com/rizkipermana/churn-prediction",
                "desc": "ML model predicting telecom customer churn using Random Forest & XGBoost with 87% accuracy. Includes SHAP explainability and Streamlit demo app.",
            },
            {
                "title": "Jakarta Air Quality Analysis",
                "url": "https://github.com/rizkipermana/jakarta-air-quality",
                "desc": "Exploratory data analysis of Jakarta's air quality data 2019-2023 using Python, Pandas, and Plotly. Identifies key pollutant patterns and seasonal trends.",
            }
        ],
        "github": "rizkipermana",
        "linkedin": "https://linkedin.com/in/rizki-permana-data",
    },
    {
        "email": "nadia.mobile@student.telkomuniversity.ac.id",
        "display_name": "Nadia Putri Anjani",
        "password": "Student123!",
        "bio": "Mobile developer specializing in cross-platform development with Flutter and native Android (Kotlin). Experienced in state management (BLoC, Riverpod) and Firebase integration. Building user-centric mobile apps.",
        "phone": "084567890123",
        "dob": date(2002, 1, 18),
        "gender": "Perempuan",
        "education": {
            "degree": "S1",
            "field": "Teknik Informatika",
            "institution": "Universitas Gadjah Mada",
            "start": date(2020, 8, 1),
            "end": None,
            "grade": "3.71"
        },
        "skills": [
            ("UI_IMPLEMENTATION", "Advanced", 2),
            ("PROBLEM_SOLVING", "Intermediate", 2),
            ("CREATIVITY", "Intermediate", 2),
        ],
        "tech_stacks": [
            ("FLUTTER", "Advanced"),
            ("DART", "Advanced"),
            ("KOTLIN", "Intermediate"),
            ("ANDROID_STUDIO", "Intermediate"),
            ("FIGMA", "Intermediate"),
            ("POSTMAN", "Beginner"),
        ],
        "experiences": [
            {
                "title": "Mobile Developer Intern",
                "org": "GoTech Solutions",
                "desc": "Developed Flutter features for a ride-hailing passenger app. Integrated Google Maps SDK, real-time location tracking with WebSocket, and push notifications.",
                "start": date(2023, 6, 1),
                "end": date(2023, 9, 30),
            }
        ],
        "organizations": [
            {
                "name": "Google Developer Student Club UGM",
                "role": "Mobile Development Lead",
                "desc": "Led Flutter workshops, coordinated GDG Solution Challenge team, and mentored 30+ students in mobile development.",
                "start": date(2022, 9, 1),
                "end": date(2023, 8, 31),
            }
        ],
        "portfolios": [
            {
                "title": "FlutterShop - E-Commerce Mobile App",
                "url": "https://github.com/nadiapanjani/flutter-shop",
                "desc": "Full-featured Flutter e-commerce app with BLoC state management, REST API integration, Firebase Auth, and Midtrans payment gateway.",
            },
            {
                "title": "MoodTracker - Mental Health App",
                "url": "https://github.com/nadiapanjani/mood-tracker",
                "desc": "Flutter app for daily mood tracking with local database (Hive), push notifications, and mood trend visualization using fl_chart.",
            }
        ],
        "github": "nadiapanjani",
        "linkedin": "https://linkedin.com/in/nadia-putri-mobile",
    },
    {
        "email": "fauzan.fullstack@student.telkomuniversity.ac.id",
        "display_name": "Fauzan Akbar Ramadhan",
        "password": "Student123!",
        "bio": "Fullstack developer comfortable across the entire web stack. Builds backend APIs with Node.js/Laravel and crafts responsive frontends with Vue.js. Experienced deploying on AWS and containerizing with Docker.",
        "phone": "085678901234",
        "dob": date(2001, 8, 30),
        "gender": "Laki-laki",
        "education": {
            "degree": "S1",
            "field": "Teknik Informatika",
            "institution": "Institut Teknologi Bandung",
            "start": date(2019, 8, 1),
            "end": None,
            "grade": "3.55"
        },
        "skills": [
            ("PROBLEM_SOLVING", "Advanced", 3),
            ("COMMUNICATION", "Advanced", 3),
            ("ANALYTICAL_THINKING", "Intermediate", 2),
        ],
        "tech_stacks": [
            ("NODEJS", "Advanced"),
            ("VUE_JS", "Advanced"),
            ("LARAVEL", "Intermediate"),
            ("POSTGRESQL", "Intermediate"),
            ("DOCKER", "Intermediate"),
            ("AWS", "Beginner"),
        ],
        "experiences": [
            {
                "title": "Fullstack Developer Intern",
                "org": "CV Inovasi Digital",
                "desc": "Built and deployed a company HR management system. Developed backend REST API with Node.js/Express and frontend SPA with Vue 3 Composition API.",
                "start": date(2023, 3, 1),
                "end": date(2023, 8, 31),
            }
        ],
        "organizations": [
            {
                "name": "Himpunan Mahasiswa Informatika ITB",
                "role": "Koordinator Divisi Software Development",
                "desc": "Managed software projects for student body events and organized weekly tech sharing sessions.",
                "start": date(2021, 10, 1),
                "end": date(2022, 9, 30),
            }
        ],
        "portfolios": [
            {
                "title": "HR Management System",
                "url": "https://github.com/fauzanakbar/hr-system",
                "desc": "Full-stack HR system with Node.js API (Express, Sequelize), Vue 3 frontend, PostgreSQL database, and Docker Compose deployment. Features attendance, payroll, and leave management.",
            },
            {
                "title": "Real-Time Chat App",
                "url": "https://github.com/fauzanakbar/realtime-chat",
                "desc": "WebSocket-based chat application using Node.js (Socket.io), Vue.js frontend, and Redis pub/sub for scalable message broadcasting.",
            }
        ],
        "github": "fauzanakbar",
        "linkedin": "https://linkedin.com/in/fauzan-akbar-fullstack",
    },
]

# ── Existing student profile completions ─────────────────────────
# Keyed by email. Only fields not yet filled will be added.
EXISTING_STUDENT_PATCHES = {
    "rasyidnafsyarie@gmail.com": {
        "display_name": "Rasyid Nafsyarie",
        "bio": "Enthusiastic computer science student with interest in backend development and cloud infrastructure. Currently learning Kubernetes and CI/CD pipelines.",
        "phone": "081111222333",
        "dob": date(2002, 5, 10),
        "gender": "Laki-laki",
        "education": {
            "degree": "S1", "field": "Teknik Informatika",
            "institution": "Telkom University Purwokerto",
            "start": date(2021, 8, 1), "end": None, "grade": "3.50"
        },
        "skills": [
            ("PROBLEM_SOLVING", "Intermediate", 1),
            ("ANALYTICAL_THINKING", "Intermediate", 1),
            ("COMMUNICATION", "Beginner", 1),
        ],
        "tech_stacks": [
            ("PYTHON", "Intermediate"),
            ("POSTGRESQL", "Beginner"),
            ("DOCKER", "Beginner"),
            ("GITLAB_CI", "Beginner"),
        ],
        "experiences": [
            {
                "title": "Asisten Praktikum Pemrograman",
                "org": "Telkom University Purwokerto",
                "desc": "Membimbing 30 mahasiswa dalam praktikum algoritma dan pemrograman dasar.",
                "start": date(2022, 9, 1), "end": date(2023, 6, 30),
            }
        ],
        "organizations": [
            {
                "name": "Kelompok Studi Linux dan Open Source",
                "role": "Anggota Aktif",
                "desc": "Belajar dan berbagi tentang sistem operasi Linux, shell scripting, dan DevOps tools.",
                "start": date(2022, 3, 1), "end": None,
            }
        ],
        "portfolios": [
            {
                "title": "Simple REST API - Python Flask",
                "url": "https://github.com/rasyidnafsyarie/flask-api",
                "desc": "RESTful API sederhana menggunakan Flask, SQLAlchemy, dan PostgreSQL dengan JWT authentication.",
            }
        ],
        "github": "rasyidnafsyarie",
        "linkedin": "https://linkedin.com/in/rasyid-nafsyarie",
    },
    "harits@gmail.com": {
        "display_name": "Mohammad Harits Tantowi",
        "bio": "Passionate UI/UX designer and frontend developer who loves creating intuitive digital experiences. Proficient in Figma and Vue.js.",
        "phone": "082222333444",
        "dob": date(2001, 9, 14),
        "gender": "Laki-laki",
        "education": {
            "degree": "S1", "field": "Desain Komunikasi Visual",
            "institution": "Telkom University Purwokerto",
            "start": date(2020, 8, 1), "end": None, "grade": "3.68"
        },
        "skills": [
            ("UI_IMPLEMENTATION", "Advanced", 2),
            ("CREATIVITY", "Advanced", 3),
            ("COMMUNICATION", "Advanced", 2),
        ],
        "tech_stacks": [
            ("FIGMA", "Advanced"),
            ("VUE_JS", "Intermediate"),
            ("TAILWIND_CSS", "Intermediate"),
            ("CANVA", "Advanced"),
            ("ADOBE_XD", "Intermediate"),
        ],
        "experiences": [
            {
                "title": "UI/UX Designer Intern",
                "org": "Agensi Digital Purwokerto",
                "desc": "Designed mobile UI for 3 client projects. Conducted user interviews and usability testing. Delivered Figma prototypes with full design handoff.",
                "start": date(2023, 7, 1), "end": date(2023, 10, 31),
            }
        ],
        "organizations": [
            {
                "name": "UX Design Club Telkom University",
                "role": "Koordinator Workshop",
                "desc": "Mengelola seri workshop desain UI/UX bulanan untuk 100+ mahasiswa.",
                "start": date(2022, 10, 1), "end": date(2023, 9, 30),
            }
        ],
        "portfolios": [
            {
                "title": "Redesign Aplikasi Kantin Kampus",
                "url": "https://figma.com/harits-kantin-redesign",
                "desc": "Proyek redesign UI/UX aplikasi kantin kampus. Meningkatkan task completion rate dari 64% ke 91% berdasarkan usability test.",
            }
        ],
        "github": "haritstan",
        "linkedin": "https://linkedin.com/in/mohammad-harits",
    },
    "jarwo@gmail.com": {
        "display_name": "Jarwo",
        "bio": "Mobile developer focused on Android native development with Kotlin. Interested in building performance-optimized apps with clean architecture.",
        "phone": "083333444555",
        "dob": date(2002, 12, 3),
        "gender": "Laki-laki",
        "education": {
            "degree": "S1", "field": "Teknik Informatika",
            "institution": "Universitas Muhammadiyah Purwokerto",
            "start": date(2021, 8, 1), "end": None, "grade": "3.40"
        },
        "skills": [
            ("PROBLEM_SOLVING", "Intermediate", 1),
            ("UI_IMPLEMENTATION", "Intermediate", 1),
            ("ANALYTICAL_THINKING", "Beginner", 1),
        ],
        "tech_stacks": [
            ("KOTLIN", "Intermediate"),
            ("ANDROID_STUDIO", "Intermediate"),
            ("JAVA_SPRING", "Beginner"),
            ("POSTMAN", "Intermediate"),
            ("MYSQL", "Beginner"),
        ],
        "experiences": [
            {
                "title": "Freelance Android Developer",
                "org": "Self-Employed",
                "desc": "Developed 2 Android apps for local SMEs: inventory management app and simple POS cashier app.",
                "start": date(2023, 1, 1), "end": date(2023, 12, 31),
            }
        ],
        "organizations": [
            {
                "name": "Komunitas Android Developer Purwokerto",
                "role": "Member",
                "desc": "Belajar bersama tentang Android development best practices dan update fitur terbaru.",
                "start": date(2022, 5, 1), "end": None,
            }
        ],
        "portfolios": [
            {
                "title": "Inventory Manager Android App",
                "url": "https://github.com/jarwo-dev/inventory-android",
                "desc": "Aplikasi manajemen stok toko dengan Kotlin, Room database, dan MVVM architecture pattern.",
            }
        ],
        "github": "jarwo-dev",
        "linkedin": "https://linkedin.com/in/jarwo-android",
    },
    "budiono@gmail.com": {
        "display_name": "Budiono Siregar",
        "bio": "Data science enthusiast with solid Python skills and statistics background. Currently working on NLP projects and exploring machine learning model deployment.",
        "phone": "084444555666",
        "dob": date(2000, 4, 20),
        "gender": "Laki-laki",
        "education": {
            "degree": "S1", "field": "Statistika",
            "institution": "Institut Pertanian Bogor",
            "start": date(2019, 8, 1), "end": None, "grade": "3.60"
        },
        "skills": [
            ("ANALYTICAL_THINKING", "Advanced", 3),
            ("PROBLEM_SOLVING", "Advanced", 2),
            ("COMMUNICATION", "Intermediate", 2),
        ],
        "tech_stacks": [
            ("PYTHON", "Advanced"),
            ("SCIKIT_LEARN", "Advanced"),
            ("TABLEAU", "Intermediate"),
            ("POSTGRESQL", "Intermediate"),
            ("GOOGLE_ANALYTICS", "Beginner"),
        ],
        "experiences": [
            {
                "title": "Research Assistant - Data Science",
                "org": "Institut Pertanian Bogor",
                "desc": "Assisted professor in agricultural yield prediction research using Python. Processed satellite imagery data and built regression models with scikit-learn.",
                "start": date(2022, 3, 1), "end": date(2023, 2, 28),
            }
        ],
        "organizations": [
            {
                "name": "Himpunan Mahasiswa Statistika IPB",
                "role": "Sekretaris",
                "desc": "Mengelola administrasi organisasi dan menyelenggarakan kompetisi statistika tingkat nasional.",
                "start": date(2021, 9, 1), "end": date(2022, 8, 31),
            }
        ],
        "portfolios": [
            {
                "title": "Sentiment Analysis Twitter",
                "url": "https://github.com/budiono-siregar/sentiment-analysis",
                "desc": "NLP project untuk analisis sentimen tweet berbahasa Indonesia menggunakan IndoBERT. Akurasi 89% pada dataset ulasan produk e-commerce.",
            }
        ],
        "github": "budiono-siregar",
        "linkedin": "https://linkedin.com/in/budiono-siregar",
    },
    "alvonzo@gmail.com": {
        "display_name": "Aji Alvonzo",
        "bio": "Cybersecurity enthusiast and backend developer. Interested in secure coding, penetration testing basics, and API security. Active in CTF competitions.",
        "phone": "085555666777",
        "dob": date(2002, 6, 7),
        "gender": "Laki-laki",
        "education": {
            "degree": "S1", "field": "Keamanan Siber",
            "institution": "Telkom University Purwokerto",
            "start": date(2021, 8, 1), "end": None, "grade": "3.45"
        },
        "skills": [
            ("PROBLEM_SOLVING", "Advanced", 2),
            ("ANALYTICAL_THINKING", "Advanced", 2),
            ("COMMUNICATION", "Beginner", 1),
        ],
        "tech_stacks": [
            ("PYTHON", "Intermediate"),
            ("KALI_LINUX", "Intermediate"),
            ("BURPSUITE", "Intermediate"),
            ("WIRESHARK", "Intermediate"),
            ("POSTGRESQL", "Beginner"),
        ],
        "experiences": [
            {
                "title": "Security Lab Assistant",
                "org": "Telkom University Purwokerto",
                "desc": "Maintained cybersecurity lab environment, created CTF challenge scenarios, and guided students in network security practicals.",
                "start": date(2023, 2, 1), "end": date(2023, 12, 31),
            }
        ],
        "organizations": [
            {
                "name": "CyberSec Community Telkom University",
                "role": "CTF Team Captain",
                "desc": "Led team in national CTF competitions, achieved Top 10 in Cyber Jawara 2023.",
                "start": date(2022, 9, 1), "end": None,
            }
        ],
        "portfolios": [
            {
                "title": "CTF Write-ups Collection",
                "url": "https://github.com/ajialvonzo/ctf-writeups",
                "desc": "Koleksi write-up CTF dari berbagai kompetisi mencakup kategori web exploitation, cryptography, dan forensics.",
            }
        ],
        "github": "ajialvonzo",
        "linkedin": "https://linkedin.com/in/aji-alvonzo",
    },
}

# ── Main seed logic ───────────────────────────────────────────────
with app.app_context():
    print("=" * 70)
    print("  InternLink Student Profile Seed")
    print("=" * 70)

    # 1. Ensure UserAccountStatus
    active_status, _ = get_or_create(
        UserAccountStatus, status_code='active',
        defaults={'status_name': 'Active'}
    )
    db.session.commit()

    # 2. Build skill & tech_stack lookups
    skills_map = {s.skill_code: s for s in Skill.query.all()}
    tech_stacks_map = {t.tech_stack_code: t for t in TechStackItem.query.all()}

    print(f"\n[INFO] Available Skills: {len(skills_map)}")
    print(f"[INFO] Available TechStacks: {len(tech_stacks_map)}")

    # ── Helper: Fill student profile ──────────────────────────────
    def fill_student_profile(user, data):
        """Fill or update profile for a given user (student)."""
        profile = StudentProfile.query.filter_by(user_account_id=user.id).first()
        if not profile:
            profile = StudentProfile(user_account_id=user.id)
            db.session.add(profile)
            db.session.flush()

        if not profile.bio:
            profile.bio = data.get("bio", "")
        if not profile.phone_number:
            profile.phone_number = data.get("phone", "")
        if not profile.date_of_birth:
            profile.date_of_birth = data.get("dob")
        if not profile.gender:
            profile.gender = data.get("gender", "")

        db.session.flush()

        # Education
        edu_data = data.get("education")
        if edu_data and not StudentEducationRecord.query.filter_by(student_profile_id=profile.id, deleted_at=None).first():
            edu = StudentEducationRecord(
                student_profile_id=profile.id,
                degree_name=edu_data["degree"],
                field_of_study=edu_data["field"],
                institution_name=edu_data["institution"],
                start_date=edu_data["start"],
                end_date=edu_data.get("end"),
                grade=edu_data.get("grade"),
            )
            db.session.add(edu)

        # Skills
        existing_skill_ids = {
            ss.skill_id for ss in StudentSkill.query.filter_by(student_profile_id=profile.id, deleted_at=None).all()
        }
        for skill_code, prof, years in data.get("skills", []):
            skill = skills_map.get(skill_code)
            if skill and skill.id not in existing_skill_ids:
                ss = StudentSkill(
                    student_profile_id=profile.id,
                    skill_id=skill.id,
                    proficiency_level=prof,
                    years_experience=years,
                )
                db.session.add(ss)

        # Tech Stacks
        existing_ts_ids = {
            st.tech_stack_item_id for st in StudentTechStackItem.query.filter_by(student_profile_id=profile.id, deleted_at=None).all()
        }
        for ts_code, prof in data.get("tech_stacks", []):
            ts = tech_stacks_map.get(ts_code)
            if ts and ts.id not in existing_ts_ids:
                sts = StudentTechStackItem(
                    student_profile_id=profile.id,
                    tech_stack_item_id=ts.id,
                    proficiency_level=prof,
                )
                db.session.add(sts)

        # Experiences
        if not StudentExperience.query.filter_by(student_profile_id=profile.id, deleted_at=None).first():
            for exp_data in data.get("experiences", []):
                exp = StudentExperience(
                    student_profile_id=profile.id,
                    title=exp_data["title"],
                    organization_name=exp_data["org"],
                    description=exp_data["desc"],
                    start_date=exp_data["start"],
                    end_date=exp_data.get("end"),
                )
                db.session.add(exp)

        # Organizations
        if not StudentOrganization.query.filter_by(student_profile_id=profile.id, deleted_at=None).first():
            for org_data in data.get("organizations", []):
                org = StudentOrganization(
                    student_profile_id=profile.id,
                    organization_name=org_data["name"],
                    role_title=org_data["role"],
                    description=org_data.get("desc"),
                    start_date=org_data["start"],
                    end_date=org_data.get("end"),
                )
                db.session.add(org)

        # Portfolios
        if not StudentPortfolio.query.filter_by(student_profile_id=profile.id, deleted_at=None).first():
            for pf_data in data.get("portfolios", []):
                pf = StudentPortfolio(
                    student_profile_id=profile.id,
                    portfolio_title=pf_data["title"],
                    portfolio_url=pf_data.get("url"),
                    description=pf_data.get("desc"),
                )
                db.session.add(pf)

        # GitHub
        github_uname = data.get("github")
        if github_uname and not StudentGithubProfile.query.filter_by(student_profile_id=profile.id, deleted_at=None).first():
            gh = StudentGithubProfile(
                student_profile_id=profile.id,
                github_username=github_uname,
                github_url=f"https://github.com/{github_uname}",
            )
            db.session.add(gh)

        # LinkedIn
        linkedin_url = data.get("linkedin")
        if linkedin_url and not StudentLinkedinProfile.query.filter_by(student_profile_id=profile.id, deleted_at=None).first():
            li = StudentLinkedinProfile(
                student_profile_id=profile.id,
                linkedin_url=linkedin_url,
            )
            db.session.add(li)

        db.session.flush()
        return profile

    # ── A. Patch existing students ────────────────────────────────
    print("\n--- Melengkapi profil mahasiswa yang sudah ada ---")
    for email, data in EXISTING_STUDENT_PATCHES.items():
        user = UserAccount.query.filter_by(email=email, role='student', deleted_at=None).first()
        if not user:
            print(f"  [!] Email {email} tidak ditemukan, skip.")
            continue
        fill_student_profile(user, data)
        db.session.commit()
        print(f"  [v] {email} -> profil dilengkapi.")

    # Get remaining students not in patch list and give minimal profile
    patched_emails = set(EXISTING_STUDENT_PATCHES.keys())
    new_emails = {s["email"] for s in NEW_STUDENTS}
    all_known = patched_emails | new_emails

    other_students = UserAccount.query.filter(
        UserAccount.role == 'student',
        UserAccount.deleted_at == None,
        ~UserAccount.email.in_(all_known)
    ).all()

    if other_students:
        print(f"\n  [INFO] Ditemukan {len(other_students)} mahasiswa lain, mengisi profil dasar...")
        for user in other_students:
            profile = StudentProfile.query.filter_by(user_account_id=user.id).first()
            if not profile:
                profile = StudentProfile(
                    user_account_id=user.id,
                    bio=f"Mahasiswa aktif dengan minat di bidang teknologi.",
                    gender="Laki-laki",
                )
                db.session.add(profile)
                db.session.flush()

            # Minimal: education record
            if not StudentEducationRecord.query.filter_by(student_profile_id=profile.id, deleted_at=None).first():
                db.session.add(StudentEducationRecord(
                    student_profile_id=profile.id,
                    degree_name="S1",
                    field_of_study="Teknik Informatika",
                    institution_name="Telkom University Purwokerto",
                    start_date=date(2021, 8, 1),
                    grade="3.30",
                ))

            # Minimal: 1 skill + 1 tech stack
            if not StudentSkill.query.filter_by(student_profile_id=profile.id, deleted_at=None).first():
                sk = skills_map.get("PROBLEM_SOLVING")
                if sk:
                    db.session.add(StudentSkill(student_profile_id=profile.id, skill_id=sk.id, proficiency_level="Beginner", years_experience=1))

            if not StudentTechStackItem.query.filter_by(student_profile_id=profile.id, deleted_at=None).first():
                ts = tech_stacks_map.get("PYTHON")
                if ts:
                    db.session.add(StudentTechStackItem(student_profile_id=profile.id, tech_stack_item_id=ts.id, proficiency_level="Beginner"))

            db.session.commit()
            print(f"  [v] {user.email} -> profil dasar diisi.")

    # ── B. Create 5 new student accounts ─────────────────────────
    print("\n--- Membuat 5 mahasiswa baru ---")
    for idx, data in enumerate(NEW_STUDENTS, start=1):
        user, u_created = get_or_create(
            UserAccount, email=data["email"],
            defaults={
                "role": "student",
                "password_hash": generate_password_hash(data["password"]),
                "display_name": data["display_name"],
                "account_status_id": active_status.id,
            }
        )
        db.session.flush()

        fill_student_profile(user, data)
        db.session.commit()

        action = "Dibuat baru" if u_created else "Sudah ada, profil dilengkapi"
        print(f"  [{idx}/5] {data['display_name']} ({data['email']}) -> {action}")

    # ── Final summary ─────────────────────────────────────────────
    from sqlalchemy import func
    total_students = UserAccount.query.filter_by(role='student', deleted_at=None).count()
    with_edu = db.session.query(func.count(func.distinct(StudentEducationRecord.student_profile_id))).filter_by(deleted_at=None).scalar()
    with_skills = db.session.query(func.count(func.distinct(StudentSkill.student_profile_id))).filter_by(deleted_at=None).scalar()
    with_ts = db.session.query(func.count(func.distinct(StudentTechStackItem.student_profile_id))).filter_by(deleted_at=None).scalar()
    with_exp = db.session.query(func.count(func.distinct(StudentExperience.student_profile_id))).filter_by(deleted_at=None).scalar()
    with_portfolio = db.session.query(func.count(func.distinct(StudentPortfolio.student_profile_id))).filter_by(deleted_at=None).scalar()
    with_github = db.session.query(func.count(func.distinct(StudentGithubProfile.student_profile_id))).filter_by(deleted_at=None).scalar()

    print()
    print("--- Ringkasan akhir ---")
    print(f"  Total mahasiswa       : {total_students}")
    print(f"  Punya pendidikan      : {with_edu}")
    print(f"  Punya skills          : {with_skills}")
    print(f"  Punya tech stacks     : {with_ts}")
    print(f"  Punya pengalaman      : {with_exp}")
    print(f"  Punya portfolio       : {with_portfolio}")
    print(f"  Punya GitHub          : {with_github}")
    print()
    print("Seed selesai! Password mahasiswa baru: Student123!")
    print("=" * 70)
