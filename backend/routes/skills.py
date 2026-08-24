from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Skill, db, User

skills_bp = Blueprint('skills', __name__)

@skills_bp.route('/add_skill', methods=['POST'])
@login_required
def add_skill():
    skill_name = request.form.get('skill_name')
    skill_type = request.form.get('skill_type', 'teach')
    skill_level = request.form.get('skill_level')
    description = request.form.get('description', '')
    
    if not skill_name or not skill_level:
        flash('Skill name and level are required')
        return redirect(url_for('dashboard'))
    
    new_skill = Skill(
        user_id=current_user.id,
        skill_name=skill_name,
        skill_type=skill_type,
        skill_level=skill_level,
        description=description
    )
    db.session.add(new_skill)
    db.session.commit()
    
    flash('Skill added successfully!')
    return redirect(url_for('dashboard'))

@skills_bp.route('/delete_skill/<int:skill_id>', methods=['POST'])
@login_required
def delete_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    
    if skill.user_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))
    
    db.session.delete(skill)
    db.session.commit()
    
    flash('Skill deleted successfully!')
    return redirect(url_for('dashboard'))

@skills_bp.route('/api/skills/smart-matches')
@login_required
def get_smart_matches():
    user_teach = Skill.query.filter_by(user_id=current_user.id, skill_type='teach').all()
    user_learn = Skill.query.filter_by(user_id=current_user.id, skill_type='learn').all()
    
    teach_names = [s.skill_name for s in user_teach]
    learn_names = [s.skill_name for s in user_learn]
    
    matches = db.session.query(User, Skill).join(Skill).filter(
        Skill.skill_name.in_(learn_names),
        Skill.skill_type == 'teach',
        Skill.user_id != current_user.id
    ).all()
    
    matches_data = []
    for user, skill in matches:
        match_score = 75
        if skill.skill_level in ['intermediate', 'advanced']:
            match_score += 10
        if skill.skill_name in teach_names:
            match_score += 15
        
        matches_data.append({
            'user_id': user.id,
            'username': user.username,
            'skill_name': skill.skill_name,
            'skill_level': skill.skill_level,
            'match_score': min(match_score, 100)
        })
    
    matches_data.sort(key=lambda x: x['match_score'], reverse=True)
    
    return jsonify(matches_data[:10])