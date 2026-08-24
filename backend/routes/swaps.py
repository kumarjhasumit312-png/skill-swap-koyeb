from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import SwapRequest, Skill, db

swaps_bp = Blueprint('swaps', __name__)

@swaps_bp.route('/send_swap_request', methods=['POST'])
@login_required
def send_swap_request():
    skill_offered_id = request.form.get('skill_offered_id')
    skill_wanted_id = request.form.get('skill_wanted_id')
    target_id = request.form.get('target_id')
    
    if not all([skill_offered_id, skill_wanted_id, target_id]):
        flash('All fields are required')
        return redirect(url_for('dashboard'))
    
    skill_offered = Skill.query.get(skill_offered_id)
    skill_wanted = Skill.query.get(skill_wanted_id)
    
    if skill_offered.user_id != current_user.id:
        flash('You can only offer your own skills')
        return redirect(url_for('dashboard'))
    
    if skill_wanted.user_id != int(target_id):
        flash('Invalid skill selection')
        return redirect(url_for('dashboard'))
    
    new_request = SwapRequest(
        requester_id=current_user.id,
        target_id=int(target_id),
        skill_offered_id=int(skill_offered_id),
        skill_wanted_id=int(skill_wanted_id)
    )
    db.session.add(new_request)
    db.session.commit()
    
    flash('Swap request sent successfully!')
    return redirect(url_for('dashboard'))

@swaps_bp.route('/respond_swap_request/<int:request_id>', methods=['POST'])
@login_required
def respond_swap_request(request_id):
    swap_request = SwapRequest.query.get_or_404(request_id)
    
    if swap_request.target_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))
    
    action = request.form.get('action')
    
    if action == 'accept':
        swap_request.status = 'accepted'
        flash('Swap request accepted!')
    elif action == 'reject':
        swap_request.status = 'rejected'
        flash('Swap request rejected')
    else:
        flash('Invalid action')
    
    db.session.commit()
    return redirect(url_for('dashboard'))

@swaps_bp.route('/api/swap_requests')
@login_required
def get_swap_requests():
    sent = SwapRequest.query.filter_by(requester_id=current_user.id).all()
    received = SwapRequest.query.filter_by(target_id=current_user.id).all()
    
    requests_data = {
        'sent': [{
            'id': r.id,
            'target': r.target.username,
            'skill_offered': r.skill_offered.skill_name,
            'skill_wanted': r.skill_wanted.skill_name,
            'status': r.status
        } for r in sent],
        'received': [{
            'id': r.id,
            'requester': r.requester.username,
            'skill_offered': r.skill_offered.skill_name,
            'skill_wanted': r.skill_wanted.skill_name,
            'status': r.status
        } for r in received]
    }
    
    return jsonify(requests_data)