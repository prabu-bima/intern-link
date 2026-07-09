from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.identity import UserAccount

class StudentRegistrationForm(FlaskForm):
    full_name = StringField('Nama Lengkap', validators=[DataRequired(message="Nama lengkap wajib diisi.")])
    university_name = StringField('Universitas', validators=[DataRequired(message="Universitas wajib diisi.")])
    major = StringField('Program Studi', validators=[DataRequired(message="Program studi wajib diisi.")])
    
    email = StringField('Email', validators=[
        DataRequired(message="Email wajib diisi."),
        Email(message="Format email tidak valid.")
    ])
    
    password = PasswordField('Kata Sandi', validators=[
        DataRequired(message="Kata sandi wajib diisi."),
        Length(min=8, message="Kata sandi minimal 8 karakter.")
    ])
    
    confirm_password = PasswordField('Konfirmasi Kata Sandi', validators=[
        DataRequired(message="Konfirmasi kata sandi wajib diisi."),
        EqualTo('password', message="Kata sandi tidak cocok.")
    ])
    
    submit = SubmitField('Daftar sebagai Mahasiswa')

    def validate_email(self, email):
        user = UserAccount.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email sudah terdaftar. Silakan gunakan email lain atau masuk ke akun Anda.')

class CompanyRegistrationForm(FlaskForm):
    company_name = StringField('Nama Perusahaan', validators=[DataRequired(message="Nama perusahaan wajib diisi.")])
    
    email = StringField('Email Perusahaan', validators=[
        DataRequired(message="Email wajib diisi."),
        Email(message="Format email tidak valid.")
    ])
    
    password = PasswordField('Kata Sandi', validators=[
        DataRequired(message="Kata sandi wajib diisi."),
        Length(min=8, message="Kata sandi minimal 8 karakter.")
    ])
    
    confirm_password = PasswordField('Konfirmasi Kata Sandi', validators=[
        DataRequired(message="Konfirmasi kata sandi wajib diisi."),
        EqualTo('password', message="Kata sandi tidak cocok.")
    ])
    
    submit = SubmitField('Daftar sebagai Perusahaan')

    def validate_email(self, email):
        user = UserAccount.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email sudah terdaftar. Silakan gunakan email lain atau masuk ke akun Anda.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="Email wajib diisi."),
        Email(message="Format email tidak valid.")
    ])
    
    password = PasswordField('Kata Sandi', validators=[
        DataRequired(message="Kata sandi wajib diisi.")
    ])
    
    remember_me = BooleanField('Ingat Saya')
    submit = SubmitField('Masuk')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="Email wajib diisi."),
        Email(message="Format email tidak valid.")
    ])
    submit = SubmitField('Kirim Tautan Reset')

    def validate_email(self, email):
        user = UserAccount.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('Tidak ada akun yang terdaftar dengan email ini.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Kata Sandi Baru', validators=[
        DataRequired(message="Kata sandi baru wajib diisi."),
        Length(min=8, message="Kata sandi minimal 8 karakter.")
    ])
    
    confirm_password = PasswordField('Konfirmasi Kata Sandi Baru', validators=[
        DataRequired(message="Konfirmasi kata sandi wajib diisi."),
        EqualTo('password', message="Kata sandi tidak cocok.")
    ])
    
    submit = SubmitField('Simpan Kata Sandi')


