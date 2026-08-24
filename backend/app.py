from datetime import datetime

from flask import Flask, render_template
from flask_login import LoginManager, login_required, current_user
from flask_socketio import SocketIO, join_room, emit

from config import Config
from models import db, User, SwapRequest, ScheduledMeeting

from routes.auth import auth_bp
from routes.skills import skills_bp
from routes.swaps import swaps_bp
from routes.scheduling import scheduling_bp
from routes.meetings import meetings_bp


socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet"
)
@socketio.on("join_meeting")
def handle_join_meeting(data):
    meeting_id = str(data.get("meeting_id"))

    if not meeting_id:
        return

    join_room(meeting_id)

    emit(
        "user_joined",
        {
            "meeting_id": meeting_id
        },
        to=meeting_id,
        include_self=False
    )


@socketio.on("webrtc_offer")
def handle_webrtc_offer(data):
    meeting_id = str(data.get("meeting_id"))
    offer = data.get("offer")

    if not meeting_id or not offer:
        return

    emit(
        "webrtc_offer",
        {
            "offer": offer
        },
        to=meeting_id,
        include_self=False
    )


@socketio.on("webrtc_answer")
def handle_webrtc_answer(data):
    meeting_id = str(data.get("meeting_id"))
    answer = data.get("answer")

    if not meeting_id or not answer:
        return

    emit(
        "webrtc_answer",
        {
            "answer": answer
        },
        to=meeting_id,
        include_self=False
    )


@socketio.on("webrtc_ice_candidate")
def handle_webrtc_ice_candidate(data):
    meeting_id = str(data.get("meeting_id"))
    candidate = data.get("candidate")

    if not meeting_id or not candidate:
        return

    emit(
        "webrtc_ice_candidate",
        {
            "candidate": candidate
        },
        to=meeting_id,
        include_self=False
    )

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    socketio.init_app(app)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please login to access this page."

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(skills_bp, url_prefix="/skills")
    app.register_blueprint(swaps_bp, url_prefix="/swaps")
    app.register_blueprint(scheduling_bp, url_prefix="/scheduling")
    app.register_blueprint(meetings_bp, url_prefix="/meetings")

    # Keep this only if backend/routes/webrtc.py exists
    from routes.webrtc import webrtc_bp
    app.register_blueprint(webrtc_bp, url_prefix="/webrtc")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/dashboard")
    @login_required
    def dashboard():
        user_skills = User.query.get(current_user.id).skills

        pending_requests = SwapRequest.query.filter(
            (
                (SwapRequest.requester_id == current_user.id)
                | (SwapRequest.target_id == current_user.id)
            )
            & (SwapRequest.status == "pending")
        ).all()

        upcoming_meetings = ScheduledMeeting.query.filter(
            (
                (ScheduledMeeting.organizer_id == current_user.id)
                | (ScheduledMeeting.participant_id == current_user.id)
            )
            & (ScheduledMeeting.status == "scheduled")
        ).filter(
            ScheduledMeeting.meeting_date >= datetime.now().date()
        ).all()

        return render_template(
            "dashboard.html",
            user_skills=user_skills,
            pending_requests=pending_requests,
            upcoming_meetings=upcoming_meetings,
            today=datetime.now().strftime("%Y-%m-%d")
        )

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()

    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )