from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import ScheduledMeeting, db
from datetime import datetime
import uuid

meetings_bp = Blueprint('meetings', __name__)

@meetings_bp.route('/meetings')
@login_required
def my_meetings():
    meetings = ScheduledMeeting.query.filter(
        (ScheduledMeeting.organizer_id == current_user.id) |
        (ScheduledMeeting.participant_id == current_user.id)
    ).order_by(ScheduledMeeting.meeting_date.desc()).all()
    
    return render_template('meetings.html', meetings=meetings)

@meetings_bp.route('/schedule_meeting', methods=['POST'])
@login_required
def schedule_meeting():
    meeting_date_str = request.form.get('meeting_date')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    participant_id = request.form.get('participant_id')
    
    meeting_code = f"MEET-{uuid.uuid4().hex[:8].upper()}"
    
    meeting_date = datetime.strptime(meeting_date_str, '%Y-%m-%d').date()
    start_time = datetime.strptime(start_time_str, '%H:%M').time()
    end_time = datetime.strptime(end_time_str, '%H:%M').time()
    
    new_meeting = ScheduledMeeting(
        swap_request_id=0,
        organizer_id=current_user.id,
        participant_id=int(participant_id),
        meeting_date=meeting_date,
        start_time=start_time,
        end_time=end_time,
        meeting_link=meeting_code,
        status='scheduled'
    )
    db.session.add(new_meeting)
    db.session.commit()
    
    flash(f'Meeting scheduled! Your meeting code: {meeting_code}')
    return redirect(url_for('dashboard'))

@meetings_bp.route('/meeting/<int:meeting_id>')
@login_required
def meeting_detail(meeting_id):
    meeting = ScheduledMeeting.query.get_or_404(meeting_id)
    
    if meeting.organizer_id != current_user.id and meeting.participant_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('my_meetings'))
    
    return render_template('meeting_detail.html', meeting=meeting)

@meetings_bp.route('/cancel_meeting/<int:meeting_id>', methods=['POST'])
@login_required
def cancel_meeting(meeting_id):
    meeting = ScheduledMeeting.query.get_or_404(meeting_id)
    
    if meeting.organizer_id != current_user.id and meeting.participant_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('my_meetings'))
    
    meeting.status = 'cancelled'
    db.session.commit()
    
    flash('Meeting cancelled successfully!')
    return redirect(url_for('my_meetings'))

@meetings_bp.route('/complete_meeting/<int:meeting_id>', methods=['POST'])
@login_required
def complete_meeting(meeting_id):
    meeting = ScheduledMeeting.query.get_or_404(meeting_id)
    
    if meeting.organizer_id != current_user.id and meeting.participant_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('my_meetings'))
    
    meeting.status = 'completed'
    db.session.commit()
    
    flash('Meeting marked as completed!')
    return redirect(url_for('my_meetings'))

@meetings_bp.route('/api/meetings')
@login_required
def get_meetings_api():
    meetings = ScheduledMeeting.query.filter(
        (ScheduledMeeting.organizer_id == current_user.id) |
        (ScheduledMeeting.participant_id == current_user.id)
    ).all()
    
    meetings_data = []
    for meeting in meetings:
        other_user = meeting.participant if meeting.organizer_id == current_user.id else meeting.organizer
        meetings_data.append({
            'id': meeting.id,
            'meeting_date': meeting.meeting_date.strftime('%Y-%m-%d'),
            'start_time': meeting.start_time.strftime('%H:%M'),
            'end_time': meeting.end_time.strftime('%H:%M'),
            'status': meeting.status,
            'meeting_link': meeting.meeting_link,
            'with_user': other_user.username,
            'with_user_id': other_user.id
        })
    
    return jsonify(meetings_data)