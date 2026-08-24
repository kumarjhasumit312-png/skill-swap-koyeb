from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import ScheduledMeeting


webrtc_bp = Blueprint("webrtc", __name__)


@webrtc_bp.route("/join", methods=["GET", "POST"])
@login_required
def join_meeting():
    """
    Dashboard / Meetings page ke Join Meeting form ke liye route.
    Valid meeting code verify karta hai, phir Jitsi room open karta hai.
    """

    if request.method == "POST":
        meeting_code = (
            request.form.get("meeting_code")
            or request.form.get("code")
            or ""
        ).strip()
    else:
        meeting_code = (request.args.get("code") or "").strip()

    if not meeting_code:
        flash("Please enter a meeting code.", "error")
        return redirect(url_for("dashboard"))

    meeting = ScheduledMeeting.query.filter_by(
        meeting_link=meeting_code
    ).first()

    if meeting is None:
        flash("Invalid meeting code.", "error")
        return redirect(url_for("dashboard"))

    allowed_users = {
        meeting.organizer_id,
        meeting.participant_id
    }

    if current_user.id not in allowed_users:
        flash("You are not allowed to join this meeting.", "error")
        return redirect(url_for("dashboard"))

    return redirect(
        url_for(
            "webrtc.meeting_room",
            meeting_id=meeting.id
        )
    )
@webrtc_bp.route("/meeting_room/<int:meeting_id>")
@login_required
def meeting_room(meeting_id):
    meeting = ScheduledMeeting.query.get_or_404(meeting_id)

    allowed_users = {
        meeting.organizer_id,
        meeting.participant_id
    }

    if current_user.id not in allowed_users:
        flash("You are not allowed to join this meeting.", "error")
        return redirect(url_for("dashboard"))

    # Database meeting code is the Jitsi room identity.
    # Special characters remove so Jitsi gets a clean room name.
    jitsi_room_name = "".join(
        character
        for character in str(meeting.meeting_link)
        if character.isalnum()
    )

    return render_template(
        "meeting_room.html",
        meeting=meeting,
        jitsi_room_name=jitsi_room_name,
        user_name=current_user.username
    )