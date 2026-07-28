"""
Seed script: 10 company accounts + 5 internship listings each.
Run: python seed_companies.py
"""
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models.identity import UserAccount, CompanyProfile
from app.models.company import CompanyVerification
from app.models.master import Location, TechnologyCategory, TechStackItem, Skill
from app.models.lookups import (
    UserAccountStatus,
    CompanyVerificationStatus,
    InternshipLifecycleStatus,
    InternshipModerationStatus,
)
from app.models.internship import (
    Internship,
    InternshipRequiredSkill,
    InternshipRequiredTechStackItem,
)

app = create_app()

# â”€â”€ Helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_or_create(model, defaults=None, **kwargs):
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    db.session.add(instance)
    db.session.flush()
    return instance, True

# â”€â”€ Master data â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

COMPANIES_DATA = [
    {
        "email": "ptdigitalsolusi@example.com",
        "display_name": "PT Digital Solusi Indonesia",
        "company_name": "PT Digital Solusi Indonesia",
        "industry": "Software Development",
        "size": "51-200",
        "year": 2015,
        "city": "Jakarta",
        "address": "Gedung Cyber, Jl. Kuningan Barat No. 8, Jakarta Selatan",
        "website": "https://digitalsolusi.example.com",
        "description": "PT Digital Solusi Indonesia adalah perusahaan teknologi terkemuka yang mengembangkan solusi perangkat lunak enterprise untuk sektor perbankan dan keuangan di Indonesia.",
        "verification": "verified",  # verified | pending | rejected
    },
    {
        "email": "cloudnusantara@example.com",
        "display_name": "Cloud Nusantara",
        "company_name": "Cloud Nusantara",
        "industry": "Cloud Computing",
        "size": "11-50",
        "year": 2019,
        "city": "Bandung",
        "address": "Jl. Dago Atas No. 55, Bandung",
        "website": "https://cloudnusantara.example.com",
        "description": "Cloud Nusantara menyediakan layanan cloud infrastructure dan DevOps consulting untuk startup dan perusahaan menengah di seluruh Indonesia.",
        "verification": "verified",
    },
    {
        "email": "kreativemedia@example.com",
        "display_name": "Kreatif Media Digital",
        "company_name": "Kreatif Media Digital",
        "industry": "Digital Marketing",
        "size": "11-50",
        "year": 2018,
        "city": "Yogyakarta",
        "address": "Jl. Malioboro No. 123, Yogyakarta",
        "website": "https://kreativemedia.example.com",
        "description": "Kreatif Media Digital adalah agensi digital marketing full-service yang membantu brand lokal dan internasional berkembang di ekosistem digital.",
        "verification": "verified",
    },
    {
        "email": "fintech.archipelago@example.com",
        "display_name": "Archipelago Fintech",
        "company_name": "Archipelago Fintech",
        "industry": "Financial Technology",
        "size": "51-200",
        "year": 2017,
        "city": "Surabaya",
        "address": "Pakuwon Trade Center Lt. 20, Surabaya",
        "website": "https://archipelagofintech.example.com",
        "description": "Archipelago Fintech membangun platform pembayaran digital dan layanan pinjaman berbasis AI untuk menjangkau masyarakat unbanked di Indonesia.",
        "verification": "verified",
    },
    {
        "email": "agritech.nusantara@example.com",
        "display_name": "AgriTech Nusantara",
        "company_name": "AgriTech Nusantara",
        "industry": "Agricultural Technology",
        "size": "11-50",
        "year": 2020,
        "city": "Semarang",
        "address": "Jl. Pemuda No. 45, Semarang",
        "website": "https://agritecthnusantara.example.com",
        "description": "AgriTech Nusantara mengembangkan platform IoT dan data analytics untuk membantu petani Indonesia meningkatkan produktivitas dan efisiensi pertanian.",
        "verification": "pending",
    },
    {
        "email": "logistikpintar@example.com",
        "display_name": "Logistik Pintar",
        "company_name": "Logistik Pintar",
        "industry": "Logistics Technology",
        "size": "201-500",
        "year": 2016,
        "city": "Jakarta",
        "address": "Jl. TB Simatupang No. 88, Jakarta Selatan",
        "website": "https://logistikpintar.example.com",
        "description": "Logistik Pintar adalah platform manajemen rantai pasok end-to-end yang mengintegrasikan pengiriman, gudang, dan manajemen armada dalam satu ekosistem digital.",
        "verification": "verified",
    },
    {
        "email": "edukasiteknologi@example.com",
        "display_name": "Edukasi Teknologi Indonesia",
        "company_name": "Edukasi Teknologi Indonesia",
        "industry": "EdTech",
        "size": "51-200",
        "year": 2018,
        "city": "Bali",
        "address": "Jl. Sunset Road No. 99, Kuta, Bali",
        "website": "https://edukasitek.example.com",
        "description": "Edukasi Teknologi Indonesia membangun platform e-learning interaktif dengan AI tutor dan live mentoring untuk mencetak talenta digital Indonesia.",
        "verification": "pending",
    },
    {
        "email": "healthbridge.id@example.com",
        "display_name": "HealthBridge Indonesia",
        "company_name": "HealthBridge Indonesia",
        "industry": "Health Technology",
        "size": "11-50",
        "year": 2021,
        "city": "Jakarta",
        "address": "Jl. Sudirman Kav. 52-53, Jakarta",
        "website": "https://healthbridge.example.com",
        "description": "HealthBridge Indonesia mengembangkan aplikasi telemedisin dan sistem rekam medis digital untuk menghubungkan pasien dengan tenaga kesehatan di seluruh Indonesia.",
        "verification": "verified",
    },
    {
        "email": "gamedev.archipelago@example.com",
        "display_name": "Archipelago Game Studio",
        "company_name": "Archipelago Game Studio",
        "industry": "Game Development",
        "size": "11-50",
        "year": 2019,
        "city": "Yogyakarta",
        "address": "Jl. Ring Road Utara No. 12, Yogyakarta",
        "website": "https://archipelagogames.example.com",
        "description": "Archipelago Game Studio adalah studio game indie yang mengembangkan game mobile dan PC bertema budaya Nusantara dengan narrative design kelas dunia.",
        "verification": "rejected",
    },
    {
        "email": "cybersec.id@example.com",
        "display_name": "CyberSec Indonesia",
        "company_name": "CyberSec Indonesia",
        "industry": "Cybersecurity",
        "size": "11-50",
        "year": 2020,
        "city": "Bandung",
        "address": "Jl. Ganesha No. 10, Bandung",
        "website": "https://cybersecid.example.com",
        "description": "CyberSec Indonesia menyediakan layanan penetration testing, security audit, dan managed security operations center (SOC) untuk perusahaan di seluruh Asia Tenggara.",
        "verification": "pending",
    },
]

# â”€â”€ 5 internship templates per company (different jobdesks) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Keys: title, description, type, duration, tech_category_code, lifecycle, moderation,
#       skills (list of skill_code), tech_stacks (list of tech_stack_code), closing_days

INTERNSHIP_TEMPLATES = {
    "PT Digital Solusi Indonesia": [
        {
            "title": "Backend Developer Intern",
            "description": "<p>Bergabunglah sebagai <strong>Backend Developer Intern</strong> dan bantu kami membangun API enterprise yang scalable. Kamu akan bekerja dengan tim backend menggunakan Java Spring Boot dan PostgreSQL.</p><ul><li>Mengembangkan RESTful API sesuai spesifikasi</li><li>Menulis unit test dan integration test</li><li>Melakukan code review bersama senior engineer</li><li>Mendokumentasikan API menggunakan Swagger/OpenAPI</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "BACKEND",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["PROBLEM_SOLVING", "COMMUNICATION"],
            "tech_stacks": ["JAVA_SPRING", "POSTGRESQL"],
            "closing_days": 30,
        },
        {
            "title": "Frontend Developer Intern",
            "description": "<p>Kami mencari <strong>Frontend Developer Intern</strong> yang passionate membangun antarmuka web modern dan responsif untuk aplikasi enterprise kami.</p><ul><li>Mengimplementasikan desain UI dari Figma ke kode React</li><li>Optimasi performa rendering dan Web Vitals</li><li>Integrasi dengan REST API backend</li><li>Menulis komponen reusable dan terdokumentasi</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "FRONTEND",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["UI_IMPLEMENTATION", "COMMUNICATION"],
            "tech_stacks": ["REACT_JS", "TAILWIND_CSS"],
            "closing_days": 25,
        },
        {
            "title": "QA Engineer Intern",
            "description": "<p>Bergabung sebagai <strong>QA Engineer Intern</strong> untuk memastikan kualitas produk perangkat lunak kami melalui pengujian manual dan otomatis.</p><ul><li>Menyusun test case berdasarkan spesifikasi produk</li><li>Melakukan regression testing setiap sprint</li><li>Menulis automated test menggunakan Selenium</li><li>Melaporkan bug dan memverifikasi bug fix</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "QA",
            "lifecycle": "active",
            "moderation": "pending",
            "skills": ["PROBLEM_SOLVING", "ANALYTICAL_THINKING"],
            "tech_stacks": ["SELENIUM", "POSTMAN"],
            "closing_days": 20,
        },
        {
            "title": "Data Analyst Intern",
            "description": "<p>Jadilah <strong>Data Analyst Intern</strong> kami dan transformasikan data mentah menjadi insight bisnis yang berdampak nyata bagi klien enterprise kami.</p><ul><li>Mengolah dan membersihkan dataset menggunakan Python/Pandas</li><li>Membangun dashboard visualisasi data</li><li>Melakukan analisis statistik deskriptif</li><li>Mempresentasikan temuan kepada stakeholder</li></ul>",
            "type": "Remote",
            "duration": 4,
            "tech_category": "DATA",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["ANALYTICAL_THINKING", "COMMUNICATION"],
            "tech_stacks": ["PYTHON", "TABLEAU"],
            "closing_days": 35,
        },
        {
            "title": "DevOps Intern",
            "description": "<p>Kami membuka posisi <strong>DevOps Intern</strong> untuk mendukung tim infrastruktur dalam otomasi deployment dan monitoring sistem produksi kami.</p><ul><li>Membantu setup CI/CD pipeline menggunakan GitLab CI</li><li>Monitoring server dan container dengan Prometheus & Grafana</li><li>Pengelolaan container Docker untuk layanan microservices</li><li>Dokumentasi runbook dan prosedur incident response</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "DEVOPS",
            "lifecycle": "closed",
            "moderation": "approved",
            "skills": ["PROBLEM_SOLVING", "ANALYTICAL_THINKING"],
            "tech_stacks": ["DOCKER", "GITLAB_CI"],
            "closing_days": -5,
        },
    ],
    "Cloud Nusantara": [
        {
            "title": "Cloud Infrastructure Intern",
            "description": "<p>Bergabunglah sebagai <strong>Cloud Infrastructure Intern</strong> dan pelajari cara mengelola infrastruktur cloud skala produksi di AWS dan GCP.</p><ul><li>Provisioning resource cloud menggunakan Terraform</li><li>Konfigurasi load balancer, VPC, dan security group</li><li>Monitoring uptime dan cost optimization</li><li>Membantu migrasi workload on-premise ke cloud</li></ul>",
            "type": "Remote",
            "duration": 3,
            "tech_category": "CLOUD",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["PROBLEM_SOLVING", "ANALYTICAL_THINKING"],
            "tech_stacks": ["AWS", "TERRAFORM"],
            "closing_days": 28,
        },
        {
            "title": "Site Reliability Engineer (SRE) Intern",
            "description": "<p>Posisi <strong>SRE Intern</strong> ini akan memperkenalkan kamu pada praktik-praktik terbaik reliability engineering dalam skala cloud computing.</p><ul><li>Menyusun SLO dan SLI untuk layanan kritikal</li><li>Berpastisipasi dalam on-call rotation (terbatas)</li><li>Otomasi runbook menggunakan Python/Bash</li><li>Analisis post-mortem insiden produksi</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "DEVOPS",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["PROBLEM_SOLVING", "COMMUNICATION"],
            "tech_stacks": ["KUBERNETES", "PROMETHEUS"],
            "closing_days": 21,
        },
        {
            "title": "Backend Engineer Intern â€“ Microservices",
            "description": "<p>Kami mencari <strong>Backend Engineer Intern</strong> yang antusias belajar membangun microservices scalable di lingkungan cloud-native.</p><ul><li>Mengembangkan service baru menggunakan Go atau Node.js</li><li>Integrasi message queue (Kafka/RabbitMQ)</li><li>Menulis OpenAPI specification untuk setiap service</li><li>Code review dan pair programming bersama senior</li></ul>",
            "type": "Remote",
            "duration": 4,
            "tech_category": "BACKEND",
            "lifecycle": "active",
            "moderation": "pending",
            "skills": ["PROBLEM_SOLVING", "COMMUNICATION"],
            "tech_stacks": ["GOLANG", "KAFKA"],
            "closing_days": 40,
        },
        {
            "title": "Database Administrator Intern",
            "description": "<p>Bergabunglah sebagai <strong>DBA Intern</strong> dan bantu kami mengelola dan mengoptimalkan database yang mendukung ribuan klien cloud kami.</p><ul><li>Query tuning dan index optimization PostgreSQL & MySQL</li><li>Setup replikasi dan backup otomatis</li><li>Monitoring slow query dan deadlock</li><li>Dokumentasi skema database dan prosedur maintenance</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "DATA",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["ANALYTICAL_THINKING", "PROBLEM_SOLVING"],
            "tech_stacks": ["POSTGRESQL", "MYSQL"],
            "closing_days": 15,
        },
        {
            "title": "Technical Writer Intern",
            "description": "<p>Kami membuka posisi <strong>Technical Writer Intern</strong> untuk membantu mendokumentasikan produk cloud kami agar mudah dipahami oleh developer.</p><ul><li>Menulis dan memperbarui dokumentasi API</li><li>Membuat tutorial dan quickstart guide</li><li>Berkolaborasi dengan tim engineering untuk akurasi teknis</li><li>Mengelola konten di portal developer kami</li></ul>",
            "type": "Remote",
            "duration": 2,
            "tech_category": "TECHNICAL_WRITING",
            "lifecycle": "closed",
            "moderation": "approved",
            "skills": ["COMMUNICATION", "ANALYTICAL_THINKING"],
            "tech_stacks": ["MARKDOWN", "CONFLUENCE"],
            "closing_days": -10,
        },
    ],
    "Kreatif Media Digital": [
        {
            "title": "UI/UX Designer Intern",
            "description": "<p>Kami mencari <strong>UI/UX Designer Intern</strong> yang kreatif untuk membantu desain pengalaman pengguna kampanye digital klien kami.</p><ul><li>Membuat wireframe dan prototype menggunakan Figma</li><li>Melakukan user research dan usability testing</li><li>Berkolaborasi dengan copywriter dan developer</li><li>Memastikan konsistensi design system</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "DESIGN",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["UI_IMPLEMENTATION", "COMMUNICATION"],
            "tech_stacks": ["FIGMA", "ADOBE_XD"],
            "closing_days": 30,
        },
        {
            "title": "Social Media Specialist Intern",
            "description": "<p>Jadilah <strong>Social Media Specialist Intern</strong> kami dan kelola konten dan strategi media sosial untuk brand-brand besar klien kami.</p><ul><li>Membuat konten kreatif harian untuk Instagram, TikTok, LinkedIn</li><li>Menjadwalkan posting dan memantau engagement</li><li>Menyusun laporan performa mingguan</li><li>Riset tren dan kompetitor</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "MARKETING",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["COMMUNICATION", "CREATIVITY"],
            "tech_stacks": ["CANVA", "META_ADS"],
            "closing_days": 20,
        },
        {
            "title": "SEO Specialist Intern",
            "description": "<p>Bergabunglah sebagai <strong>SEO Specialist Intern</strong> dan bantu klien kami mendominasi halaman pertama mesin pencari.</p><ul><li>Melakukan keyword research dan on-page optimization</li><li>Audit teknis website menggunakan SEMrush/Ahrefs</li><li>Membangun backlink melalui outreach</li><li>Melaporkan ranking dan traffic organic bulanan</li></ul>",
            "type": "Remote",
            "duration": 3,
            "tech_category": "MARKETING",
            "lifecycle": "active",
            "moderation": "pending",
            "skills": ["ANALYTICAL_THINKING", "COMMUNICATION"],
            "tech_stacks": ["GOOGLE_ANALYTICS", "SEMRUSH"],
            "closing_days": 25,
        },
        {
            "title": "Video Content Creator Intern",
            "description": "<p>Kami mencari <strong>Video Content Creator Intern</strong> yang berbakat untuk memproduksi konten video viral untuk klien-klien kami.</p><ul><li>Shoot dan edit video short-form (Reels, TikTok)</li><li>Membuat storyboard dan skrip video</li><li>Berkolaborasi dengan tim kreatif dan klien</li><li>Mengoptimalkan video untuk berbagai platform</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "CONTENT",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["CREATIVITY", "COMMUNICATION"],
            "tech_stacks": ["ADOBE_PREMIERE", "CAPCUT"],
            "closing_days": 18,
        },
        {
            "title": "Performance Marketing Intern",
            "description": "<p>Bergabunglah sebagai <strong>Performance Marketing Intern</strong> dan kelola kampanye paid ads dengan budget jutaan rupiah untuk klien kami.</p><ul><li>Setup dan optimasi campaign Google Ads & Meta Ads</li><li>A/B testing copy dan creative iklan</li><li>Analisis data iklan dan ROAS</li><li>Menyusun laporan performa kampanye</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "MARKETING",
            "lifecycle": "closed",
            "moderation": "approved",
            "skills": ["ANALYTICAL_THINKING", "COMMUNICATION"],
            "tech_stacks": ["GOOGLE_ADS", "META_ADS"],
            "closing_days": -7,
        },
    ],
    "Archipelago Fintech": [
        {
            "title": "Mobile Developer Intern â€“ Android",
            "description": "<p>Kami mencari <strong>Mobile Developer Intern (Android)</strong> untuk membantu mengembangkan aplikasi pembayaran digital kami yang digunakan jutaan pengguna.</p><ul><li>Mengembangkan fitur baru menggunakan Kotlin</li><li>Integrasi SDK payment gateway</li><li>Implementasi UI dari desain Figma</li><li>Menulis unit test dan UI test</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "MOBILE",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["PROBLEM_SOLVING", "UI_IMPLEMENTATION"],
            "tech_stacks": ["KOTLIN", "ANDROID_STUDIO"],
            "closing_days": 30,
        },
        {
            "title": "Data Engineer Intern",
            "description": "<p>Bergabunglah sebagai <strong>Data Engineer Intern</strong> untuk membangun pipeline data yang mendukung analitik fraud detection dan credit scoring kami.</p><ul><li>Membangun ETL pipeline menggunakan Apache Airflow</li><li>Mengelola data warehouse BigQuery/Redshift</li><li>Transformasi data menggunakan dbt</li><li>Monitoring kualitas data harian</li></ul>",
            "type": "Hybrid",
            "duration": 4,
            "tech_category": "DATA",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["ANALYTICAL_THINKING", "PROBLEM_SOLVING"],
            "tech_stacks": ["PYTHON", "AIRFLOW"],
            "closing_days": 35,
        },
        {
            "title": "Machine Learning Intern",
            "description": "<p>Jadilah <strong>Machine Learning Intern</strong> kami dan bantu mengembangkan model AI untuk credit scoring dan deteksi penipuan keuangan.</p><ul><li>Eksplorasi dan preprocessing dataset keuangan</li><li>Melatih dan mengevaluasi model klasifikasi</li><li>Deploy model menggunakan FastAPI</li><li>Monitoring model drift di produksi</li></ul>",
            "type": "Hybrid",
            "duration": 4,
            "tech_category": "AI_ML",
            "lifecycle": "active",
            "moderation": "pending",
            "skills": ["ANALYTICAL_THINKING", "PROBLEM_SOLVING"],
            "tech_stacks": ["PYTHON", "SCIKIT_LEARN"],
            "closing_days": 40,
        },
        {
            "title": "Compliance & Risk Intern",
            "description": "<p>Kami membuka posisi <strong>Compliance & Risk Intern</strong> untuk membantu tim legal dan compliance kami memastikan operasional fintech sesuai regulasi OJK.</p><ul><li>Review dokumen kebijakan dan prosedur operasional</li><li>Monitoring perubahan regulasi keuangan</li><li>Membantu persiapan audit internal</li><li>Penyusunan laporan kepatuhan bulanan</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "FINANCE",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["ANALYTICAL_THINKING", "COMMUNICATION"],
            "tech_stacks": ["MS_EXCEL", "CONFLUENCE"],
            "closing_days": 22,
        },
        {
            "title": "Product Analyst Intern",
            "description": "<p>Bergabunglah sebagai <strong>Product Analyst Intern</strong> dan bantu tim product management kami mengambil keputusan berbasis data.</p><ul><li>Analisis funnel konversi pengguna aplikasi</li><li>A/B testing fitur produk baru</li><li>Menyusun laporan insight pengguna mingguan</li><li>Berkolaborasi dengan PM dan engineering</li></ul>",
            "type": "Remote",
            "duration": 3,
            "tech_category": "PRODUCT",
            "lifecycle": "closed",
            "moderation": "approved",
            "skills": ["ANALYTICAL_THINKING", "COMMUNICATION"],
            "tech_stacks": ["MIXPANEL", "GOOGLE_ANALYTICS"],
            "closing_days": -3,
        },
    ],
    "AgriTech Nusantara": [
        {
            "title": "IoT Developer Intern",
            "description": "<p>Kami mencari <strong>IoT Developer Intern</strong> yang antusias untuk mengembangkan perangkat sensor pertanian pintar kami.</p><ul><li>Pemrograman firmware sensor menggunakan ESP32/Arduino</li><li>Integrasi protokol MQTT untuk transmisi data</li><li>Dashboard monitoring tanaman real-time</li><li>Pengujian perangkat di lapangan</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "IOT",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["PROBLEM_SOLVING", "ANALYTICAL_THINKING"],
            "tech_stacks": ["ARDUINO", "MQTT"],
            "closing_days": 30,
        },
        {
            "title": "Mobile Developer Intern â€“ Flutter",
            "description": "<p>Bergabunglah sebagai <strong>Flutter Developer Intern</strong> untuk mengembangkan aplikasi mobile yang digunakan langsung oleh petani Indonesia.</p><ul><li>Implementasi fitur baru pada aplikasi Flutter</li><li>Integrasi data sensor IoT ke tampilan mobile</li><li>Offline-first functionality untuk area sinyal lemah</li><li>UI/UX yang ramah pengguna awam teknologi</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "MOBILE",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["UI_IMPLEMENTATION", "PROBLEM_SOLVING"],
            "tech_stacks": ["FLUTTER", "DART"],
            "closing_days": 28,
        },
        {
            "title": "Data Scientist Intern",
            "description": "<p>Jadilah <strong>Data Scientist Intern</strong> kami dan kembangkan model prediktif cuaca dan hasil panen untuk membantu petani mengambil keputusan lebih baik.</p><ul><li>Analisis data cuaca dan produktivitas lahan</li><li>Membangun model prediksi menggunakan time series</li><li>Visualisasi insight untuk petani</li><li>Validasi model dengan data lapangan</li></ul>",
            "type": "Remote",
            "duration": 4,
            "tech_category": "AI_ML",
            "lifecycle": "active",
            "moderation": "pending",
            "skills": ["ANALYTICAL_THINKING", "PROBLEM_SOLVING"],
            "tech_stacks": ["PYTHON", "SCIKIT_LEARN"],
            "closing_days": 35,
        },
        {
            "title": "Backend Developer Intern â€“ API & Integration",
            "description": "<p>Kami membuka posisi <strong>Backend Developer Intern</strong> untuk membangun API yang menghubungkan perangkat IoT lapangan dengan platform cloud kami.</p><ul><li>Pengembangan REST API menggunakan Node.js</li><li>Integrasi data sensor dari MQTT broker</li><li>Manajemen database time-series (InfluxDB)</li><li>Dokumentasi API endpoint</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "BACKEND",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["PROBLEM_SOLVING", "COMMUNICATION"],
            "tech_stacks": ["NODEJS", "INFLUXDB"],
            "closing_days": 20,
        },
        {
            "title": "Field Research Intern",
            "description": "<p>Bergabunglah sebagai <strong>Field Research Intern</strong> untuk terjun langsung ke lapangan dan mengumpulkan data dari petani mitra kami.</p><ul><li>Survei dan wawancara petani mitra</li><li>Pengambilan data pertumbuhan tanaman</li><li>Analisis kebutuhan pengguna di lapangan</li><li>Menyusun laporan riset mingguan</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "RESEARCH",
            "lifecycle": "closed",
            "moderation": "approved",
            "skills": ["COMMUNICATION", "ANALYTICAL_THINKING"],
            "tech_stacks": ["MS_EXCEL", "GOOGLE_FORMS"],
            "closing_days": -8,
        },
    ],
    "Logistik Pintar": [
        {
            "title": "Fullstack Developer Intern",
            "description": "<p>Kami mencari <strong>Fullstack Developer Intern</strong> untuk membantu mengembangkan platform manajemen logistik kami yang melayani ratusan mitra pengiriman.</p><ul><li>Pengembangan fitur frontend menggunakan Vue.js</li><li>Pengembangan endpoint backend menggunakan Laravel</li><li>Integrasi third-party API (kurir, maps)</li><li>Testing dan debugging fitur end-to-end</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "FULLSTACK",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["PROBLEM_SOLVING", "COMMUNICATION"],
            "tech_stacks": ["VUE_JS", "LARAVEL"],
            "closing_days": 30,
        },
        {
            "title": "Operations Analyst Intern",
            "description": "<p>Bergabunglah sebagai <strong>Operations Analyst Intern</strong> dan optimalkan efisiensi jaringan logistik kami menggunakan data.</p><ul><li>Analisis data pengiriman dan rute optimal</li><li>Pembuatan dashboard KPI operasional</li><li>Identifikasi bottleneck dan rekomendasi solusi</li><li>Simulasi skenario optimasi menggunakan spreadsheet/Python</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "DATA",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["ANALYTICAL_THINKING", "PROBLEM_SOLVING"],
            "tech_stacks": ["PYTHON", "TABLEAU"],
            "closing_days": 25,
        },
        {
            "title": "Mobile Developer Intern â€“ React Native",
            "description": "<p>Kami membuka posisi <strong>React Native Developer Intern</strong> untuk mengembangkan aplikasi driver dan merchant platform kami.</p><ul><li>Pengembangan fitur aplikasi driver (tracking, navigasi)</li><li>Integrasi Google Maps SDK</li><li>Push notification dan real-time update</li><li>Optimasi performa aplikasi</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "MOBILE",
            "lifecycle": "active",
            "moderation": "pending",
            "skills": ["UI_IMPLEMENTATION", "PROBLEM_SOLVING"],
            "tech_stacks": ["REACT_NATIVE", "NODEJS"],
            "closing_days": 22,
        },
        {
            "title": "Business Development Intern",
            "description": "<p>Jadilah <strong>Business Development Intern</strong> kami dan bantu ekspansi jaringan mitra pengiriman dan merchant di kota-kota baru.</p><ul><li>Riset dan prospek mitra pengiriman baru</li><li>Presentasi proposal kerjasama</li><li>Onboarding mitra baru ke platform</li><li>Monitoring KPI mitra aktif</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "BUSINESS",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["COMMUNICATION", "ANALYTICAL_THINKING"],
            "tech_stacks": ["MS_EXCEL", "GOOGLE_WORKSPACE"],
            "closing_days": 20,
        },
        {
            "title": "GIS & Routing Intern",
            "description": "<p>Kami mencari <strong>GIS & Routing Intern</strong> untuk mengembangkan algoritma optimasi rute pengiriman kami menggunakan data geospasial.</p><ul><li>Analisis data geospasial menggunakan QGIS</li><li>Implementasi algoritma routing (OSRM, Vroom)</li><li>Visualisasi zona pengiriman dan coverage</li><li>Evaluasi akurasi prediksi ETA</li></ul>",
            "type": "Hybrid",
            "duration": 4,
            "tech_category": "DATA",
            "lifecycle": "closed",
            "moderation": "approved",
            "skills": ["ANALYTICAL_THINKING", "PROBLEM_SOLVING"],
            "tech_stacks": ["PYTHON", "POSTGRESQL"],
            "closing_days": -12,
        },
    ],
    "Edukasi Teknologi Indonesia": [
        {
            "title": "Instructional Designer Intern",
            "description": "<p>Kami mencari <strong>Instructional Designer Intern</strong> yang kreatif untuk mendesain kurikulum dan konten pembelajaran digital yang menarik.</p><ul><li>Merancang learning path dan kurikulum kursus</li><li>Membuat storyboard materi video pembelajaran</li><li>Menulis skrip dan modul materi belajar</li><li>Evaluasi efektivitas konten bersama tim pedagogi</li></ul>",
            "type": "Remote",
            "duration": 3,
            "tech_category": "CONTENT",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["COMMUNICATION", "CREATIVITY"],
            "tech_stacks": ["CANVA", "ARTICULATE"],
            "closing_days": 30,
        },
        {
            "title": "Frontend Developer Intern â€“ EdTech Platform",
            "description": "<p>Bergabunglah sebagai <strong>Frontend Developer Intern</strong> dan bangun fitur interaktif di platform e-learning kami yang digunakan ratusan ribu pelajar.</p><ul><li>Pengembangan komponen React interaktif (quiz, video player)</li><li>Implementasi fitur gamifikasi (poin, badge, leaderboard)</li><li>Optimasi aksesibilitas dan performa</li><li>Integrasi dengan LMS backend</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "FRONTEND",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["UI_IMPLEMENTATION", "PROBLEM_SOLVING"],
            "tech_stacks": ["REACT_JS", "TYPESCRIPT"],
            "closing_days": 25,
        },
        {
            "title": "Community Manager Intern",
            "description": "<p>Kami membuka posisi <strong>Community Manager Intern</strong> untuk mengelola dan mengembangkan komunitas pelajar dan mentor platform kami.</p><ul><li>Moderasi forum diskusi dan community Discord</li><li>Merancang program engagement komunitas</li><li>Koordinasi acara live session dan webinar</li><li>Analisis sentimen dan feedback komunitas</li></ul>",
            "type": "Remote",
            "duration": 3,
            "tech_category": "COMMUNITY",
            "lifecycle": "active",
            "moderation": "pending",
            "skills": ["COMMUNICATION", "CREATIVITY"],
            "tech_stacks": ["DISCORD", "NOTION"],
            "closing_days": 20,
        },
        {
            "title": "Backend Developer Intern â€“ LMS",
            "description": "<p>Jadilah <strong>Backend Developer Intern</strong> kami dan kembangkan fitur LMS (Learning Management System) yang mendukung jutaan sesi belajar.</p><ul><li>Pengembangan API enrollment, progress tracking, dan sertifikasi</li><li>Optimasi query database untuk skala besar</li><li>Integrasi dengan payment gateway</li><li>Unit testing dan dokumentasi API</li></ul>",
            "type": "Hybrid",
            "duration": 4,
            "tech_category": "BACKEND",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["PROBLEM_SOLVING", "ANALYTICAL_THINKING"],
            "tech_stacks": ["NODEJS", "POSTGRESQL"],
            "closing_days": 35,
        },
        {
            "title": "AI Tutor Developer Intern",
            "description": "<p>Bergabunglah sebagai <strong>AI Tutor Developer Intern</strong> dan bantu kami membangun asisten belajar berbasis AI yang menjawab pertanyaan pelajar 24/7.</p><ul><li>Fine-tuning model LLM untuk domain pendidikan</li><li>Pengembangan chatbot dengan RAG (Retrieval Augmented Generation)</li><li>Evaluasi akurasi dan keamanan respons AI</li><li>Integrasi ke platform web dan mobile</li></ul>",
            "type": "Remote",
            "duration": 4,
            "tech_category": "AI_ML",
            "lifecycle": "closed",
            "moderation": "approved",
            "skills": ["PROBLEM_SOLVING", "ANALYTICAL_THINKING"],
            "tech_stacks": ["PYTHON", "OPENAI_API"],
            "closing_days": -4,
        },
    ],
    "HealthBridge Indonesia": [
        {
            "title": "Mobile Developer Intern â€“ iOS",
            "description": "<p>Kami mencari <strong>iOS Developer Intern</strong> yang bersemangat untuk mengembangkan aplikasi telemedisin kami di platform Apple.</p><ul><li>Pengembangan fitur konsultasi dokter menggunakan SwiftUI</li><li>Integrasi video call SDK (WebRTC)</li><li>Keamanan data kesehatan (HealthKit, enkripsi)</li><li>Pengujian di berbagai perangkat iOS</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "MOBILE",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["UI_IMPLEMENTATION", "PROBLEM_SOLVING"],
            "tech_stacks": ["SWIFT", "XCODE"],
            "closing_days": 30,
        },
        {
            "title": "Data Analyst â€“ Health Data Intern",
            "description": "<p>Bergabunglah sebagai <strong>Health Data Analyst Intern</strong> dan bantu kami mengolah data kesehatan untuk meningkatkan kualitas layanan telemedisin.</p><ul><li>Analisis data konsultasi dan outcome pasien</li><li>Pembuatan dashboard KPI layanan kesehatan</li><li>Identifikasi pola penyakit dan tren kesehatan</li><li>Pelaporan insight kepada tim medis dan manajemen</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "DATA",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["ANALYTICAL_THINKING", "COMMUNICATION"],
            "tech_stacks": ["PYTHON", "TABLEAU"],
            "closing_days": 28,
        },
        {
            "title": "Backend Developer Intern â€“ Healthcare API",
            "description": "<p>Kami membuka posisi <strong>Backend Developer Intern</strong> untuk mengembangkan API layanan kesehatan yang aman, andal, dan sesuai standar FHIR.</p><ul><li>Pengembangan FHIR-compliant REST API</li><li>Implementasi keamanan data medis (HIPAA-aware)</li><li>Integrasi dengan sistem RS dan laboratorium</li><li>Unit testing dan load testing API</li></ul>",
            "type": "WFO",
            "duration": 4,
            "tech_category": "BACKEND",
            "lifecycle": "active",
            "moderation": "pending",
            "skills": ["PROBLEM_SOLVING", "ANALYTICAL_THINKING"],
            "tech_stacks": ["JAVA_SPRING", "POSTGRESQL"],
            "closing_days": 35,
        },
        {
            "title": "Medical Content Writer Intern",
            "description": "<p>Jadilah <strong>Medical Content Writer Intern</strong> kami dan produksi konten kesehatan yang akurat dan mudah dipahami oleh masyarakat luas.</p><ul><li>Menulis artikel kesehatan berdasarkan evidence-based medicine</li><li>Berkolaborasi dengan dokter untuk review medis</li><li>SEO optimization konten kesehatan</li><li>Manajemen kalender konten blog dan media sosial</li></ul>",
            "type": "Remote",
            "duration": 3,
            "tech_category": "CONTENT",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["COMMUNICATION", "ANALYTICAL_THINKING"],
            "tech_stacks": ["WORDPRESS", "GOOGLE_ANALYTICS"],
            "closing_days": 22,
        },
        {
            "title": "UX Researcher Intern",
            "description": "<p>Kami mencari <strong>UX Researcher Intern</strong> untuk melakukan riset pengguna dan memastikan produk kami benar-benar memenuhi kebutuhan pasien dan dokter.</p><ul><li>Merancang dan menjalankan user interview</li><li>Analisis usability testing dengan pasien dan nakes</li><li>Menyusun laporan insight pengguna</li><li>Berkolaborasi dengan tim produk dan desain</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "DESIGN",
            "lifecycle": "closed",
            "moderation": "approved",
            "skills": ["COMMUNICATION", "ANALYTICAL_THINKING"],
            "tech_stacks": ["FIGMA", "NOTION"],
            "closing_days": -6,
        },
    ],
    "Archipelago Game Studio": [
        {
            "title": "Game Developer Intern â€“ Unity",
            "description": "<p>Kami mencari <strong>Unity Game Developer Intern</strong> yang passionate untuk turut membangun game mobile bertema budaya Nusantara bersama kami.</p><ul><li>Implementasi gameplay mechanics menggunakan Unity C#</li><li>Integrasi aset seni dan animasi dari tim art</li><li>Optimasi performa game untuk perangkat mid-range</li><li>Playtesting dan bug fixing</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "GAMEDEV",
            "lifecycle": "active",
            "moderation": "pending",
            "skills": ["PROBLEM_SOLVING", "CREATIVITY"],
            "tech_stacks": ["UNITY", "CSHARP"],
            "closing_days": 30,
        },
        {
            "title": "2D Game Artist Intern",
            "description": "<p>Bergabunglah sebagai <strong>2D Game Artist Intern</strong> dan ciptakan visual yang memukau terinspirasi dari budaya dan mitologi Nusantara.</p><ul><li>Membuat karakter, environment, dan UI sprite 2D</li><li>Animasi karakter menggunakan Spine atau Unity Animator</li><li>Konsistensi visual sesuai art style guide</li><li>Berkolaborasi dengan game designer dan programmer</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "DESIGN",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["CREATIVITY", "COMMUNICATION"],
            "tech_stacks": ["ADOBE_PHOTOSHOP", "SPINE"],
            "closing_days": 25,
        },
        {
            "title": "Game Designer Intern",
            "description": "<p>Kami membuka posisi <strong>Game Designer Intern</strong> untuk merancang level, sistem gameplay, dan narasi yang imersif pada proyek game kami.</p><ul><li>Merancang level dan puzzle gameplay</li><li>Menulis game design document (GDD)</li><li>Playtesting dan iterasi desain berdasarkan feedback</li><li>Riset referensi game dan budaya lokal</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "GAMEDEV",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["CREATIVITY", "ANALYTICAL_THINKING"],
            "tech_stacks": ["NOTION", "FIGMA"],
            "closing_days": 20,
        },
        {
            "title": "Narrative Writer Intern",
            "description": "<p>Jadilah <strong>Narrative Writer Intern</strong> kami dan tulis cerita yang kaya dan penuh dengan referensi budaya Nusantara untuk game kami.</p><ul><li>Menulis skrip dialog dan narasi karakter</li><li>Riset folklor, mitologi, dan sejarah Nusantara</li><li>Berkolaborasi dengan game designer untuk integrasi cerita</li><li>Proofreading dan localization assistance</li></ul>",
            "type": "Remote",
            "duration": 3,
            "tech_category": "CONTENT",
            "lifecycle": "active",
            "moderation": "pending",
            "skills": ["COMMUNICATION", "CREATIVITY"],
            "tech_stacks": ["NOTION", "GOOGLE_WORKSPACE"],
            "closing_days": 18,
        },
        {
            "title": "QA Tester Intern â€“ Mobile Games",
            "description": "<p>Kami mencari <strong>QA Tester Intern</strong> yang teliti untuk memastikan setiap fitur dan level game kami berjalan sempurna sebelum dirilis.</p><ul><li>Menyusun dan menjalankan test case gameplay</li><li>Testing di berbagai perangkat Android & iOS</li><li>Melaporkan dan melacak bug di Jira</li><li>Regression testing setelah setiap build baru</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "QA",
            "lifecycle": "closed",
            "moderation": "approved",
            "skills": ["ANALYTICAL_THINKING", "PROBLEM_SOLVING"],
            "tech_stacks": ["JIRA", "ANDROID_STUDIO"],
            "closing_days": -15,
        },
    ],
    "CyberSec Indonesia": [
        {
            "title": "Penetration Testing Intern",
            "description": "<p>Bergabunglah sebagai <strong>Penetration Testing Intern</strong> dan pelajari cara mengidentifikasi dan mengeksploitasi kerentanan sistem secara etis.</p><ul><li>Melakukan vulnerability assessment web aplikasi</li><li>Network scanning dan enumeration</li><li>Menyusun laporan temuan kerentanan</li><li>Simulasi serangan phishing yang terkontrol</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "SECURITY",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["PROBLEM_SOLVING", "ANALYTICAL_THINKING"],
            "tech_stacks": ["KALI_LINUX", "BURPSUITE"],
            "closing_days": 30,
        },
        {
            "title": "SOC Analyst Intern",
            "description": "<p>Kami membuka posisi <strong>SOC Analyst Intern</strong> untuk memantau dan merespons insiden keamanan siber di Security Operations Center kami.</p><ul><li>Monitoring alert keamanan menggunakan SIEM (Splunk/ELK)</li><li>Triase dan investigasi insiden keamanan Level 1</li><li>Analisis log dan identifikasi anomali</li><li>Dokumentasi playbook penanganan insiden</li></ul>",
            "type": "WFO",
            "duration": 3,
            "tech_category": "SECURITY",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["ANALYTICAL_THINKING", "PROBLEM_SOLVING"],
            "tech_stacks": ["SPLUNK", "WIRESHARK"],
            "closing_days": 25,
        },
        {
            "title": "Malware Analysis Intern",
            "description": "<p>Jadilah <strong>Malware Analysis Intern</strong> kami dan pelajari teknik analisis malware statis dan dinamis di lingkungan sandbox yang aman.</p><ul><li>Analisis statis binary menggunakan IDA Pro/Ghidra</li><li>Dynamic analysis di sandbox environment</li><li>Menyusun IOC (Indicator of Compromise)</li><li>Laporan threat intelligence sederhana</li></ul>",
            "type": "WFO",
            "duration": 4,
            "tech_category": "SECURITY",
            "lifecycle": "active",
            "moderation": "pending",
            "skills": ["ANALYTICAL_THINKING", "PROBLEM_SOLVING"],
            "tech_stacks": ["GHIDRA", "PYTHON"],
            "closing_days": 35,
        },
        {
            "title": "Cloud Security Intern",
            "description": "<p>Bergabunglah sebagai <strong>Cloud Security Intern</strong> untuk membantu klien kami mengamankan infrastruktur cloud mereka sesuai standar CIS Benchmark.</p><ul><li>Audit konfigurasi AWS/GCP berdasarkan CIS Benchmark</li><li>Implementasi security group dan IAM policy review</li><li>Monitoring cloud security posture</li><li>Dokumentasi temuan dan rekomendasi mitigasi</li></ul>",
            "type": "Hybrid",
            "duration": 3,
            "tech_category": "SECURITY",
            "lifecycle": "active",
            "moderation": "approved",
            "skills": ["ANALYTICAL_THINKING", "PROBLEM_SOLVING"],
            "tech_stacks": ["AWS", "TERRAFORM"],
            "closing_days": 28,
        },
        {
            "title": "Security Awareness Intern",
            "description": "<p>Kami mencari <strong>Security Awareness Intern</strong> untuk membantu merancang dan mengeksekusi program edukasi keamanan siber bagi klien korporat kami.</p><ul><li>Membuat materi pelatihan keamanan siber</li><li>Menyusun simulasi phishing awareness</li><li>Presentasi ke karyawan klien</li><li>Mengukur efektivitas program awareness</li></ul>",
            "type": "Remote",
            "duration": 3,
            "tech_category": "SECURITY",
            "lifecycle": "closed",
            "moderation": "approved",
            "skills": ["COMMUNICATION", "CREATIVITY"],
            "tech_stacks": ["CANVA", "MS_POWERPOINT"],
            "closing_days": -9,
        },
    ],
}

# â”€â”€ Skill & TechStack master definitions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

SKILLS_MASTER = {
    "PROBLEM_SOLVING":    "Problem Solving",
    "COMMUNICATION":      "Communication",
    "ANALYTICAL_THINKING":"Analytical Thinking",
    "UI_IMPLEMENTATION":  "UI Implementation",
    "CREATIVITY":         "Creativity",
}

TECH_STACKS_MASTER = {
    "JAVA_SPRING":     "Java Spring Boot",
    "POSTGRESQL":      "PostgreSQL",
    "MYSQL":           "MySQL",
    "REACT_JS":        "React.js",
    "TAILWIND_CSS":    "Tailwind CSS",
    "TYPESCRIPT":      "TypeScript",
    "SELENIUM":        "Selenium",
    "POSTMAN":         "Postman",
    "PYTHON":          "Python",
    "TABLEAU":         "Tableau",
    "DOCKER":          "Docker",
    "GITLAB_CI":       "GitLab CI",
    "AWS":             "AWS",
    "TERRAFORM":       "Terraform",
    "KUBERNETES":      "Kubernetes",
    "PROMETHEUS":      "Prometheus",
    "GOLANG":          "Go",
    "KAFKA":           "Apache Kafka",
    "MARKDOWN":        "Markdown",
    "CONFLUENCE":      "Confluence",
    "FIGMA":           "Figma",
    "ADOBE_XD":        "Adobe XD",
    "CANVA":           "Canva",
    "META_ADS":        "Meta Ads Manager",
    "GOOGLE_ANALYTICS":"Google Analytics",
    "SEMRUSH":         "SEMrush",
    "ADOBE_PREMIERE":  "Adobe Premiere Pro",
    "CAPCUT":          "CapCut",
    "GOOGLE_ADS":      "Google Ads",
    "KOTLIN":          "Kotlin",
    "ANDROID_STUDIO":  "Android Studio",
    "AIRFLOW":         "Apache Airflow",
    "SCIKIT_LEARN":    "Scikit-learn",
    "MIXPANEL":        "Mixpanel",
    "MS_EXCEL":        "Microsoft Excel",
    "VUE_JS":          "Vue.js",
    "LARAVEL":         "Laravel",
    "REACT_NATIVE":    "React Native",
    "NODEJS":          "Node.js",
    "GOOGLE_WORKSPACE":"Google Workspace",
    "INFLUXDB":        "InfluxDB",
    "ARDUINO":         "Arduino",
    "MQTT":            "MQTT",
    "FLUTTER":         "Flutter",
    "DART":            "Dart",
    "GOOGLE_FORMS":    "Google Forms",
    "ARTICULATE":      "Articulate 360",
    "DISCORD":         "Discord",
    "NOTION":          "Notion",
    "OPENAI_API":      "OpenAI API",
    "WORDPRESS":       "WordPress",
    "SWIFT":           "Swift",
    "XCODE":           "Xcode",
    "UNITY":           "Unity",
    "CSHARP":          "C#",
    "ADOBE_PHOTOSHOP": "Adobe Photoshop",
    "SPINE":           "Spine 2D",
    "JIRA":            "Jira",
    "MS_POWERPOINT":   "Microsoft PowerPoint",
    "KALI_LINUX":      "Kali Linux",
    "BURPSUITE":       "Burp Suite",
    "SPLUNK":          "Splunk",
    "WIRESHARK":       "Wireshark",
    "GHIDRA":          "Ghidra",
    "GOOGLE_WORKSPACE":"Google Workspace",
}

# TechCategory codes used in templates
TECH_CATEGORIES_MASTER = {
    "BACKEND":         "Backend Development",
    "FRONTEND":        "Frontend Development",
    "FULLSTACK":       "Fullstack Development",
    "MOBILE":          "Mobile Development",
    "DATA":            "Data & Analytics",
    "AI_ML":           "AI & Machine Learning",
    "DEVOPS":          "DevOps & Cloud",
    "CLOUD":           "Cloud Computing",
    "QA":              "Quality Assurance",
    "DESIGN":          "UI/UX Design",
    "MARKETING":       "Digital Marketing",
    "CONTENT":         "Content Creation",
    "SECURITY":        "Cybersecurity",
    "IOT":             "Internet of Things",
    "GAMEDEV":         "Game Development",
    "FINANCE":         "Finance & Compliance",
    "PRODUCT":         "Product Management",
    "BUSINESS":        "Business Development",
    "RESEARCH":        "Research",
    "TECHNICAL_WRITING":"Technical Writing",
    "COMMUNITY":       "Community Management",
}

# City â†’ location code mapping
LOCATIONS_MASTER = {
    "Jakarta":    ("JKT", "DKI Jakarta"),
    "Bandung":    ("BDG", "Jawa Barat"),
    "Yogyakarta": ("YOG", "DI Yogyakarta"),
    "Surabaya":   ("SBY", "Jawa Timur"),
    "Semarang":   ("SMG", "Jawa Tengah"),
    "Bali":       ("DPS", "Bali"),
}

# â”€â”€ Main seed logic â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

with app.app_context():
    print("=" * 60)
    print("  InternLink Company Seed  ")
    print("=" * 60)

    # â”€â”€ 1. Ensure UserAccountStatus â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    active_status, _ = get_or_create(
        UserAccountStatus, status_code='active',
        defaults={'status_name': 'Active'}
    )
    db.session.commit()

    # â”€â”€ 2. Ensure CompanyVerificationStatus â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ver_statuses = {}
    for code, name in [('verified', 'Verified'), ('pending', 'Pending'), ('rejected', 'Rejected')]:
        obj, _ = get_or_create(
            CompanyVerificationStatus, status_code=code,
            defaults={'status_name': name}
        )
        ver_statuses[code] = obj
    db.session.commit()

    # â”€â”€ 3. Ensure InternshipLifecycleStatus â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lifecycle_statuses = {}
    for code, name in [('active', 'Active'), ('closed', 'Closed'), ('draft', 'Draft')]:
        obj, _ = get_or_create(
            InternshipLifecycleStatus, status_code=code,
            defaults={'status_name': name}
        )
        lifecycle_statuses[code] = obj
    db.session.commit()

    # â”€â”€ 4. Ensure InternshipModerationStatus â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    mod_statuses = {}
    for code, name in [('approved', 'Approved'), ('pending', 'Pending Review'), ('rejected', 'Rejected')]:
        obj, _ = get_or_create(
            InternshipModerationStatus, status_code=code,
            defaults={'status_name': name}
        )
        mod_statuses[code] = obj
    db.session.commit()

    # â”€â”€ 5. Ensure Locations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    locations = {}
    for city, (code, region) in LOCATIONS_MASTER.items():
        obj, created = get_or_create(
            Location, location_code=code,
            defaults={'city': city, 'region': region, 'country': 'Indonesia'}
        )
        locations[city] = obj
        if created:
            print(f"  [+] Location: {city}")
    db.session.commit()

    # â”€â”€ 6. Ensure TechnologyCategories â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    tech_categories = {}
    for code, name in TECH_CATEGORIES_MASTER.items():
        obj, created = get_or_create(
            TechnologyCategory, category_code=code,
            defaults={'category_name': name}
        )
        tech_categories[code] = obj
        if created:
            print(f"  [+] TechCategory: {name}")
    db.session.commit()

    # â”€â”€ 7. Ensure Skills â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    skills_map = {}
    for code, name in SKILLS_MASTER.items():
        obj, created = get_or_create(
            Skill, skill_code=code,
            defaults={'skill_name': name}
        )
        skills_map[code] = obj
        if created:
            print(f"  [+] Skill: {name}")
    db.session.commit()

    # â”€â”€ 8. Ensure TechStackItems â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    tech_stacks_map = {}
    for code, name in TECH_STACKS_MASTER.items():
        obj, created = get_or_create(
            TechStackItem, tech_stack_code=code,
            defaults={'tech_stack_name': name}
        )
        tech_stacks_map[code] = obj
        if created:
            print(f"  [+] TechStack: {name}")
    db.session.commit()
    print()

    # â”€â”€ 9. Seed Companies + Internships â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    for idx, co_data in enumerate(COMPANIES_DATA, start=1):
        print(f"[{idx:02d}/10] Perusahaan: {co_data['company_name']}")

        # Create or retrieve UserAccount
        user, u_created = get_or_create(
            UserAccount, email=co_data['email'],
            defaults={
                'role': 'company',
                'password_hash': generate_password_hash('Password123!'),
                'display_name': co_data['display_name'],
                'account_status_id': active_status.id,
            }
        )
        if not u_created:
            print(f"       â†’ Akun sudah ada, skip buat ulang.")
        db.session.flush()

        # Create or retrieve CompanyProfile
        loc = locations.get(co_data['city'], list(locations.values())[0])
        company, c_created = get_or_create(
            CompanyProfile, user_account_id=user.id,
            defaults={
                'company_name': co_data['company_name'],
                'company_description': co_data['description'],
                'industry_category': co_data['industry'],
                'company_size': co_data['size'],
                'founding_year': co_data['year'],
                'address_line': co_data['address'],
                'location_id': loc.id,
                'website_url': co_data['website'],
            }
        )
        db.session.flush()

        # Add CompanyVerification record if not already exists
        existing_ver = CompanyVerification.query.filter_by(
            company_profile_id=company.id
        ).first()
        if not existing_ver:
            ver_status_obj = ver_statuses.get(co_data['verification'], ver_statuses['pending'])
            verification = CompanyVerification(
                company_profile_id=company.id,
                verification_status_id=ver_status_obj.id,
                admin_note=f"Seeded automatically. Status: {co_data['verification']}.",
                verified_at=datetime.utcnow() if co_data['verification'] == 'verified' else None,
            )
            db.session.add(verification)
            db.session.flush()
            print(f"       â†’ Verifikasi: {co_data['verification']}")

        # Create internships for this company
        internship_list = INTERNSHIP_TEMPLATES.get(co_data['company_name'], [])
        created_count = 0
        skipped_count = 0
        for tmpl in internship_list:
            existing_int = Internship.query.filter_by(
                company_profile_id=company.id,
                internship_title=tmpl['title'],
                deleted_at=None
            ).first()
            if existing_int:
                skipped_count += 1
                continue

            closing = datetime.utcnow() + timedelta(days=tmpl['closing_days'])
            lc_status = lifecycle_statuses.get(tmpl['lifecycle'], lifecycle_statuses['active'])
            md_status = mod_statuses.get(tmpl['moderation'], mod_statuses['pending'])
            tc = tech_categories.get(tmpl['tech_category'], list(tech_categories.values())[0])

            internship = Internship(
                company_profile_id=company.id,
                technology_category_id=tc.id,
                location_id=loc.id,
                internship_title=tmpl['title'],
                internship_description=tmpl['description'],
                internship_type=tmpl['type'],
                duration_months=tmpl['duration'],
                lifecycle_status_id=lc_status.id,
                moderation_status_id=md_status.id,
                closing_at=closing,
            )
            db.session.add(internship)
            db.session.flush()

            # Required Skills
            for skill_code in tmpl.get('skills', []):
                skill_obj = skills_map.get(skill_code)
                if skill_obj:
                    req_skill = InternshipRequiredSkill(
                        internship_id=internship.id,
                        skill_id=skill_obj.id,
                        required_level='Intermediate',
                    )
                    db.session.add(req_skill)

            # Required Tech Stacks
            for ts_code in tmpl.get('tech_stacks', []):
                ts_obj = tech_stacks_map.get(ts_code)
                if ts_obj:
                    req_ts = InternshipRequiredTechStackItem(
                        internship_id=internship.id,
                        tech_stack_item_id=ts_obj.id,
                        required_level='Basic',
                    )
                    db.session.add(req_ts)

            created_count += 1

        db.session.commit()
        print(f"       â†’ Lowongan dibuat: {created_count} | Di-skip (sudah ada): {skipped_count}")

    print()
    print("=" * 60)
    print("  Seed selesai! ")
    print("  10 perusahaan + 50 lowongan telah berhasil di-seed.")
    print("  Password semua akun: Password123!")
    print("=" * 60)

