import json
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import selectinload, joinedload
from app.extensions import db
from app.models import (
    StudentProfile,
    Internship,
    InternshipLifecycleStatus,
    InternshipModerationStatus,
    AIJobRecommendationRun,
    AIJobRecommendationItem
)
from app.models.student import (
    StudentSkill, StudentTechStackItem, StudentEducationRecord,
    StudentExperience, StudentOrganization, StudentPortfolio
)
from app.models.internship import InternshipRequiredSkill, InternshipRequiredTechStackItem
from app.models.master import Skill, TechStackItem, Location, TechnologyCategory
from app.services.groq_service import groq_service, AIPromptTemplates

logger = logging.getLogger(__name__)

# Hard cap on pool size sent to Groq — prevents token bloat with many active internships
POOL_LIMIT = 30


def get_student_full_profile(student_profile_id: int) -> Dict[str, Any]:
    """Extract complete student data for job recommendation.
    Uses eager loading to avoid N+1 queries on relationship collections.
    """
    student = StudentProfile.query.options(
        selectinload(StudentProfile.skills).joinedload(StudentSkill.skill),
        selectinload(StudentProfile.tech_stack_items).joinedload(StudentTechStackItem.tech_stack_item),
        selectinload(StudentProfile.education_records),
        selectinload(StudentProfile.experiences),
        selectinload(StudentProfile.organizations),
        selectinload(StudentProfile.portfolios),
    ).filter_by(id=student_profile_id).first()

    if not student:
        raise ValueError(f"StudentProfile not found with ID: {student_profile_id}")

    skills = [
        {
            "skill_name": ss.skill.skill_name,
            "proficiency_level": ss.proficiency_level or "",
            "years_experience": ss.years_experience or 0,
        }
        for ss in student.skills if ss.deleted_at is None
    ]

    tech_stack = [
        {
            "tech_stack_name": st.tech_stack_item.tech_stack_name,
            "proficiency_level": st.proficiency_level or "",
        }
        for st in student.tech_stack_items if st.deleted_at is None
    ]

    education = [
        {
            "degree_name": edu.degree_name,
            "field_of_study": edu.field_of_study,
            "institution_name": edu.institution_name,
            "grade": edu.grade or "",
        }
        for edu in student.education_records if edu.deleted_at is None
    ]

    experiences = [
        {
            "title": exp.title,
            "organization_name": exp.organization_name,
            "description": (exp.description or "")[:200],  # truncate long descriptions
        }
        for exp in student.experiences if exp.deleted_at is None
    ]

    portfolios = [
        {
            "title": sp.portfolio_title,
            "description": (sp.description or "")[:150],
        }
        for sp in student.portfolios if sp.deleted_at is None
    ]

    return {
        "student_id": student.id,
        "bio": (student.bio or "")[:300],  # truncate bio
        "skills": skills,
        "tech_stack": tech_stack,
        "education": education,
        "experiences": experiences,
        "portfolios": portfolios,
    }


def get_active_internships_pool() -> list[Dict[str, Any]]:
    """Query active internships with their requirements.

    Uses selectinload to eliminate the N+1 query pattern.
    Strips internship_description from the payload to reduce token count —
    the AI only needs title, category, skills, and tech stack for matching.
    Capped at POOL_LIMIT to keep prompt size manageable.
    """
    active_status = InternshipLifecycleStatus.query.filter_by(
        status_code='active'
    ).first()

    query = Internship.query.options(
        joinedload(Internship.location),
        joinedload(Internship.technology_category),
        selectinload(Internship.required_skills).joinedload(InternshipRequiredSkill.skill),
        selectinload(Internship.required_tech_stack_items).joinedload(InternshipRequiredTechStackItem.tech_stack_item),
    ).filter(Internship.deleted_at.is_(None))

    if active_status:
        query = query.filter(Internship.lifecycle_status_id == active_status.id)

    approved_moderation = InternshipModerationStatus.query.filter_by(status_code='approved').first()
    if approved_moderation:
        query = query.filter(Internship.moderation_status_id == approved_moderation.id)

    internships = query.limit(POOL_LIMIT).all()

    pool = []
    for i in internships:
        required_skills = [
            rs.skill.skill_name
            for rs in i.required_skills
            if rs.deleted_at is None
        ]
        required_tech_stack = [
            rt.tech_stack_item.tech_stack_name
            for rt in i.required_tech_stack_items
            if rt.deleted_at is None
        ]
        pool.append({
            "internship_id": i.id,
            "title": i.internship_title,
            "type": i.internship_type or "",
            "location": f"{i.location.city}" if i.location else "",
            "category": i.technology_category.category_name if i.technology_category else "",
            "required_skills": required_skills,
            "required_tech_stack": required_tech_stack,
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
    Generates new recommendations via Groq API if no cache exists.
    """
    student_data = get_student_full_profile(student_profile_id)
    internships_pool = get_active_internships_pool()
    
    # If no active internships, return an empty run without calling Groq API
    if not internships_pool:
        new_run = AIJobRecommendationRun(
            student_profile_id=student_profile_id,
            model_name=groq_service.model_name,
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

    # 2. Call Groq API
    prompt = AIPromptTemplates.job_recommendation(student_data, internships_pool)
    
    fallback_response = {
        "recommendations": [],
        "error": True
    }
    
    result_json = groq_service.generate_json(prompt, fallback=fallback_response)
    
    # 3. Create AIJobRecommendationRun
    new_run = AIJobRecommendationRun(
        student_profile_id=student_profile_id,
        model_name=groq_service.model_name,
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
