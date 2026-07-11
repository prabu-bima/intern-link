# InternLink

Web-based Internship Recruitment Platform for Technology Students.

## Setup Project (Development)

Berikut adalah langkah-langkah untuk menyiapkan proyek setelah Anda melakukan *clone* dari repository.

### 1. Persyaratan Sistem
- Python 3.10+
- Node.js & npm (untuk Tailwind CSS)
- Git

### 2. Setup Lingkungan Python (Virtual Environment)
Buka terminal di root direktori proyek (`internlink/`) dan jalankan:
```bash
# Membuat virtual environment
python -m venv venv

# Mengaktifkan virtual environment (Windows)
.\venv\Scripts\activate

# Mengaktifkan virtual environment (Mac/Linux)
source venv/bin/activate
```

### 3. Install Dependensi Python
```bash
pip install -r requirements.txt
```

### 4. Install Dependensi Node.js (Tailwind CSS)
```bash
npm install
```

### 5. Pengaturan Environment Variables
Duplikat file `.env.example` menjadi `.env` (jika belum ada) dan sesuaikan nilainya:
```env
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key

# Supabase
DATABASE_URL=postgresql://postgres.xxx:password@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-supabase-key
```

### 6. Inisialisasi Database (Migrasi)
Karena migrasi awal (`migrations/` folder) sudah ada, jalankan perintah berikut untuk mengaplikasikan tabel-tabel ke dalam database Supabase Anda:
```bash
flask db upgrade
```

### 7. Build CSS (Tailwind)
Jalankan perintah ini untuk membangun file `output.css` dari `input.css`:
```bash
npm run build:css

# (Opsional) Jika Anda sedang mengembangkan frontend, jalankan perintah ini di terminal terpisah:
npm run watch:css
```

### 8. Menjalankan Aplikasi
```bash
python run.py
```
Aplikasi akan berjalan di `http://127.0.0.1:5000/`.

### 9. Mengupdate data lookups
```bash
venv\Scripts\python scripts\seed_lookups.py
```
