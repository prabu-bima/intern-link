from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, URLField
from wtforms.validators import DataRequired, Email, Length, Optional, URL

class PersonalInformationForm(FlaskForm):
    full_name = StringField('Nama Lengkap', validators=[DataRequired(), Length(max=100)])
    email = StringField('Alamat Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone_number = StringField('Nomor HP', validators=[Optional(), Length(max=20)])
    date_of_birth = DateField('Tanggal Lahir', validators=[Optional()])
    gender = SelectField('Jenis Kelamin', choices=[('', 'Pilih Jenis Kelamin'), ('Laki-laki', 'Laki-laki'), ('Perempuan', 'Perempuan')], validators=[Optional()])
    bio = TextAreaField('Bio / Ringkasan Profesional', validators=[Optional(), Length(max=1000)])

class EducationForm(FlaskForm):
    institution_name = StringField('Nama Institusi / Universitas', validators=[DataRequired(), Length(max=200)])
    field_of_study = StringField('Program Studi / Jurusan', validators=[DataRequired(), Length(max=100)])
    degree_name = StringField('Gelar', validators=[DataRequired(), Length(max=100)])
    start_date = DateField('Tanggal Mulai', validators=[DataRequired()])
    end_date = DateField('Tanggal Lulus (Atau Perkiraan)', validators=[Optional()])
    grade = StringField('IPK / Nilai', validators=[Optional(), Length(max=20)])

class StudentSkillForm(FlaskForm):
    skill_id = SelectField('Keahlian', coerce=int, validators=[DataRequired()])
    proficiency_level = SelectField('Tingkat Penguasaan', choices=[
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced')
    ], validators=[DataRequired()])

class StudentTechStackItemForm(FlaskForm):
    tech_stack_item_id = SelectField('Tech Stack', coerce=int, validators=[DataRequired()])
    proficiency_level = SelectField('Tingkat Penguasaan', choices=[
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced')
    ], validators=[DataRequired()])

class ExperienceForm(FlaskForm):
    organization_name = StringField('Nama Perusahaan / Organisasi', validators=[DataRequired(), Length(max=200)])
    title = StringField('Jabatan / Posisi', validators=[DataRequired(), Length(max=100)])
    start_date = DateField('Tanggal Mulai', validators=[DataRequired()])
    end_date = DateField('Tanggal Selesai', validators=[Optional()])
    description = TextAreaField('Deskripsi Pekerjaan', validators=[Optional(), Length(max=1000)])

class OrganizationForm(FlaskForm):
    organization_name = StringField('Nama Organisasi', validators=[DataRequired(), Length(max=200)])
    role_title = StringField('Jabatan / Peran', validators=[DataRequired(), Length(max=100)])
    start_date = DateField('Tanggal Mulai', validators=[DataRequired()])
    end_date = DateField('Tanggal Selesai', validators=[Optional()])
    description = TextAreaField('Deskripsi Kegiatan', validators=[Optional(), Length(max=1000)])

class CertificateForm(FlaskForm):
    certificate_title = StringField('Nama Sertifikat', validators=[DataRequired(), Length(max=200)])
    issuer = StringField('Lembaga Penerbit', validators=[DataRequired(), Length(max=200)])
    issue_date = DateField('Tanggal Diterbitkan', validators=[DataRequired()])
    credential_url = URLField('URL Kredensial', validators=[Optional(), URL(), Length(max=500)])
    certificate_file = FileField('File Sertifikat (PDF/Gambar)', validators=[
        Optional(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Hanya file PDF, JPG, atau PNG yang diizinkan.')
    ])

class PortfolioForm(FlaskForm):
    portfolio_title = StringField('Judul Portofolio / Proyek', validators=[DataRequired(), Length(max=200)])
    portfolio_url = URLField('Tautan Portofolio', validators=[Optional(), URL(), Length(max=255)])
    description = TextAreaField('Deskripsi Proyek', validators=[Optional(), Length(max=1000)])
