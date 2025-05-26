from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from src.models.workout import WorkoutModel
from src.utils.chart_utils import create_interactive_chart, create_radar_chart, create_progress_heatmap, create_weekly_summary_chart
from datetime import datetime, timedelta
import pandas as pd
import json

# إنشاء مسار للمتدربين
trainee_bp = Blueprint('trainee', __name__)
workout_model = WorkoutModel()

@trainee_bp.route('/dashboard')
@login_required
def dashboard():
    """لوحة تحكم المتدرب"""
    if not current_user.is_trainee():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('coach.dashboard'))
    
    # الحصول على المدربين المشرفين على المتدرب
    from src.models.user import CoachTraineeRelationship
    coaches = CoachTraineeRelationship.get_coaches_for_trainee(current_user.id)
    
    # الحصول على بيانات تمارين المتدرب
    workouts = workout_model.get_user_workouts(current_user.id)
    exercises = workout_model.get_exercises()
    
    # إنشاء رسم بياني للتقدم
    chart_data = create_interactive_chart(workouts, exercises)
    
    # الحصول على الإشعارات غير المقروءة
    from src.models.notification import Notification
    notifications = Notification.get_unread_notifications(current_user.id)
    
    return render_template('trainee/dashboard.html', 
                          coaches=coaches,
                          workouts=workouts.to_dict('records') if not workouts.empty else [],
                          workout_dates=workouts['date'].tolist() if not workouts.empty else [],
                          exercises=exercises,
                          chart_data=chart_data,
                          notifications=notifications)

@trainee_bp.route('/add', methods=['POST'])
@login_required
def add_workout():
    """إضافة تمرين جديد"""
    if not current_user.is_trainee():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('coach.dashboard'))
    
    date_str = request.form.get('date') or datetime.today().strftime('%Y-%m-%d')
    
    # جمع بيانات التمارين من النموذج
    exercise_data = {}
    for ex in workout_model.get_exercises().keys():
        value = request.form.get(ex, '')
        weight = request.form.get(f"{ex}_weight", '0')
        resistance = request.form.get(f"{ex}_resistance", '')
        notes = request.form.get(f"{ex}_notes", '')
        
        if value:
            exercise_data[ex] = {
                'value': value,
                'weight': weight,
                'resistance_level': resistance,
                'notes': notes
            }
    
    # إضافة التمرين
    workout_model.add_workout(current_user.id, date_str, exercise_data)
    
    # إرسال إشعار للمدربين
    from src.models.user import CoachTraineeRelationship
    from src.models.notification import Notification
    
    coaches = CoachTraineeRelationship.get_coaches_for_trainee(current_user.id)
    for coach in coaches:
        notification = Notification(
            user_id=coach.id,
            message=f"قام المتدرب {current_user.name} بإضافة تمرين جديد بتاريخ {date_str}"
        )
        notification.save()
    
    flash('تمت إضافة التمرين بنجاح', 'success')
    return redirect(url_for('trainee.dashboard'))

@trainee_bp.route('/update/<int:workout_id>', methods=['POST'])
@login_required
def update_workout(workout_id):
    """تحديث تمرين موجود"""
    if not current_user.is_trainee():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('coach.dashboard'))
    
    date_str = request.form.get('date') or datetime.today().strftime('%Y-%m-%d')
    
    # جمع بيانات التمارين من النموذج
    exercise_data = {}
    for ex in workout_model.get_exercises().keys():
        value = request.form.get(ex, '')
        weight = request.form.get(f"{ex}_weight", '0')
        resistance = request.form.get(f"{ex}_resistance", '')
        notes = request.form.get(f"{ex}_notes", '')
        
        if value:
            exercise_data[ex] = {
                'value': value,
                'weight': weight,
                'resistance_level': resistance,
                'notes': notes
            }
    
    # تحديث التمرين
    workout_model.update_workout(workout_id, date_str, exercise_data)
    
    flash('تم تحديث التمرين بنجاح', 'success')
    return redirect(url_for('trainee.dashboard'))

@trainee_bp.route('/delete/<int:workout_id>', methods=['POST'])
@login_required
def delete_workout(workout_id):
    """حذف تمرين موجود"""
    if not current_user.is_trainee():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('coach.dashboard'))
    
    workout_model.delete_workout(workout_id)
    
    flash('تم حذف التمرين بنجاح', 'success')
    return redirect(url_for('trainee.dashboard'))

@trainee_bp.route('/add_exercise', methods=['POST'])
@login_required
def add_exercise():
    """إضافة نوع تمرين جديد"""
    if not current_user.is_trainee():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('coach.dashboard'))
    
    name = request.form.get('name', '')
    unit = request.form.get('unit', 'عدد')
    category = request.form.get('category', 'عام')
    
    if name:
        workout_model.add_exercise(name, unit, category)
        flash('تمت إضافة التمرين بنجاح', 'success')
    else:
        flash('اسم التمرين مطلوب', 'error')
    
    return redirect(url_for('trainee.dashboard'))

@trainee_bp.route('/export/excel', methods=['GET'])
@login_required
def export_excel():
    """تصدير البيانات إلى ملف Excel"""
    if not current_user.is_trainee():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('coach.dashboard'))
    
    filename = f'src/static/data/workout_export_{current_user.id}.xlsx'
    workout_model.export_to_excel(current_user.id, filename)
    
    from flask import send_file
    return send_file(filename, 
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name='تمارين_الشارع.xlsx')

@trainee_bp.route('/export/pdf', methods=['GET'])
@login_required
def export_pdf():
    """تصدير البيانات إلى ملف PDF"""
    if not current_user.is_trainee():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('coach.dashboard'))
    
    # الحصول على بيانات تمارين المتدرب
    workouts = workout_model.get_user_workouts(current_user.id)
    exercises = workout_model.get_exercises()
    
    # استخدام WeasyPrint لإنشاء ملف PDF
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    import pandas as pd
    
    # إنشاء محتوى HTML للتقرير
    lang = session.get('lang', 'ar')
    title = "تقرير تمارين الشارع" if lang == 'ar' else "Street Workout Report"
    date_label = "التاريخ" if lang == 'ar' else "Date"
    
    html_content = f"""
    <!DOCTYPE html>
    <html dir="{'rtl' if lang == 'ar' else 'ltr'}">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            @page {{ size: A4; margin: 1cm; }}
            body {{ 
                font-family: "DejaVu Sans", "Arial", sans-serif;
                direction: {'rtl' if lang == 'ar' else 'ltr'};
                text-align: {'right' if lang == 'ar' else 'left'};
            }}
            h1 {{ text-align: center; color: #3498db; }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 20px;
            }}
            th, td {{ 
                border: 1px solid #ddd; 
                padding: 8px; 
                text-align: center;
            }}
            th {{ 
                background-color: #2c3e50; 
                color: white; 
            }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .weight-badge {{
                display: inline-block;
                padding: 2px 5px;
                background-color: #3498db;
                color: white;
                border-radius: 3px;
                font-size: 0.8rem;
                margin-left: 5px;
            }}
            .resistance-badge {{
                display: inline-block;
                padding: 2px 5px;
                color: white;
                border-radius: 3px;
                font-size: 0.8rem;
                margin-left: 5px;
            }}
            .resistance-badge.light {{ background-color: #27ae60; }}
            .resistance-badge.medium {{ background-color: #f39c12; }}
            .resistance-badge.heavy {{ background-color: #e74c3c; }}
        </style>
    </head>
    <body>
        <h1>{title} - {current_user.name}</h1>
        <table>
            <thead>
                <tr>
                    <th>{date_label}</th>
    """
    
    # إضافة أعمدة التمارين
    for ex in exercises:
        html_content += f"<th>{ex}</th>"
    
    html_content += """
                </tr>
            </thead>
            <tbody>
    """
    
    # إضافة بيانات الجدول
    if not workouts.empty:
        for _, row in workouts.iterrows():
            html_content += f"<tr><td>{row['date']}</td>"
            
            for ex in exercises:
                if ex in row and not pd.isna(row[ex]):
                    html_content += f"<td>{int(row[ex])}"
                    
                    # إضافة الوزن إذا كان موجوداً
                    weight_key = f"{ex}_weight"
                    if weight_key in row and not pd.isna(row[weight_key]) and row[weight_key] > 0:
                        kg_text = "كجم" if lang == 'ar' else "kg"
                        html_content += f"<span class='weight-badge'>{row[weight_key]} {kg_text}</span>"
                    
                    # إضافة المقاومة إذا كانت موجودة
                    resistance_key = f"{ex}_resistance"
                    if resistance_key in row and not pd.isna(row[resistance_key]) and row[resistance_key]:
                        resistance_text = ""
                        if row[resistance_key] == 'light':
                            resistance_text = "خفيفة" if lang == 'ar' else "Light"
                        elif row[resistance_key] == 'medium':
                            resistance_text = "متوسطة" if lang == 'ar' else "Medium"
                        elif row[resistance_key] == 'heavy':
                            resistance_text = "ثقيلة" if lang == 'ar' else "Heavy"
                        
                        html_content += f"<span class='resistance-badge {row[resistance_key]}'>{resistance_text}</span>"
                    
                    html_content += "</td>"
                else:
                    html_content += "<td>-</td>"
            
            html_content += "</tr>"
    
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    # إنشاء ملف PDF
    font_config = FontConfiguration()
    pdf_path = f'src/static/data/workout_export_{current_user.id}.pdf'
    
    HTML(string=html_content).write_pdf(
        pdf_path,
        stylesheets=[],
        font_config=font_config
    )
    
    from flask import send_file
    return send_file(pdf_path, 
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name='تمارين_الشارع.pdf')

@trainee_bp.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """تعليم الإشعار كمقروء"""
    if not current_user.is_trainee():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('coach.dashboard'))
    
    from src.models.notification import Notification
    notification = Notification.get_by_id(notification_id)
    
    if notification and notification.user_id == current_user.id:
        notification.mark_as_read()
        flash('تم تعليم الإشعار كمقروء', 'success')
    else:
        flash('غير مصرح لك بالوصول إلى هذا الإشعار', 'error')
    
    return redirect(url_for('trainee.dashboard'))

@trainee_bp.route('/mark_all_notifications_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """تعليم جميع الإشعارات كمقروءة"""
    if not current_user.is_trainee():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('coach.dashboard'))
    
    from src.models.notification import Notification
    Notification.mark_all_as_read(current_user.id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    flash('تم تعليم جميع الإشعارات كمقروءة', 'success')
    return redirect(url_for('trainee.dashboard'))

@trainee_bp.route('/share/<int:workout_id>')
@login_required
def share_workout(workout_id):
    """مشاركة تمرين على وسائل التواصل الاجتماعي"""
    if not current_user.is_trainee():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('coach.dashboard'))
    
    # إنشاء رابط المشاركة
    share_url = url_for('trainee.view_shared_workout', 
                        workout_id=workout_id, 
                        user_id=current_user.id, 
                        _external=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'share_url': share_url})
    
    return render_template('trainee/share.html', share_url=share_url)

@trainee_bp.route('/shared/<int:user_id>/<int:workout_id>')
def view_shared_workout(user_id, workout_id):
    """عرض تمرين مشترك"""
    # الحصول على بيانات المستخدم
    from src.models.user import User
    user = User.get_by_id(user_id)
    
    if not user:
        flash('المستخدم غير موجود', 'error')
        return redirect(url_for('home'))
    
    # الحصول على بيانات التمرين
    workouts = workout_model.get_user_workouts(user_id)
    
    if workouts.empty:
        flash('التمرين غير موجود', 'error')
        return redirect(url_for('home'))
    
    # البحث عن التمرين المحدد
    workout = next((w for w in workouts.to_dict('records') if w['id'] == workout_id), None)
    
    if not workout:
        flash('التمرين غير موجود', 'error')
        return redirect(url_for('home'))
    
    exercises = workout_model.get_exercises()
    
    return render_template('trainee/shared_workout.html', 
                          user=user,
                          workout=workout,
                          exercises=exercises)

@trainee_bp.route('/update_chart')
@login_required
def update_chart():
    """تحديث الرسم البياني"""
    if not current_user.is_trainee():
        return jsonify({'error': 'غير مصرح لك بالوصول إلى هذه الصفحة'})
    
    chart_type = request.args.get('type', 'line')
    time_range = request.args.get('range', 'all')
    
    # الحصول على بيانات تمارين المتدرب
    workouts = workout_model.get_user_workouts(current_user.id)
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

@trainee_bp.route('/progress_analysis')
@login_required
def progress_analysis():
    """تحليل تقدم المتدرب"""
    if not current_user.is_trainee():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('coach.dashboard'))
    
    # الحصول على بيانات تمارين المتدرب
    workouts = workout_model.get_user_workouts(current_user.id)
    exercises = workout_model.get_exercises()
    
    # تحليل التقدم
    from src.routes.coach_routes import analyze_trainee_progress
    progress_analysis = analyze_trainee_progress(workouts, exercises)
    
    # إحصائيات إضافية
    from src.routes.coach_routes import calculate_workout_frequency, find_strongest_exercises, find_weakest_exercises, find_recent_improvements
    
    stats = {
        'total_workouts': len(workouts) if not workouts.empty else 0,
        'workout_frequency': calculate_workout_frequency(workouts),
        'strongest_exercises': find_strongest_exercises(workouts, exercises),
        'weakest_exercises': find_weakest_exercises(workouts, exercises),
        'recent_improvements': find_recent_improvements(workouts, exercises)
    }
    
    return render_template('trainee/progress_analysis.html', 
                          stats=stats,
                          progress_analysis=progress_analysis)

@trainee_bp.route('/weight_tracking')
@login_required
def weight_tracking():
    """تتبع الأوزان والمقاومة"""
    if not current_user.is_trainee():
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('coach.dashboard'))
    
    # الحصول على بيانات تمارين المتدرب
    workouts = workout_model.get_user_workouts(current_user.id)
    exercises = workout_model.get_exercises()
    
    # تحضير بيانات تتبع الأوزان
    weight_data = {}
    resistance_data = {}
    
    if not workouts.empty:
        for ex in exercises:
            weight_key = f"{ex}_weight"
            resistance_key = f"{ex}_resistance"
            
            if weight_key in workouts.columns:
                weight_df = workouts[['date', ex, weight_key]].dropna(subset=[ex, weight_key])
                if not weight_df.empty:
                    weight_data[ex] = weight_df.to_dict('records')
            
            if resistance_key in workouts.columns:
                resistance_df = workouts[['date', ex, resistance_key]].dropna(subset=[ex, resistance_key])
                if not resistance_df.empty:
                    resistance_data[ex] = resistance_df.to_dict('records')
    
    return render_template('trainee/weight_tracking.html', 
                          exercises=exercises,
                          weight_data=weight_data,
                          resistance_data=resistance_data)
