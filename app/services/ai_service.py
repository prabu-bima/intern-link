import os
import json
import hashlib
from datetime import datetime
import google.generativeai as genai
from flask import current_app
from app.extensions import db
from app.models.ai import AISkillMatchRun, AISkillMatchSkillItem, AISkillMatchTechStackItem
from app.models.lookups import AISkillMatchItemRole
from app.models.identity import StudentProfile
from app.models.internship import Internship

# Configure Gemini globally if API key exists
if os.environ.get('GEMINI_API_KEY'):
    genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

def calculate_skill_match(student_profile_id: int, internship_id: int) -> dict:
    """
    Calculate AI Skill Match using Google Gemini API.
    Checks if a valid result exists first. If not, calls the API and saves the result.
    Returns a dict with the result data.
    """
    # 1. Check if a recent run exists
    existing_run = AISkillMatchRun.query.filter_by(
        student_profile_id=student_profile_id,
        internship_id=internship_id
    ).filter(AISkillMatchRun.deleted_at.is_(None)).order_by(AISkillMatchRun.id.desc()).first()
    
    if existing_run and existing_run.generation_status == 'success':
        # Retrieve items
        matched_skills = [
            item.skill.skill_name for item in existing_run.skill_items 
            if item.item_role.role_code == 'matched'
        ]
        missing_skills = [
            item.skill.skill_name for item in existing_run.skill_items 
            if item.item_role.role_code == 'missing'
        ]
        
        return {
            'status': 'success',
            'match_percentage': existing_run.match_percentage,
            'ai_explanation': existing_run.ai_explanation,
            'matching_skills': matched_skills,
            'missing_skills': missing_skills
        }
        
    # 2. Fetch data to build prompt
    student = StudentProfile.query.get(student_profile_id)
    internship = Internship.query.get(internship_id)
    
    if not student or not internship:
        return {'status': 'error', 'message': 'Student or Internship not found'}
        
    # Student data
    student_skills = [s.skill.skill_name for s in student.skills]
    student_tech_stack = [ts.tech_stack_item.tech_stack_name for ts in student.tech_stack_items]
    
    # Internship data
    required_skills = [s.skill.skill_name for s in internship.required_skills]
    required_tech_stack = [ts.tech_stack_item.tech_stack_name for ts in internship.required_tech_stack_items]
    
    # Check if we have enough requirements to match against
    if not required_skills and not required_tech_stack:
        return {
            'status': 'success',
            'match_percentage': 100.0,
            'ai_explanation': 'Lowongan ini tidak mensyaratkan keahlian khusus secara spesifik pada sistem.',
            'matching_skills': [],
            'missing_skills': []
        }
        
    # Check API key
    if not os.environ.get('GEMINI_API_KEY'):
        return {'status': 'error', 'message': 'GEMINI_API_KEY is not configured in .env'}
        
    # 3. Build Prompt
    prompt = f"""
Anda adalah sistem AI rekrutmen cerdas bernama InternLink.
Tugas Anda adalah membandingkan profil keahlian mahasiswa dengan syarat magang dan menghasilkan laporan kecocokan.

### Profil Mahasiswa:
- Skills: {', '.join(student_skills) if student_skills else 'Tidak ada'}
- Tech Stack: {', '.join(student_tech_stack) if student_tech_stack else 'Tidak ada'}

### Persyaratan Magang ({internship.internship_title} di {internship.company_profile.company_name}):
- Required Skills: {', '.join(required_skills) if required_skills else 'Tidak ada'}
- Required Tech Stack: {', '.join(required_tech_stack) if required_tech_stack else 'Tidak ada'}

Instruksi:
1. Hitung persentase kecocokan (0-100) berdasarkan seberapa banyak syarat magang yang dipenuhi mahasiswa.
2. Jelaskan alasan skor tersebut dalam 2-3 kalimat singkat (gunakan bahasa Indonesia yang profesional dan memotivasi).
3. Identifikasi syarat mana saja yang berhasil dipenuhi mahasiswa (matched). Jika syarat dan keahlian mahasiswa sangat mirip tapi beda penulisan, anggap cocok.
4. Identifikasi syarat mana saja yang belum dimiliki mahasiswa (missing).

Keluarkan hasil secara ketat HANYA dalam format JSON berikut (tanpa tambahan markdown atau backtick):
{{
    "match_percentage": <number>,
    "ai_explanation": "<string>",
    "matching_skills": ["<skill1>", "<skill2>"],
    "missing_skills": ["<skill3>", "<skill4>"]
}}
"""

    # 4. Call Gemini API
    try:
        model = genai.GenerativeModel('gemini-3.5-flash')
        # Ensure we get JSON
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        
        result_json = response.text
        # Clean up possible markdown wrappers
        if result_json.startswith('```json'):
            result_json = result_json[7:]
        if result_json.startswith('```'):
            result_json = result_json[3:]
        if result_json.endswith('```'):
            result_json = result_json[:-3]
        result_json = result_json.strip()
        
        try:
            result_data = json.loads(result_json)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error in Gemini AI Match: {e}")
            print(f"Raw response: {result_json}")
            return {'status': 'error', 'message': 'Gagal memproses respons dari AI. Silakan coba lagi.'}
        
        # 5. Save to database
        run = AISkillMatchRun(
            student_profile_id=student_profile_id,
            internship_id=internship_id,
            match_percentage=result_data.get('match_percentage', 0),
            ai_explanation=result_data.get('ai_explanation', ''),
            model_name='gemini-3.5-flash',
            generation_status='success'
        )
        db.session.add(run)
        db.session.flush() # Get run.id
        
        # We need role codes
        matched_role = AISkillMatchItemRole.query.filter_by(role_code='matched').first()
        missing_role = AISkillMatchItemRole.query.filter_by(role_code='missing').first()
        
        if not matched_role:
            matched_role = AISkillMatchItemRole(role_code='matched', role_name='Matched Skill')
            db.session.add(matched_role)
            db.session.flush()
        if not missing_role:
            missing_role = AISkillMatchItemRole(role_code='missing', role_name='Missing Skill')
            db.session.add(missing_role)
            db.session.flush()
            
        
        # Add skill items based on required skills matching the strings
        req_skill_map = { s.skill.skill_name.lower(): s.skill_id for s in internship.required_skills }
        
        # Matched skills
        for ms in result_data.get('matching_skills', []):
            if ms.lower() in req_skill_map:
                item = AISkillMatchSkillItem(
                    ai_skill_match_run_id=run.id,
                    skill_id=req_skill_map[ms.lower()],
                    item_role_id=matched_role.id
                )
                db.session.add(item)
                
        # Missing skills
        for ms in result_data.get('missing_skills', []):
            if ms.lower() in req_skill_map:
                item = AISkillMatchSkillItem(
                    ai_skill_match_run_id=run.id,
                    skill_id=req_skill_map[ms.lower()],
                    item_role_id=missing_role.id
                )
                db.session.add(item)
                
        db.session.commit()
        
        return {
            'status': 'success',
            'match_percentage': run.match_percentage,
            'ai_explanation': run.ai_explanation,
            'matching_skills': result_data.get('matching_skills', []),
            'missing_skills': result_data.get('missing_skills', [])
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in Gemini AI Match: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
