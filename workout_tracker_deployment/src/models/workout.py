import pandas as pd
import os
from datetime import datetime
import sqlite3

class WorkoutModel:
    """نموذج بيانات تمارين الشارع"""
    
    def __init__(self, data_file='src/static/data/workout_data.db'):
        """تهيئة النموذج مع ملف البيانات"""
        self.data_file = data_file
        self.default_exercises = {
            'Push-ups': 'عدد',
            'Pull-ups': 'عدد',
            'Pike Push-ups': 'عدد',
            'Dips': 'عدد',
            'Rows': 'عدد',
            'Tuck Planche Hold': 'ثواني',
            'Advanced Tuck Front Lever Hold': 'ثواني',
        }
        # التأكد من وجود مجلد البيانات
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        self.init_db()
        
    def init_db(self):
        """تهيئة قاعدة البيانات وإنشاء الجداول"""
        conn = self.get_db_connection()
        
        # إنشاء جدول التمارين
        conn.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            unit TEXT NOT NULL,
            category TEXT DEFAULT 'عام',
            created_at TEXT NOT NULL
        )
        ''')
        
        # إنشاء جدول سجلات التمارين
        conn.execute('''
        CREATE TABLE IF NOT EXISTS workout_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # إنشاء جدول تفاصيل التمارين
        conn.execute('''
        CREATE TABLE IF NOT EXISTS workout_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            value REAL NOT NULL,
            weight REAL DEFAULT 0,
            resistance_level TEXT DEFAULT NULL,
            notes TEXT DEFAULT NULL,
            FOREIGN KEY (workout_id) REFERENCES workout_records (id),
            FOREIGN KEY (exercise_id) REFERENCES exercises (id)
        )
        ''')
        
        # إضافة التمارين الافتراضية إذا لم تكن موجودة
        for name, unit in self.default_exercises.items():
            conn.execute(
                'INSERT OR IGNORE INTO exercises (name, unit, created_at) VALUES (?, ?, ?)',
                (name, unit, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
        
        conn.commit()
        conn.close()
    
    def get_db_connection(self):
        """إنشاء اتصال بقاعدة البيانات"""
        conn = sqlite3.connect(self.data_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_exercises(self):
        """الحصول على قائمة التمارين المتاحة ووحداتها"""
        conn = self.get_db_connection()
        exercises = conn.execute('SELECT id, name, unit, category FROM exercises').fetchall()
        conn.close()
        
        # تحويل النتائج إلى قاموس
        exercise_dict = {}
        for ex in exercises:
            exercise_dict[ex['name']] = ex['unit']
        
        return exercise_dict
    
    def get_exercises_with_details(self):
        """الحصول على قائمة التمارين مع جميع التفاصيل"""
        conn = self.get_db_connection()
        exercises = conn.execute('SELECT * FROM exercises').fetchall()
        conn.close()
        
        return [dict(ex) for ex in exercises]
    
    def add_exercise(self, name, unit, category='عام'):
        """إضافة نوع تمرين جديد"""
        conn = self.get_db_connection()
        
        try:
            conn.execute(
                'INSERT INTO exercises (name, unit, category, created_at) VALUES (?, ?, ?, ?)',
                (name, unit, category, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # التمرين موجود بالفعل
            conn.close()
            return False
    
    def delete_exercise(self, exercise_id):
        """حذف نوع تمرين"""
        conn = self.get_db_connection()
        
        # التحقق من وجود سجلات تمارين تستخدم هذا التمرين
        details = conn.execute(
            'SELECT COUNT(*) as count FROM workout_details WHERE exercise_id = ?',
            (exercise_id,)
        ).fetchone()
        
        if details['count'] > 0:
            # لا يمكن حذف التمرين لأنه مستخدم في سجلات
            conn.close()
            return False
        
        conn.execute('DELETE FROM exercises WHERE id = ?', (exercise_id,))
        conn.commit()
        conn.close()
        return True
    
    def add_workout(self, user_id, date_str, exercise_data):
        """إضافة تمرين جديد"""
        conn = self.get_db_connection()
        
        # تحويل التاريخ
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
        except:
            date = datetime.today().strftime('%Y-%m-%d')
        
        # إنشاء سجل تمرين جديد
        cursor = conn.execute(
            'INSERT INTO workout_records (user_id, date, created_at) VALUES (?, ?, ?)',
            (user_id, date, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        workout_id = cursor.lastrowid
        
        # إضافة تفاصيل التمارين
        for exercise_name, data in exercise_data.items():
            if not data.get('value'):
                continue
                
            # الحصول على معرف التمرين
            exercise = conn.execute(
                'SELECT id FROM exercises WHERE name = ?',
                (exercise_name,)
            ).fetchone()
            
            if not exercise:
                continue
                
            # إضافة تفاصيل التمرين
            conn.execute(
                '''INSERT INTO workout_details 
                   (workout_id, exercise_id, value, weight, resistance_level, notes) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    workout_id, 
                    exercise['id'], 
                    float(data.get('value', 0)),
                    float(data.get('weight', 0)),
                    data.get('resistance_level', None),
                    data.get('notes', None)
                )
            )
        
        conn.commit()
        conn.close()
        return workout_id
    
    def update_workout(self, workout_id, date_str, exercise_data):
        """تحديث بيانات تمرين موجود"""
        conn = self.get_db_connection()
        
        # تحويل التاريخ
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
        except:
            # الحصول على التاريخ الحالي
            current_date = conn.execute(
                'SELECT date FROM workout_records WHERE id = ?',
                (workout_id,)
            ).fetchone()
            date = current_date['date'] if current_date else datetime.today().strftime('%Y-%m-%d')
        
        # تحديث تاريخ التمرين
        conn.execute(
            'UPDATE workout_records SET date = ? WHERE id = ?',
            (date, workout_id)
        )
        
        # حذف تفاصيل التمرين الحالية
        conn.execute('DELETE FROM workout_details WHERE workout_id = ?', (workout_id,))
        
        # إضافة تفاصيل التمارين الجديدة
        for exercise_name, data in exercise_data.items():
            if not data.get('value'):
                continue
                
            # الحصول على معرف التمرين
            exercise = conn.execute(
                'SELECT id FROM exercises WHERE name = ?',
                (exercise_name,)
            ).fetchone()
            
            if not exercise:
                continue
                
            # إضافة تفاصيل التمرين
            conn.execute(
                '''INSERT INTO workout_details 
                   (workout_id, exercise_id, value, weight, resistance_level, notes) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    workout_id, 
                    exercise['id'], 
                    float(data.get('value', 0)),
                    float(data.get('weight', 0)),
                    data.get('resistance_level', None),
                    data.get('notes', None)
                )
            )
        
        conn.commit()
        conn.close()
        return True
    
    def delete_workout(self, workout_id):
        """حذف تمرين موجود"""
        conn = self.get_db_connection()
        
        # حذف تفاصيل التمرين
        conn.execute('DELETE FROM workout_details WHERE workout_id = ?', (workout_id,))
        
        # حذف سجل التمرين
        conn.execute('DELETE FROM workout_records WHERE id = ?', (workout_id,))
        
        conn.commit()
        conn.close()
        return True
    
    def get_user_workouts(self, user_id):
        """الحصول على جميع تمارين المستخدم"""
        conn = self.get_db_connection()
        
        # الحصول على سجلات التمارين
        workouts = conn.execute(
            '''SELECT wr.id, wr.date, wr.created_at
               FROM workout_records wr
               WHERE wr.user_id = ?
               ORDER BY wr.date DESC''',
            (user_id,)
        ).fetchall()
        
        result = []
        
        for workout in workouts:
            workout_dict = dict(workout)
            
            # الحصول على تفاصيل التمارين
            details = conn.execute(
                '''SELECT e.name, e.unit, wd.value, wd.weight, wd.resistance_level, wd.notes
                   FROM workout_details wd
                   JOIN exercises e ON wd.exercise_id = e.id
                   WHERE wd.workout_id = ?''',
                (workout['id'],)
            ).fetchall()
            
            # إضافة تفاصيل التمارين إلى القاموس
            for detail in details:
                workout_dict[detail['name']] = detail['value']
                workout_dict[f"{detail['name']}_weight"] = detail['weight']
                workout_dict[f"{detail['name']}_resistance"] = detail['resistance_level']
                workout_dict[f"{detail['name']}_notes"] = detail['notes']
            
            result.append(workout_dict)
        
        conn.close()
        
        # تحويل النتائج إلى DataFrame
        if result:
            df = pd.DataFrame(result)
            # تحويل عمود التاريخ
            df['Date'] = pd.to_datetime(df['date'])
            return df
        else:
            # إنشاء DataFrame فارغ
            return pd.DataFrame(columns=['id', 'date', 'created_at', 'Date'])
    
    def get_all_workouts(self):
        """الحصول على جميع بيانات التمارين (للتوافق مع الكود القديم)"""
        # هذه الدالة للتوافق مع الكود القديم فقط
        # في التطبيق الجديد، يجب استخدام get_user_workouts
        return pd.DataFrame(columns=['Date'])
    
    def export_to_excel(self, user_id, filename):
        """تصدير بيانات المستخدم إلى ملف Excel"""
        df = self.get_user_workouts(user_id)
        
        if not df.empty:
            df.to_excel(filename, index=False)
            return os.path.exists(filename)
        return False
