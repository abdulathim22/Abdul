import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, current_user
from datetime import datetime

# إنشاء تطبيق Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key-for-development')

# إعداد مدير تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# استيراد النماذج
from src.models.user import User

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

# تسجيل مسارات التطبيق
from src.routes.auth_routes import auth_bp
from src.routes.trainee_routes import trainee_bp
from src.routes.coach_routes import coach_bp

app.register_blueprint(auth_bp)
app.register_blueprint(trainee_bp)
app.register_blueprint(coach_bp)

# إعداد متغيرات عامة للقوالب
@app.context_processor
def inject_globals():
    return {
        'current_year': datetime.now().year,
        'app_version': '1.0.0',
        'lang': session.get('lang', 'ar')  # اللغة الافتراضية هي العربية
    }

# الصفحة الرئيسية
@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.is_coach():
            return redirect(url_for('coach.dashboard'))
        else:
            return redirect(url_for('trainee.dashboard'))
    return redirect(url_for('auth.login'))

# معالج الأخطاء 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message='الصفحة غير موجودة'), 404

# معالج الأخطاء 500
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message='خطأ في الخادم'), 500

# تشغيل التطبيق
if __name__ == '__main__':
    # التأكد من وجود مجلدات البيانات
    os.makedirs('src/static/data', exist_ok=True)
    
    # تهيئة قاعدة البيانات
    from src.models.user import init_db
    init_db()
    
    # تشغيل التطبيق
    app.run(host='0.0.0.0', port=5000, debug=False)
