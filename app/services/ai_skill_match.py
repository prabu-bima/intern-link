import json
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.extensions import db
from app.models import (
    StudentProfile,
    Internship,
    AISkillMatchRun,
    AISkillMatchSkillItem,
    AISkillMatchTechStackItem,
    AISkillMatchItemRole,
    Skill,
    TechStackItem
)
from app.services.gemini import gemini_service, AIPromptTemplates

logger = logging.getLogger(__name__)

def get_student_profile_data(student_profile_id: int) -> Dict[str, Any]:
    """Extract structured student data for AI matching."""
    student = StudentProfile.query.get(student_profile_id)
    if not student:
        raise ValueError(f"StudentProfile not found with ID: {student_profile_id}")

    skills = []
    for ss in student.skills:
        if ss.deleted_at is None:
            skills.append(ss.skill.skill_name)
            
    tech_stack = []
    for st in student.tech_stack_items:
        if st.deleted_at is None:
            tech_stack.append(st.tech_stack_item.tech_stack_name)
            
    portfolios = []
    for sp in student.portfolios:
        if sp.deleted_at is None:
            portfolios.append({
                "title": sp.portfolio_title,
                "description": sp.description or ""
            })

    return {
        "student_id": student.id,
        "bio": student.bio or "",
        "skills": skills,
        "tech_stack": tech_stack,
        "portfolios": portfolios
    }

def get_internship_requirements_data(internship_id: int) -> Dict[str, Any]:
    """Extract structured internship requirements for AI matching."""
    internship = Internship.query.get(internship_id)
    if not internship:
        raise ValueError(f"Internship not found with ID: {internship_id}")

    required_skills = []
    for rs in internship.required_skills:
        if rs.deleted_at is None:
            required_skills.append(rs.skill.skill_name)

    required_tech_stack = []
    for rt in internship.required_tech_stack_items:
        if rt.deleted_at is None:
            required_tech_stack.append(rt.tech_stack_item.tech_stack_name)

    return {
        "internship_id": internship.id,
        "title": internship.internship_title,
        "description": internship.internship_description,
        "required_skills": required_skills,
        "required_tech_stack": required_tech_stack
    }

def compute_input_snapshot_hash(student_data: Dict[str, Any], internship_data: Dict[str, Any]) -> str:
    """Compute a SHA-256 hash of the JSON inputs for caching purposes."""
    # Ensure consistent ordering for hashing
    data_to_hash = {
        "student": student_data,
        "internship": internship_data
    }
    json_str = json.dumps(data_to_hash, sort_keys=True)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

def run_skill_match(student_profile_id: int, internship_id: int) -> Optional[AISkillMatchRun]:
    """
    Run the AI Skill Match logic. Uses cached result if input hasn't changed.
    Generates new match via Gemini API if no cache exists.
    """
    student_data = get_student_profile_data(student_profile_id)
    internship_data = get_internship_requirements_data(internship_id)
    
    snapshot_hash = compute_input_snapshot_hash(student_data, internship_data)
    
    # 1. Check Cache
    existing_run = AISkillMatchRun.query.filter_by(
        student_profile_id=student_profile_id,
        internship_id=internship_id,
        input_snapshot_hash=snapshot_hash,
        deleted_at=None
    ).first()
    
    if existing_run and existing_run.generation_status == 'success':
        logger.info(f"Returning cached AI Skill Match for Student {student_profile_id} and Internship {internship_id}")
        return existing_run

    # 2. Call Gemini API
    prompt = AIPromptTemplates.ai_skill_match(student_data, internship_data)
    
    fallback_response = {
        "match_percentage": 0,
        "matching_skills": [],
        "missing_skills": [],
        "explanation": "Maaf, sistem AI sedang tidak tersedia saat ini. Tidak dapat menganalisis kecocokan.",
        "suggested_skills": [],
        "error": True
    }
    
    result_json = gemini_service.generate_json(prompt, fallback=fallback_response)
    
    # 3. Create AISkillMatchRun
    new_run = AISkillMatchRun(
        student_profile_id=student_profile_id,
        internship_id=internship_id,
        match_percentage=result_json.get("match_percentage", 0),
        ai_explanation=result_json.get("explanation", ""),
        suggested_skills_summary=", ".join(result_json.get("suggested_skills", [])),
        model_name=gemini_service.model_name,
        model_version="1.0",
        input_snapshot_hash=snapshot_hash,
        input_snapshot_json={"student": student_data, "internship": internship_data},
        generation_status="failed" if result_json.get("error") else "success"
    )
    db.session.add(new_run)
    db.session.flush() # Get new_run.id
    
    if result_json.get("error"):
        db.session.commit()
        return new_run

    # 4. Process Skills and Tech Stack Items
    _process_ai_items(new_run.id, result_json)
    
    db.session.commit()
    logger.info(f"Successfully generated new AI Skill Match for Student {student_profile_id} and Internship {internship_id}")
    return new_run

def _process_ai_items(run_id: int, result_json: Dict[str, Any]):
    """Helper to process matching, missing, and suggested skills returned by AI."""
    
    roles = {
        "matching": AISkillMatchItemRole.query.filter_by(role_code="matching").first(),
        "missing": AISkillMatchItemRole.query.filter_by(role_code="missing").first(),
        "suggested": AISkillMatchItemRole.query.filter_by(role_code="suggested").first()
    }
    
    # If roles are missing in DB, we can't save items (should be seeded)
    if not all(roles.values()):
        logger.error("AISkillMatchItemRole records are missing in the database.")
        return
        
    categories = [
        ("matching", result_json.get("matching_skills", [])),
        ("missing", result_json.get("missing_skills", [])),
        ("suggested", result_json.get("suggested_skills", []))
    ]
    
    for role_code, items in categories:
        role_id = roles[role_code].id
        for item_name in items:
            # 1. Try to match as a Skill
            skill = Skill.query.filter(Skill.skill_name.ilike(item_name)).first()
            if skill:
                db.session.add(AISkillMatchSkillItem(
                    ai_skill_match_run_id=run_id,
                    skill_id=skill.id,
                    item_role_id=role_id
                ))
                continue
                
            # 2. Try to match as a Tech Stack Item
            tech_stack = TechStackItem.query.filter(TechStackItem.tech_stack_name.ilike(item_name)).first()
            if tech_stack:
                db.session.add(AISkillMatchTechStackItem(
                    ai_skill_match_run_id=run_id,
                    tech_stack_item_id=tech_stack.id,
                    item_role_id=role_id
                ))
