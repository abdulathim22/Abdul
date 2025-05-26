import sqlite3
from datetime import datetime

class Notification:
    """نموذج الإشعارات"""
    
    def __init__(self, id=None, user_id=None, message=None, is_read=0, created_at=None):
        self.id = id
        self.user_id = user_id
        self.message = message
        self.is_read = is_read
        self.created_at = created_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def get_by_id(notification_id):
        """الحصول على الإشعار بواسطة المعرف"""
        from src.models.user import get_db_connection
        conn = get_db_connection()
        notification = conn.execute('SELECT * FROM notifications WHERE id = ?', (notification_id,)).fetchone()
        conn.close()
        
        if notification:
            return Notification(
                id=notification['id'],
                user_id=notification['user_id'],
                message=notification['message'],
                is_read=notification['is_read'],
                created_at=notification['created_at']
            )
        return None
    
    @staticmethod
    def get_user_notifications(user_id):
        """الحصول على جميع إشعارات المستخدم"""
        from src.models.user import get_db_connection
        conn = get_db_connection()
        notifications = conn.execute(
            'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()
        conn.close()
        
        return [Notification(
            id=notification['id'],
            user_id=notification['user_id'],
            message=notification['message'],
            is_read=notification['is_read'],
            created_at=notification['created_at']
        ) for notification in notifications]
    
    @staticmethod
    def get_unread_notifications(user_id):
        """الحصول على الإشعارات غير المقروءة للمستخدم"""
        from src.models.user import get_db_connection
        conn = get_db_connection()
        notifications = conn.execute(
            'SELECT * FROM notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()
        conn.close()
        
        return [Notification(
            id=notification['id'],
            user_id=notification['user_id'],
            message=notification['message'],
            is_read=notification['is_read'],
            created_at=notification['created_at']
        ) for notification in notifications]
    
    def save(self):
        """حفظ الإشعار في قاعدة البيانات"""
        from src.models.user import get_db_connection
        conn = get_db_connection()
        
        if self.id:
            # تحديث إشعار موجود
            conn.execute(
                'UPDATE notifications SET user_id = ?, message = ?, is_read = ? WHERE id = ?',
                (self.user_id, self.message, self.is_read, self.id)
            )
        else:
            # إضافة إشعار جديد
            cursor = conn.execute(
                'INSERT INTO notifications (user_id, message, is_read, created_at) VALUES (?, ?, ?, ?)',
                (self.user_id, self.message, self.is_read, self.created_at)
            )
            self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return self.id
    
    def mark_as_read(self):
        """تعليم الإشعار كمقروء"""
        self.is_read = 1
        self.save()
    
    @staticmethod
    def mark_all_as_read(user_id):
        """تعليم جميع إشعارات المستخدم كمقروءة"""
        from src.models.user import get_db_connection
        conn = get_db_connection()
        conn.execute(
            'UPDATE notifications SET is_read = 1 WHERE user_id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(notification_id):
        """حذف إشعار"""
        from src.models.user import get_db_connection
        conn = get_db_connection()
        conn.execute('DELETE FROM notifications WHERE id = ?', (notification_id,))
        conn.commit()
        conn.close()
