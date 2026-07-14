import json
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.extensions import db
from app.models import (
    StudentProfile,
    Internship,
    InternshipLifecycleStatus,
    AIJobRecommendationRun,
    AIJobRecommendationItem
)
from app.services.gemini import gemini_service, AIPromptTemplates

logger = logging.getLogger(__name__)

def get_student_full_profile(student_profile_id: int) -> Dict[str, Any]:
    """Extract complete student data for job recommendation."""
    student = StudentProfile.query.get(student_profile_id)
    if not student:
        raise ValueError(f"StudentProfile not found with ID: {student_profile_id}")

    skills = []
    for ss in student.skills:
        if ss.deleted_at is None:
            skills.append({
                "skill_name": ss.skill.skill_name,
                "proficiency_level": ss.proficiency_level or "",
                "years_experience": ss.years_experience or 0
            })
            
    tech_stack = []
    for st in student.tech_stack_items:
        if st.deleted_at is None:
            tech_stack.append({
                "tech_stack_name": st.tech_stack_item.tech_stack_name,
                "proficiency_level": st.proficiency_level or ""
            })
            
    education = []
    for edu in student.education_records:
        if edu.deleted_at is None:
            education.append({
                "degree_name": edu.degree_name,
                "field_of_study": edu.field_of_study,
                "institution_name": edu.institution_name,
                "grade": edu.grade or "",
                "start_date": edu.start_date.isoformat() if edu.start_date else "",
                "end_date": edu.end_date.isoformat() if edu.end_date else ""
            })
            
    experiences = []
    for exp in student.experiences:
        if exp.deleted_at is None:
            experiences.append({
                "title": exp.title,
                "organization_name": exp.organization_name,
                "description": exp.description or "",
                "start_date": exp.start_date.isoformat() if exp.start_date else "",
                "end_date": exp.end_date.isoformat() if exp.end_date else ""
            })
            
    organizations = []
    for org in student.organizations:
        if org.deleted_at is None:
            organizations.append({
                "organization_name": org.organization_name,
                "role_title": org.role_title,
                "description": org.description or "",
                "start_date": org.start_date.isoformat() if org.start_date else "",
                "end_date": org.end_date.isoformat() if org.end_date else ""
            })

    portfolios = []
    for sp in student.portfolios:
        if sp.deleted_at is None:
            portfolios.append({
                "title": sp.portfolio_title,
                "url": sp.portfolio_url or "",
                "description": sp.description or ""
            })

    return {
        "student_id": student.id,
        "bio": student.bio or "",
        "skills": skills,
        "tech_stack": tech_stack,
        "education": education,
        "experiences": experiences,
        "organizations": organizations,
        "portfolios": portfolios
    }

def get_active_internships_pool() -> list[Dict[str, Any]]:
    """Query all active internships with their requirements."""
    # Find active lifecycle status
    active_status = InternshipLifecycleStatus.query.filter(
        InternshipLifecycleStatus.status_code == 'active'
    ).first()
    if not active_status:
        active_status = InternshipLifecycleStatus.query.filter(
            InternshipLifecycleStatus.status_name.ilike('%active%')
        ).first()
    if not active_status:
        active_status = InternshipLifecycleStatus.query.filter(
            InternshipLifecycleStatus.status_name.ilike('%open%')
        ).first()

    query = Internship.query
    if active_status:
        query = query.filter(Internship.lifecycle_status_id == active_status.id)
    query = query.filter(Internship.deleted_at.is_(None))
    
    internships = query.all()
    pool = []
    for i in internships:
        required_skills = []
        for rs in i.required_skills:
            if rs.deleted_at is None:
                required_skills.append(rs.skill.skill_name)
                
        required_tech_stack = []
        for rt in i.required_tech_stack_items:
            if rt.deleted_at is None:
                required_tech_stack.append(rt.tech_stack_item.tech_stack_name)
                
        pool.append({
            "internship_id": i.id,
            "title": i.internship_title,
            "description": i.internship_description,
            "type": i.internship_type or "",
            "location": f"{i.location.city}, {i.location.region}" if i.location else "",
            "category": i.technology_category.category_name if i.technology_category else "",
            "required_skills": required_skills,
            "required_tech_stack": required_tech_stack
        })
    return pool

def compute_recommendation_input_hash(student_data: Dict[str, Any], internships_pool: list[Dict[str, Any]]) -> str:
    """Compute a SHA-256 hash of the JSON inputs for caching purposes."""
    data_to_hash = {
        "student": student_data,
        "internships": internships_pool
    }
    json_str = json.dumps(data_to_hash, sort_keys=True)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

def run_job_recommendation(student_profile_id: int) -> Optional[AIJobRecommendationRun]:
    """
    Run the AI Job Recommendation logic. Uses cached result if input hasn't changed.
    Generates new recommendations via Gemini API if no cache exists.
    """
    student_data = get_student_full_profile(student_profile_id)
    internships_pool = get_active_internships_pool()
    
    # If no active internships, return an empty run without calling Gemini API
    if not internships_pool:
        new_run = AIJobRecommendationRun(
            student_profile_id=student_profile_id,
            model_name=gemini_service.model_name,
            model_version="1.0",
            input_snapshot_hash="",
            input_snapshot_json={"student": student_data, "internships": []},
            generation_status="success"
        )
        db.session.add(new_run)
        db.session.commit()
        return new_run

    snapshot_hash = compute_recommendation_input_hash(student_data, internships_pool)
    
    # 1. Check Cache
    existing_run = AIJobRecommendationRun.query.filter_by(
        student_profile_id=student_profile_id,
        input_snapshot_hash=snapshot_hash,
        deleted_at=None
    ).first()
    
    if existing_run and existing_run.generation_status == 'success':
        logger.info(f"Returning cached AI Job Recommendation for Student {student_profile_id}")
        return existing_run

    # 2. Call Gemini API
    prompt = AIPromptTemplates.job_recommendation(student_data, internships_pool)
    
    fallback_response = {
        "recommendations": [],
        "error": True
    }
    
    result_json = gemini_service.generate_json(prompt, fallback=fallback_response)
    
    # 3. Create AIJobRecommendationRun
    new_run = AIJobRecommendationRun(
        student_profile_id=student_profile_id,
        model_name=gemini_service.model_name,
        model_version="1.0",
        input_snapshot_hash=snapshot_hash,
        input_snapshot_json={"student": student_data, "internships": internships_pool},
        generation_status="failed" if result_json.get("error") else "success"
    )
    db.session.add(new_run)
    db.session.flush() # Get new_run.id
    
    if result_json.get("error"):
        db.session.commit()
        return new_run

    # 4. Save Recommendation Items
    recommendations_list = result_json.get("recommendations", [])
    valid_ids = {item["internship_id"] for item in internships_pool}
    recommendations_list = [r for r in recommendations_list if r.get("internship_id") in valid_ids]
    
    recommendations_list.sort(key=lambda x: x.get("match_percentage", 0), reverse=True)
    
    for rank, rec in enumerate(recommendations_list, start=1):
        db_item = AIJobRecommendationItem(
            ai_job_recommendation_run_id=new_run.id,
            internship_id=rec.get("internship_id"),
            match_score=float(rec.get("match_percentage", 0)),
            recommendation_reason=rec.get("reasoning", ""),
            rank_no=rank
        )
        db.session.add(db_item)
        
    db.session.commit()
    logger.info(f"Successfully generated new AI Job Recommendation for Student {student_profile_id}")
    return new_run
