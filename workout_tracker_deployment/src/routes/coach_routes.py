from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from src.models.workout import WorkoutModel
from src.utils.chart_utils import create_interactive_chart, create_comparison_chart
from datetime import datetime
import pandas as pd
import json

# إنشاء مسار للمدربين
coach_bp = Blueprint('coach', __name__)
workout_model = WorkoutModel()

@coach_bp.route('/dashboard')
@login_required
def dashboard():
    """لوحة تحكم المدرب"""
    if not current_user.is_coach():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('trainee.dashboard'))
    
    # الحصول على المتدربين الذين يشرف عليهم المدرب
    from src.models.user import CoachTraineeRelationship, User
    trainees = CoachTraineeRelationship.get_trainees_for_coach(current_user.id)
    
    # إحصائيات عامة
    stats = {
        'total_trainees': len(trainees),
        'active_trainees': 0,
        'total_workouts': 0,
        'recent_activities': []
    }
    
    # حساب المتدربين النشطين وإجمالي التمارين
    if trainees:
        active_count = 0
        total_workouts = 0
        recent_activities = []
        
        for trainee in trainees:
            workouts = workout_model.get_user_workouts(trainee.id)
            
            if not workouts.empty:
                # التحقق من النشاط في آخر 30 يوم
                last_30_days = (datetime.now() - workouts['date'].max()).days <= 30
                if last_30_days:
                    active_count += 1
                
                total_workouts += len(workouts)
                
                # إضافة آخر نشاط
                if not workouts.empty:
                    last_workout = workouts.iloc[-1]
                    recent_activities.append({
                        'trainee_id': trainee.id,
                        'trainee_name': trainee.name,
                        'type': 'تمرين جديد',
                        'date': last_workout['date']
                    })
        
        stats['active_trainees'] = active_count
        stats['total_workouts'] = total_workouts
        
        # ترتيب الأنشطة الأخيرة حسب التاريخ
        stats['recent_activities'] = sorted(
            recent_activities, 
            key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), 
            reverse=True
        )[:5]  # أخذ آخر 5 أنشطة فقط
    
    # الحصول على الإشعارات غير المقروءة
    from src.models.notification import Notification
    notifications = Notification.get_unread_notifications(current_user.id)
    
    return render_template('coach/dashboard.html', 
                          trainees=trainees,
                          stats=stats,
                          exercises=workout_model.get_exercises(),
                          notifications=notifications)

@coach_bp.route('/trainees')
@login_required
def trainees():
    """إدارة المتدربين"""
    if not current_user.is_coach():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('trainee.dashboard'))
    
    # الحصول على المتدربين الذين يشرف عليهم المدرب
    from src.models.user import CoachTraineeRelationship, User
    trainees = CoachTraineeRelationship.get_trainees_for_coach(current_user.id)
    
    # الحصول على جميع المتدربين المتاحين للإضافة
    all_trainees = User.get_all_trainees()
    available_trainees = [t for t in all_trainees if t not in trainees]
    
    return render_template('coach/trainees.html', 
                          trainees=trainees,
                          available_trainees=available_trainees)

@coach_bp.route('/add_trainee/<int:trainee_id>', methods=['POST'])
@login_required
def add_trainee(trainee_id):
    """إضافة متدرب جديد"""
    if not current_user.is_coach():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('trainee.dashboard'))
    
    from src.models.user import CoachTraineeRelationship, User
    trainee = User.get_by_id(trainee_id)
    
    if not trainee or not trainee.is_trainee():
        flash('المتدرب غير موجود', 'error')
        return redirect(url_for('coach.trainees'))
    
    # إضافة العلاقة بين المدرب والمتدرب
    CoachTraineeRelationship.add_relationship(current_user.id, trainee_id)
    
    # إرسال إشعار للمتدرب
    from src.models.notification import Notification
    notification = Notification(
        user_id=trainee_id,
        message=f"تمت إضافتك كمتدرب للمدرب {current_user.name}"
    )
    notification.save()
    
    flash(f'تمت إضافة المتدرب {trainee.name} بنجاح', 'success')
    return redirect(url_for('coach.trainees'))

@coach_bp.route('/remove_trainee/<int:trainee_id>', methods=['POST'])
@login_required
def remove_trainee(trainee_id):
    """إزالة متدرب"""
    if not current_user.is_coach():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('trainee.dashboard'))
    
    from src.models.user import CoachTraineeRelationship, User
    trainee = User.get_by_id(trainee_id)
    
    if not trainee:
        flash('المتدرب غير موجود', 'error')
        return redirect(url_for('coach.trainees'))
    
    # إزالة العلاقة بين المدرب والمتدرب
    CoachTraineeRelationship.remove_relationship(current_user.id, trainee_id)
    
    # إرسال إشعار للمتدرب
    from src.models.notification import Notification
    notification = Notification(
        user_id=trainee_id,
        message=f"تمت إزالتك من قائمة متدربي المدرب {current_user.name}"
    )
    notification.save()
    
    flash(f'تمت إزالة المتدرب {trainee.name} بنجاح', 'success')
    return redirect(url_for('coach.trainees'))

@coach_bp.route('/trainee/<int:trainee_id>')
@login_required
def view_trainee(trainee_id):
    """عرض تقدم المتدرب"""
    if not current_user.is_coach():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('trainee.dashboard'))
    
    from src.models.user import User, CoachTraineeRelationship
    trainee = User.get_by_id(trainee_id)
    
    if not trainee or not trainee.is_trainee():
        flash('المتدرب غير موجود', 'error')
        return redirect(url_for('coach.dashboard'))
    
    # التحقق من أن المدرب يشرف على هذا المتدرب
    if not CoachTraineeRelationship.check_relationship(current_user.id, trainee_id):
        flash('غير مصرح لك بالوصول إلى بيانات هذا المتدرب', 'error')
        return redirect(url_for('coach.dashboard'))
    
    # الحصول على بيانات تمارين المتدرب
    workouts = workout_model.get_user_workouts(trainee_id)
    exercises = workout_model.get_exercises()
    
    # إنشاء رسم بياني للتقدم
    chart_data = create_interactive_chart(workouts, exercises)
    
    # تحليل التقدم
    progress_analysis = analyze_trainee_progress(workouts, exercises)
    
    return render_template('coach/view_trainee.html', 
                          trainee=trainee,
                          workouts=workouts.to_dict('records') if not workouts.empty else [],
                          exercises=exercises,
                          chart_data=chart_data,
                          progress_analysis=progress_analysis)

@coach_bp.route('/trainee/<int:trainee_id>/stats')
@login_required
def trainee_stats(trainee_id):
    """إحصائيات المتدرب"""
    if not current_user.is_coach():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('trainee.dashboard'))
    
    from src.models.user import User, CoachTraineeRelationship
    trainee = User.get_by_id(trainee_id)
    
    if not trainee or not trainee.is_trainee():
        flash('المتدرب غير موجود', 'error')
        return redirect(url_for('coach.dashboard'))
    
    # التحقق من أن المدرب يشرف على هذا المتدرب
    if not CoachTraineeRelationship.check_relationship(current_user.id, trainee_id):
        flash('غير مصرح لك بالوصول إلى بيانات هذا المتدرب', 'error')
        return redirect(url_for('coach.dashboard'))
    
    # الحصول على بيانات تمارين المتدرب
    workouts = workout_model.get_user_workouts(trainee_id)
    exercises = workout_model.get_exercises()
    
    # إحصائيات
    stats = {
        'total_workouts': len(workouts) if not workouts.empty else 0,
        'workout_frequency': calculate_workout_frequency(workouts),
        'strongest_exercises': find_strongest_exercises(workouts, exercises),
        'weakest_exercises': find_weakest_exercises(workouts, exercises),
        'recent_improvements': find_recent_improvements(workouts, exercises),
        'weight_progression': analyze_weight_progression(workouts, exercises),
        'resistance_usage': analyze_resistance_usage(workouts, exercises)
    }
    
    return render_template('coach/trainee_stats.html', 
                          trainee=trainee,
                          stats=stats,
                          exercises=exercises)

@coach_bp.route('/send_notification/<int:trainee_id>', methods=['POST'])
@login_required
def send_notification(trainee_id):
    """إرسال إشعار للمتدرب"""
    if not current_user.is_coach():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('trainee.dashboard'))
    
    from src.models.user import User, CoachTraineeRelationship
    trainee = User.get_by_id(trainee_id)
    
    if not trainee or not trainee.is_trainee():
        flash('المتدرب غير موجود', 'error')
        return redirect(url_for('coach.dashboard'))
    
    # التحقق من أن المدرب يشرف على هذا المتدرب
    if not CoachTraineeRelationship.check_relationship(current_user.id, trainee_id):
        flash('غير مصرح لك بالوصول إلى بيانات هذا المتدرب', 'error')
        return redirect(url_for('coach.dashboard'))
    
    message = request.form.get('message', '')
    
    if message:
        from src.models.notification import Notification
        notification = Notification(
            user_id=trainee_id,
            message=f"رسالة من المدرب {current_user.name}: {message}"
        )
        notification.save()
        
        flash('تم إرسال الإشعار بنجاح', 'success')
    else:
        flash('الرسالة مطلوبة', 'error')
    
    return redirect(url_for('coach.view_trainee', trainee_id=trainee_id))

@coach_bp.route('/export_trainee_data/<int:trainee_id>')
@login_required
def export_trainee_data(trainee_id):
    """تصدير بيانات المتدرب"""
    if not current_user.is_coach():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('trainee.dashboard'))
    
    from src.models.user import User, CoachTraineeRelationship
    trainee = User.get_by_id(trainee_id)
    
    if not trainee or not trainee.is_trainee():
        flash('المتدرب غير موجود', 'error')
        return redirect(url_for('coach.dashboard'))
    
    # التحقق من أن المدرب يشرف على هذا المتدرب
    if not CoachTraineeRelationship.check_relationship(current_user.id, trainee_id):
        flash('غير مصرح لك بالوصول إلى بيانات هذا المتدرب', 'error')
        return redirect(url_for('coach.dashboard'))
    
    filename = f'src/static/data/trainee_export_{trainee_id}.xlsx'
    workout_model.export_to_excel(trainee_id, filename)
    
    from flask import send_file
    return send_file(filename, 
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=f'تمارين_{trainee.name}.xlsx')

@coach_bp.route('/update_trainee_chart/<int:trainee_id>')
@login_required
def update_trainee_chart(trainee_id):
    """تحديث الرسم البياني للمتدرب"""
    if not current_user.is_coach():
        return jsonify({'error': 'غير مصرح لك بالوصول إلى هذه الصفحة'})
    
    from src.models.user import CoachTraineeRelationship
    
    # التحقق من أن المدرب يشرف على هذا المتدرب
    if not CoachTraineeRelationship.check_relationship(current_user.id, trainee_id):
        return jsonify({'error': 'غير مصرح لك بالوصول إلى بيانات هذا المتدرب'})
    
    chart_type = request.args.get('type', 'line')
    time_range = request.args.get('range', 'all')
    
    # الحصول على بيانات تمارين المتدرب
    workouts = workout_model.get_user_workouts(trainee_id)
    exercises = workout_model.get_exercises()
    
    # تطبيق فلتر الفترة الزمنية
    if time_range != 'all' and not workouts.empty:
        end_date = datetime.now()
        
        if time_range == 'month':
            start_date = end_date - timedelta(days=30)
        elif time_range == '3months':
            start_date = end_date - timedelta(days=90)
        elif time_range == '6months':
            start_date = end_date - timedelta(days=180)
        elif time_range == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = workouts['Date'].min()
        
        workouts = workouts[workouts['Date'] >= start_date]
    
    # إنشاء الرسم البياني المناسب
    if chart_type == 'radar':
        chart_data = create_radar_chart(workouts, exercises)
    elif chart_type == 'heatmap':
        chart_data = create_progress_heatmap(workouts, exercises)
    elif chart_type == 'weekly':
        chart_data = create_weekly_summary_chart(workouts, exercises)
    else:  # line
        chart_data = create_interactive_chart(workouts, exercises)
    
    return jsonify({'chart_data': chart_data})

@coach_bp.route('/get_comparison_data')
@login_required
def get_comparison_data():
    """الحصول على بيانات مقارنة المتدربين"""
    if not current_user.is_coach():
        return jsonify({'error': 'غير مصرح لك بالوصول إلى هذه الصفحة'})
    
    exercise = request.args.get('exercise', '')
    
    # الحصول على المتدربين الذين يشرف عليهم المدرب
    from src.models.user import CoachTraineeRelationship
    trainees = CoachTraineeRelationship.get_trainees_for_coach(current_user.id)
    
    if not trainees:
        return jsonify({'chart_data': '{}'})
    
    # جمع بيانات التمارين لكل متدرب
    trainee_data = {}
    
    for trainee in trainees:
        workouts = workout_model.get_user_workouts(trainee.id)
        
        if not workouts.empty and exercise in workouts.columns:
            exercise_data = workouts[['date', exercise]].dropna(subset=[exercise])
            
            if not exercise_data.empty:
                trainee_data[trainee.name] = exercise_data.to_dict('records')
    
    # إنشاء رسم بياني للمقارنة
    chart_data = create_comparison_chart(trainee_data, exercise)
    
    return jsonify({'chart_data': chart_data})

@coach_bp.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """تعليم الإشعار كمقروء"""
    if not current_user.is_coach():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('trainee.dashboard'))
    
    from src.models.notification import Notification
    notification = Notification.get_by_id(notification_id)
    
    if notification and notification.user_id == current_user.id:
        notification.mark_as_read()
        flash('تم تعليم الإشعار كمقروء', 'success')
    else:
        flash('غير مصرح لك بالوصول إلى هذا الإشعار', 'error')
    
    return redirect(url_for('coach.dashboard'))

@coach_bp.route('/mark_all_notifications_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """تعليم جميع الإشعارات كمقروءة"""
    if not current_user.is_coach():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('trainee.dashboard'))
    
    from src.models.notification import Notification
    Notification.mark_all_as_read(current_user.id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    flash('تم تعليم جميع الإشعارات كمقروءة', 'success')
    return redirect(url_for('coach.dashboard'))

# وظائف مساعدة لتحليل البيانات

def analyze_trainee_progress(workouts, exercises):
    """تحليل تقدم المتدرب"""
    if workouts.empty:
        return {
            'overall': 'لا توجد بيانات كافية للتحليل',
            'exercises': {}
        }
    
    # تحليل عام
    workout_count = len(workouts)
    
    if workout_count < 3:
        overall = 'لا توجد بيانات كافية للتحليل، يجب إضافة المزيد من التمارين'
    else:
        # حساب معدل التحسن العام
        improvement_rates = []
        
        for ex in exercises:
            if ex in workouts.columns:
                ex_data = workouts[['date', ex]].dropna(subset=[ex])
                
                if len(ex_data) >= 3:
                    first_value = ex_data.iloc[0][ex]
                    last_value = ex_data.iloc[-1][ex]
                    
                    if first_value > 0:
                        improvement = (last_value - first_value) / first_value * 100
                        improvement_rates.append(improvement)
        
        if improvement_rates:
            avg_improvement = sum(improvement_rates) / len(improvement_rates)
            
            if avg_improvement > 20:
                overall = 'تقدم ممتاز! استمر في العمل الجيد'
            elif avg_improvement > 10:
                overall = 'تقدم جيد، يمكن تحسين بعض التمارين'
            elif avg_improvement > 0:
                overall = 'تقدم بطيء، يجب زيادة التركيز على التمارين'
            else:
                overall = 'لا يوجد تقدم، يجب مراجعة خطة التمارين'
        else:
            overall = 'لا توجد بيانات كافية للتحليل'
    
    # تحليل كل تمرين
    exercise_analysis = {}
    
    for ex in exercises:
        if ex in workouts.columns:
            ex_data = workouts[['date', ex]].dropna(subset=[ex])
            
            if len(ex_data) >= 3:
                first_value = ex_data.iloc[0][ex]
                last_value = ex_data.iloc[-1][ex]
                
                if first_value > 0:
                    improvement = (last_value - first_value) / first_value * 100
                    
                    if improvement > 30:
                        exercise_analysis[ex] = f'تحسن ممتاز بنسبة {improvement:.1f}%'
                    elif improvement > 15:
                        exercise_analysis[ex] = f'تحسن جيد بنسبة {improvement:.1f}%'
                    elif improvement > 5:
                        exercise_analysis[ex] = f'تحسن بسيط بنسبة {improvement:.1f}%'
                    elif improvement > -5:
                        exercise_analysis[ex] = 'لا يوجد تغيير ملحوظ'
                    else:
                        exercise_analysis[ex] = f'تراجع في الأداء بنسبة {-improvement:.1f}%'
                else:
                    exercise_analysis[ex] = 'لا يمكن حساب نسبة التحسن'
            else:
                exercise_analysis[ex] = 'لا توجد بيانات كافية للتحليل'
    
    return {
        'overall': overall,
        'exercises': exercise_analysis
    }

def calculate_workout_frequency(workouts):
    """حساب معدل تكرار التمارين"""
    if workouts.empty:
        return 'لا توجد بيانات'
    
    workout_count = len(workouts)
    
    if workout_count < 2:
        return 'لا توجد بيانات كافية'
    
    # تحويل التواريخ إلى كائنات datetime
    dates = [datetime.strptime(date, '%Y-%m-%d') for date in workouts['date']]
    
    # حساب الفترة الزمنية بين أول وآخر تمرين
    first_date = min(dates)
    last_date = max(dates)
    days_diff = (last_date - first_date).days
    
    if days_diff == 0:
        return 'جميع التمارين في نفس اليوم'
    
    # حساب معدل التمارين في الأسبوع
    weeks = days_diff / 7
    workouts_per_week = workout_count / weeks if weeks > 0 else workout_count
    
    if workouts_per_week >= 5:
        return f'{workouts_per_week:.1f} تمارين في الأسبوع (ممتاز)'
    elif workouts_per_week >= 3:
        return f'{workouts_per_week:.1f} تمارين في الأسبوع (جيد)'
    elif workouts_per_week >= 1:
        return f'{workouts_per_week:.1f} تمارين في الأسبوع (متوسط)'
    else:
        return f'{workouts_per_week:.1f} تمارين في الأسبوع (منخفض)'

def find_strongest_exercises(workouts, exercises):
    """البحث عن أقوى التمارين"""
    if workouts.empty:
        return []
    
    strongest = []
    
    for ex in exercises:
        if ex in workouts.columns:
            ex_data = workouts[ex].dropna()
            
            if not ex_data.empty:
                max_value = ex_data.max()
                max_date = workouts.loc[ex_data.idxmax(), 'date']
                
                strongest.append({
                    'name': ex,
                    'value': max_value,
                    'date': max_date
                })
    
    # ترتيب التمارين حسب القيمة النسبية
    for ex in strongest:
        ex_data = workouts[ex['name']].dropna()
        if not ex_data.empty:
            avg_value = ex_data.mean()
            if avg_value > 0:
                ex['relative_strength'] = ex['value'] / avg_value
            else:
                ex['relative_strength'] = 1
    
    strongest.sort(key=lambda x: x.get('relative_strength', 0), reverse=True)
    
    return strongest[:3]  # إرجاع أقوى 3 تمارين

def find_weakest_exercises(workouts, exercises):
    """البحث عن أضعف التمارين"""
    if workouts.empty:
        return []
    
    weakest = []
    
    for ex in exercises:
        if ex in workouts.columns:
            ex_data = workouts[ex].dropna()
            
            if not ex_data.empty:
                min_value = ex_data.min()
                min_date = workouts.loc[ex_data.idxmin(), 'date']
                
                weakest.append({
                    'name': ex,
                    'value': min_value,
                    'date': min_date
                })
    
    # ترتيب التمارين حسب القيمة النسبية
    for ex in weakest:
        ex_data = workouts[ex['name']].dropna()
        if not ex_data.empty:
            avg_value = ex_data.mean()
            if avg_value > 0:
                ex['relative_weakness'] = avg_value / ex['value']
            else:
                ex['relative_weakness'] = 1
    
    weakest.sort(key=lambda x: x.get('relative_weakness', 0), reverse=True)
    
    return weakest[:3]  # إرجاع أضعف 3 تمارين

def find_recent_improvements(workouts, exercises):
    """البحث عن التحسينات الأخيرة"""
    if workouts.empty or len(workouts) < 2:
        return []
    
    improvements = []
    
    for ex in exercises:
        if ex in workouts.columns:
            ex_data = workouts[['date', ex]].dropna(subset=[ex])
            
            if len(ex_data) >= 2:
                # مقارنة آخر قيمتين
                last_value = ex_data.iloc[-1][ex]
                prev_value = ex_data.iloc[-2][ex]
                
                if prev_value > 0:
                    improvement = (last_value - prev_value) / prev_value * 100
                    
                    if improvement > 0:
                        improvements.append({
                            'name': ex,
                            'improvement': improvement,
                            'from_value': prev_value,
                            'to_value': last_value,
                            'date': ex_data.iloc[-1]['date']
                        })
    
    # ترتيب التحسينات حسب النسبة
    improvements.sort(key=lambda x: x['improvement'], reverse=True)
    
    return improvements[:5]  # إرجاع أفضل 5 تحسينات

def analyze_weight_progression(workouts, exercises):
    """تحليل تقدم الأوزان"""
    if workouts.empty:
        return {}
    
    weight_progression = {}
    
    for ex in exercises:
        weight_key = f"{ex}_weight"
        
        if ex in workouts.columns and weight_key in workouts.columns:
            weight_data = workouts[['date', ex, weight_key]].dropna(subset=[ex, weight_key])
            
            if not weight_data.empty and len(weight_data) >= 2:
                first_weight = weight_data.iloc[0][weight_key]
                last_weight = weight_data.iloc[-1][weight_key]
                
                if first_weight > 0:
                    improvement = (last_weight - first_weight) / first_weight * 100
                    
                    weight_progression[ex] = {
                        'first_weight': first_weight,
                        'last_weight': last_weight,
                        'improvement': improvement,
                        'status': 'تحسن' if improvement > 0 else 'تراجع' if improvement < 0 else 'ثبات'
                    }
    
    return weight_progression

def analyze_resistance_usage(workouts, exercises):
    """تحليل استخدام المقاومة"""
    if workouts.empty:
        return {}
    
    resistance_usage = {}
    
    for ex in exercises:
        resistance_key = f"{ex}_resistance"
        
        if ex in workouts.columns and resistance_key in workouts.columns:
            resistance_data = workouts[['date', ex, resistance_key]].dropna(subset=[ex, resistance_key])
            
            if not resistance_data.empty:
                # حساب تكرار كل مستوى مقاومة
                resistance_counts = resistance_data[resistance_key].value_counts().to_dict()
                
                # تحويل العدد إلى نسبة مئوية
                total = sum(resistance_counts.values())
                resistance_percentages = {k: (v / total * 100) for k, v in resistance_counts.items()}
                
                resistance_usage[ex] = {
                    'counts': resistance_counts,
                    'percentages': resistance_percentages
                }
    
    return resistance_usage
