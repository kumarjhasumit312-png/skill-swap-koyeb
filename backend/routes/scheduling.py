from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Availability, ScheduledMeeting, SwapRequest, db
from datetime import datetime, time

scheduling_bp = Blueprint('scheduling', __name__)

@scheduling_bp.route('/availability', methods=['GET', 'POST'])
@login_required
def manage_availability():
    if request.method == 'POST':
        day = request.form.get('day_of_week')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        timezone = request.form.get('timezone', 'Asia/Kolkata')
        
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        new_availability = Availability(
            user_id=current_user.id,
            day_of_week=day,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone
        )
        db.session.add(new_availability)
        db.session.commit()
        
        flash('Availability added successfully!')
        return redirect(url_for('scheduling.manage_availability'))
    
    availabilities = Availability.query.filter_by(user_id=current_user.id).all()
    return render_template('availability.html', availabilities=availabilities)

@scheduling_bp.route('/delete_availability/<int:avail_id>', methods=['POST'])
@login_required
def delete_availability(avail_id):
    availability = Availability.query.get_or_404(avail_id)
    
    if availability.user_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('scheduling.manage_availability'))
    
    db.session.delete(availability)
    db.session.commit()
    
    flash('Availability deleted successfully!')
    return redirect(url_for('scheduling.manage_availability'))

@scheduling_bp.route('/api/availability/<int:user_id>')
@login_required
def get_user_availability(user_id):
    availabilities = Availability.query.filter_by(user_id=user_id).all()
    
    avail_data = []
    for avail in availabilities:
        avail_data.append({
            'id': avail.id,
            'day_of_week': avail.day_of_week,
            'start_time': avail.start_time.strftime('%H:%M'),
            'end_time': avail.end_time.strftime('%H:%M'),
            'timezone': avail.timezone
        })
    
    return jsonify(avail_data)

@scheduling_bp.route('/book_meeting/<int:target_user_id>', methods=['GET', 'POST'])
@login_required
def book_meeting(target_user_id):
    if request.method == 'POST':
        swap_request_id = request.form.get('swap_request_id')
        meeting_date_str = request.form.get('meeting_date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        meeting_date = datetime.strptime(meeting_date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        meeting_link = f"MEET-{target_user_id}_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        new_meeting = ScheduledMeeting(
            swap_request_id=int(swap_request_id),
            organizer_id=current_user.id,
            participant_id=target_user_id,
            meeting_date=meeting_date,
            start_time=start_time,
            end_time=end_time,
            meeting_link=meeting_link
        )
        db.session.add(new_meeting)
        db.session.commit()
        
        flash(f'Meeting scheduled! Your meeting code: {meeting_link}')
        return redirect(url_for('meetings.my_meetings'))
    
    target_availability = Availability.query.filter_by(user_id=target_user_id).all()
    swap_requests = SwapRequest.query.filter(
        ((SwapRequest.requester_id == current_user.id) & (SwapRequest.target_id == target_user_id)) |
        ((SwapRequest.target_id == current_user.id) & (SwapRequest.requester_id == target_user_id))
    ).filter_by(status='accepted').all()
    
    return render_template('book_meeting.html', 
                         target_user_id=target_user_id,
                         availabilities=target_availability,
                         swap_requests=swap_requests)