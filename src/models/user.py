from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

class User(UserMixin):
    """نموذج المستخدم مع دعم أنواع الحسابات (مدرب/متدرب)"""
    
    def __init__(self, id=None, email=None, name=None, user_type=None, password_hash=None, created_at=None):
        self.id = id
        self.email = email
        self.name = name
        self.user_type = user_type  # 'coach' أو 'trainee'
        self.password_hash = password_hash
        self.created_at = created_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def set_password(self, password):
        """تعيين كلمة المرور المشفرة"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """التحقق من كلمة المرور"""
        return check_password_hash(self.password_hash, password)
    
    def is_coach(self):
        """التحقق مما إذا كان المستخدم مدرباً"""
        return self.user_type == 'coach'
    
    def is_trainee(self):
        """التحقق مما إذا كان المستخدم متدرباً"""
        return self.user_type == 'trainee'
    
    @staticmethod
    def get_by_id(user_id):
        """الحصول على المستخدم بواسطة المعرف"""
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        if user:
            return User(
                id=user['id'],
                email=user['email'],
                name=user['name'],
                user_type=user['user_type'],
                password_hash=user['password_hash'],
                created_at=user['created_at']
            )
        return None
    
    @staticmethod
    def get_by_email(email):
        """الحصول على المستخدم بواسطة البريد الإلكتروني"""
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user:
            return User(
                id=user['id'],
                email=user['email'],
                name=user['name'],
                user_type=user['user_type'],
                password_hash=user['password_hash'],
                created_at=user['created_at']
            )
        return None
    
    def save(self):
        """حفظ المستخدم في قاعدة البيانات"""
        conn = get_db_connection()
        
        if self.id:
            # تحديث مستخدم موجود
            conn.execute(
                'UPDATE users SET email = ?, name = ?, user_type = ?, password_hash = ? WHERE id = ?',
                (self.email, self.name, self.user_type, self.password_hash, self.id)
            )
        else:
            # إضافة مستخدم جديد
            cursor = conn.execute(
                'INSERT INTO users (email, name, user_type, password_hash, created_at) VALUES (?, ?, ?, ?, ?)',
                (self.email, self.name, self.user_type, self.password_hash, self.created_at)
            )
            self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return self.id
    
    @staticmethod
    def get_all_trainees():
        """الحصول على جميع المتدربين"""
        conn = get_db_connection()
        trainees = conn.execute('SELECT * FROM users WHERE user_type = "trainee"').fetchall()
        conn.close()
        
        return [User(
            id=trainee['id'],
            email=trainee['email'],
            name=trainee['name'],
            user_type=trainee['user_type'],
            password_hash=trainee['password_hash'],
            created_at=trainee['created_at']
        ) for trainee in trainees]
    
    @staticmethod
    def get_all_coaches():
        """الحصول على جميع المدربين"""
        conn = get_db_connection()
        coaches = conn.execute('SELECT * FROM users WHERE user_type = "coach"').fetchall()
        conn.close()
        
        return [User(
            id=coach['id'],
            email=coach['email'],
            name=coach['name'],
            user_type=coach['user_type'],
            password_hash=coach['password_hash'],
            created_at=coach['created_at']
        ) for coach in coaches]


class CoachTraineeRelationship:
    """نموذج العلاقة بين المدرب والمتدرب"""
    
    def __init__(self, id=None, coach_id=None, trainee_id=None, created_at=None):
        self.id = id
        self.coach_id = coach_id
        self.trainee_id = trainee_id
        self.created_at = created_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def get_trainees_for_coach(coach_id):
        """الحصول على جميع المتدربين لمدرب معين"""
        conn = get_db_connection()
        relationships = conn.execute(
            '''SELECT u.* FROM users u
               JOIN coach_trainee_relationships r ON u.id = r.trainee_id
               WHERE r.coach_id = ? AND u.user_type = "trainee"''',
            (coach_id,)
        ).fetchall()
        conn.close()
        
        return [User(
            id=trainee['id'],
            email=trainee['email'],
            name=trainee['name'],
            user_type=trainee['user_type'],
            password_hash=trainee['password_hash'],
            created_at=trainee['created_at']
        ) for trainee in relationships]
    
    @staticmethod
    def get_coaches_for_trainee(trainee_id):
        """الحصول على جميع المدربين لمتدرب معين"""
        conn = get_db_connection()
        relationships = conn.execute(
            '''SELECT u.* FROM users u
               JOIN coach_trainee_relationships r ON u.id = r.coach_id
               WHERE r.trainee_id = ? AND u.user_type = "coach"''',
            (trainee_id,)
        ).fetchall()
        conn.close()
        
        return [User(
            id=coach['id'],
            email=coach['email'],
            name=coach['name'],
            user_type=coach['user_type'],
            password_hash=coach['password_hash'],
            created_at=coach['created_at']
        ) for coach in relationships]
    
    def save(self):
        """حفظ العلاقة في قاعدة البيانات"""
        conn = get_db_connection()
        
        # التحقق من وجود العلاقة
        existing = conn.execute(
            'SELECT id FROM coach_trainee_relationships WHERE coach_id = ? AND trainee_id = ?',
            (self.coach_id, self.trainee_id)
        ).fetchone()
        
        if existing:
            self.id = existing['id']
        else:
            # إضافة علاقة جديدة
            cursor = conn.execute(
                'INSERT INTO coach_trainee_relationships (coach_id, trainee_id, created_at) VALUES (?, ?, ?)',
                (self.coach_id, self.trainee_id, self.created_at)
            )
            self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return self.id
    
    @staticmethod
    def delete(coach_id, trainee_id):
        """حذف العلاقة بين المدرب والمتدرب"""
        conn = get_db_connection()
        conn.execute(
            'DELETE FROM coach_trainee_relationships WHERE coach_id = ? AND trainee_id = ?',
            (coach_id, trainee_id)
        )
        conn.commit()
        conn.close()


def get_db_connection():
    """إنشاء اتصال بقاعدة البيانات"""
    db_path = 'src/static/data/workout_app.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    conn = get_db_connection()
    
    # إنشاء جدول المستخدمين
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        user_type TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    # إنشاء جدول العلاقات بين المدربين والمتدربين
    conn.execute('''
    CREATE TABLE IF NOT EXISTS coach_trainee_relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coach_id INTEGER NOT NULL,
        trainee_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (coach_id) REFERENCES users (id),
        FOREIGN KEY (trainee_id) REFERENCES users (id),
        UNIQUE(coach_id, trainee_id)
    )
    ''')
    
    # إنشاء جدول الإشعارات
    conn.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()
