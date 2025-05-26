from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import User

# إنشاء مسار للمصادقة
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """تسجيل الدخول"""
    if current_user.is_authenticated:
        if current_user.is_coach():
            return redirect(url_for('coach.dashboard'))
        else:
            return redirect(url_for('trainee.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.get_by_email(email)
        
        if not user or not check_password_hash(user.password, password):
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=remember)
        
        if user.is_coach():
            return redirect(url_for('coach.dashboard'))
        else:
            return redirect(url_for('trainee.dashboard'))
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """إنشاء حساب جديد"""
    if current_user.is_authenticated:
        if current_user.is_coach():
            return redirect(url_for('coach.dashboard'))
        else:
            return redirect(url_for('trainee.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        user_type = request.form.get('user_type')
        
        # التحقق من البيانات
        if not name or not email or not password:
            flash('جميع الحقول مطلوبة', 'error')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('كلمات المرور غير متطابقة', 'error')
            return redirect(url_for('auth.register'))
        
        if User.get_by_email(email):
            flash('البريد الإلكتروني مستخدم بالفعل', 'error')
            return redirect(url_for('auth.register'))
        
        # إنشاء المستخدم
        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password, method='sha256'),
            user_type=user_type
        )
        user.save()
        
        flash('تم إنشاء الحساب بنجاح، يمكنك الآن تسجيل الدخول', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """الملف الشخصي"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # التحقق من البيانات
        if not name or not email:
            flash('الاسم والبريد الإلكتروني مطلوبان', 'error')
            return redirect(url_for('auth.profile'))
        
        # التحقق من البريد الإلكتروني
        user_with_email = User.get_by_email(email)
        if user_with_email and user_with_email.id != current_user.id:
            flash('البريد الإلكتروني مستخدم بالفعل', 'error')
            return redirect(url_for('auth.profile'))
        
        # تحديث البيانات
        current_user.name = name
        current_user.email = email
        
        # تحديث كلمة المرور إذا تم توفيرها
        if current_password and new_password:
            if not check_password_hash(current_user.password, current_password):
                flash('كلمة المرور الحالية غير صحيحة', 'error')
                return redirect(url_for('auth.profile'))
            
            if new_password != confirm_password:
                flash('كلمات المرور الجديدة غير متطابقة', 'error')
                return redirect(url_for('auth.profile'))
            
            current_user.password = generate_password_hash(new_password, method='sha256')
        
        current_user.save()
        
        flash('تم تحديث الملف الشخصي بنجاح', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html')

@auth_bp.route('/set_language/<lang>')
def set_language(lang):
    """تعيين لغة التطبيق"""
    if lang in ['ar', 'en']:
        session['lang'] = lang
    
    return redirect(request.referrer or url_for('home'))
