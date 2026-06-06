from flask import Flask, redirect, url_for
from flask_login import current_user
from core.extensions import db, login_manager, socketio
import os


def create_app():
    app = Flask(__name__)

    # Config — reads from environment variables in production
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///englishapp.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'homework')
    app.config['PDF_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'pdfs')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

    # Fix for Railway PostgreSQL URL (starts with postgres:// but SQLAlchemy needs postgresql://)
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    if db_url.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('postgres://', 'postgresql://', 1)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*', async_mode='eventlet')

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    from core.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Inject now into all templates
    from datetime import datetime as dt

    @app.context_processor
    def inject_globals():
        return {'now': dt.utcnow()}

    @app.before_request
    def check_single_session():
        from flask import session, redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.role == 'teacher':
                return
            saved_token = session.get('user_token')
            if current_user.session_token != saved_token:
                current_user.is_banned = True
                current_user.session_token = None
                db.session.commit()
                from flask_login import logout_user
                logout_user()
                session.clear()
                return redirect(url_for('auth.login'))

    # Blueprints
    from core.routes.auth import auth_bp
    from core.routes.student import student_bp
    from core.routes.teacher import teacher_bp
    import core.routes.chat  # register socket events

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            return redirect(url_for('student.dashboard'))
        return redirect(url_for('auth.login'))

    # Create tables and seed data
    with app.app_context():
        db.create_all()
        seed_data()

    return app


def seed_data():
    from core.models import User, Grade, Course, Unit, Lesson, Exam, Question, Announcement, SubscriptionCode
    from werkzeug.security import generate_password_hash
    from datetime import datetime, timedelta

    if User.query.count() > 0:
        return

    # Grades
    grades_data = [
        ('First Secondary', 1),
        ('Second Secondary', 2),
        ('Third Secondary', 3),
    ]
    grades = []
    for name, order in grades_data:
        g = Grade(name=name, order=order)
        db.session.add(g)
        grades.append(g)
    db.session.flush()

    # Teacher
    teacher = User(
        name='Mr. Monsif',
        email='teacher@englishclass.com',
        password_hash=generate_password_hash('teacher123'),
        role='teacher'
    )
    db.session.add(teacher)

    # Sample Student
    student = User(
        name='Ali Mohamed',
        email='student@demo.com',
        password_hash=generate_password_hash('student123'),
        role='student',
        grade_id=grades[0].id,
        phone='01234567890'
    )
    db.session.add(student)
    db.session.flush()

    # Subscription code for demo student
    sub_code = SubscriptionCode(
        code='ENG-DEMO-2025',
        grade_id=grades[0].id,
        used_by=student.id,
        expires_at=datetime.utcnow() + timedelta(days=365)
    )
    db.session.add(sub_code)

    # Extra codes
    for i in range(5):
        code = SubscriptionCode(
            code=SubscriptionCode.generate_code('First'),
            grade_id=grades[0].id,
            expires_at=datetime.utcnow() + timedelta(days=180)
        )
        db.session.add(code)
    for i in range(3):
        code = SubscriptionCode(
            code=SubscriptionCode.generate_code('Second'),
            grade_id=grades[1].id,
            expires_at=datetime.utcnow() + timedelta(days=180)
        )
        db.session.add(code)

    # Course
    course = Course(
        title='English Language — Term 1',
        description='Complete English curriculum for First Secondary students covering grammar, reading, and writing.',
        grade_id=grades[0].id,
    )
    db.session.add(course)
    db.session.flush()

    # Units
    unit1 = Unit(title='Unit 1: Present Tenses', description='Simple, continuous and perfect present tenses.',
                 course_id=course.id, order=1)
    unit2 = Unit(title='Unit 2: Vocabulary & Reading', description='Building vocabulary through context and reading passages.',
                 course_id=course.id, order=2)
    db.session.add_all([unit1, unit2])
    db.session.flush()

    # Lessons
    l1 = Lesson(title='Present Simple', description='Learn how to use present simple tense.',
                unit_id=unit1.id, youtube_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ', order=1)
    l2 = Lesson(title='Present Continuous', description='Learn when to use present continuous.',
                unit_id=unit1.id, youtube_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ', order=2)
    l3 = Lesson(title='Reading Comprehension', description='Techniques for reading comprehension.',
                unit_id=unit2.id, youtube_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ', order=1)
    db.session.add_all([l1, l2, l3])
    db.session.flush()

    # Exam
    exam = Exam(title='Unit 1 Quiz', grade_id=grades[0].id, lesson_id=l1.id, duration_minutes=20, pass_score=60)
    db.session.add(exam)
    db.session.flush()

    questions = [
        ('Which sentence is correct?', 'She go to school.', 'She goes to school.', 'She going to school.', 'She goed to school.', 'B'),
        ('Choose the correct form:', 'He is play football now.', 'He plays football now.', 'He is playing football now.', 'He played football now.', 'C'),
        ('The present simple is used for:', 'Actions happening now.', 'Habitual actions.', 'Past completed actions.', 'Future plans only.', 'B'),
        ('Complete: "She ___ English every day."', 'study', 'studies', 'is studying', 'studied', 'B'),
        ('Which is NOT present simple?', 'I work hard.', 'They play tennis.', 'He is sleeping.', 'We eat lunch at noon.', 'C'),
    ]
    for i, (text, a, b, c, d, correct) in enumerate(questions, 1):
        q = Question(exam_id=exam.id, text=text, option_a=a, option_b=b,
                     option_c=c, option_d=d, correct_answer=correct, order=i)
        db.session.add(q)

    # Announcements
    ann1 = Announcement(
        title='Welcome to the New Term! 🎉',
        content='Welcome students! This platform is your go-to resource for all English lessons, exercises, and exams. Make sure to activate your subscription and start learning today.',
        grade_id=None,
        is_pinned=True
    )
    ann2 = Announcement(
        title='Unit 1 Exam — Date Announced',
        content='The Unit 1 exam will be available online starting next week. Make sure you have reviewed all lessons before attempting.',
        grade_id=grades[0].id,
        is_pinned=False
    )
    db.session.add_all([ann1, ann2])
    db.session.commit()
