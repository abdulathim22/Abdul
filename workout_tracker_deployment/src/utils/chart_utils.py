import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

def create_interactive_chart(workouts, exercises):
    """إنشاء رسم بياني تفاعلي للتقدم"""
    if workouts.empty:
        # إنشاء رسم بياني فارغ
        fig = go.Figure()
        fig.update_layout(
            title="لا توجد بيانات كافية لعرض التقدم",
            xaxis_title="التاريخ",
            yaxis_title="القيمة",
            template="plotly_white"
        )
        return json.dumps(fig.to_dict())
    
    fig = go.Figure()
    
    # إضافة خط لكل تمرين
    for ex in exercises:
        if ex in workouts.columns:
            ex_data = workouts[['date', ex]].dropna(subset=[ex])
            
            if not ex_data.empty:
                fig.add_trace(go.Scatter(
                    x=ex_data['date'],
                    y=ex_data[ex],
                    mode='lines+markers',
                    name=ex,
                    hovertemplate='%{y} ' + exercises.get(ex, '')
                ))
    
    # تخصيص تنسيق الرسم البياني
    fig.update_layout(
        title="تطور أداء التمارين",
        xaxis_title="التاريخ",
        yaxis_title="القيمة",
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white",
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return json.dumps(fig.to_dict())

def create_radar_chart(workouts, exercises):
    """إنشاء رسم بياني راداري للتقدم"""
    if workouts.empty:
        # إنشاء رسم بياني فارغ
        fig = go.Figure()
        fig.update_layout(
            title="لا توجد بيانات كافية لعرض التقدم",
            template="plotly_white"
        )
        return json.dumps(fig.to_dict())
    
    # الحصول على أحدث قيم للتمارين
    latest_values = {}
    max_values = {}
    
    for ex in exercises:
        if ex in workouts.columns:
            ex_data = workouts[ex].dropna()
            
            if not ex_data.empty:
                latest_values[ex] = ex_data.iloc[-1]
                max_values[ex] = ex_data.max()
    
    if not latest_values:
        # إنشاء رسم بياني فارغ
        fig = go.Figure()
        fig.update_layout(
            title="لا توجد بيانات كافية لعرض التقدم",
            template="plotly_white"
        )
        return json.dumps(fig.to_dict())
    
    # تحضير البيانات للرسم الراداري
    categories = list(latest_values.keys())
    
    # تطبيع القيم بالنسبة للقيمة القصوى
    normalized_values = [latest_values[ex] / max_values[ex] * 100 if max_values[ex] > 0 else 0 for ex in categories]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=normalized_values,
        theta=categories,
        fill='toself',
        name='القيم الحالية'
    ))
    
    fig.update_layout(
        title="تحليل راداري للتمارين",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        template="plotly_white"
    )
    
    return json.dumps(fig.to_dict())

def create_progress_heatmap(workouts, exercises):
    """إنشاء خريطة حرارية لتقدم التمارين"""
    if workouts.empty:
        # إنشاء رسم بياني فارغ
        fig = go.Figure()
        fig.update_layout(
            title="لا توجد بيانات كافية لعرض التقدم",
            template="plotly_white"
        )
        return json.dumps(fig.to_dict())
    
    # تحضير البيانات للخريطة الحرارية
    heatmap_data = []
    
    for ex in exercises:
        if ex in workouts.columns:
            ex_data = workouts[['date', ex]].dropna(subset=[ex])
            
            if not ex_data.empty:
                for _, row in ex_data.iterrows():
                    heatmap_data.append({
                        'date': row['date'],
                        'exercise': ex,
                        'value': row[ex]
                    })
    
    if not heatmap_data:
        # إنشاء رسم بياني فارغ
        fig = go.Figure()
        fig.update_layout(
            title="لا توجد بيانات كافية لعرض التقدم",
            template="plotly_white"
        )
        return json.dumps(fig.to_dict())
    
    # تحويل البيانات إلى DataFrame
    heatmap_df = pd.DataFrame(heatmap_data)
    
    # تطبيع القيم لكل تمرين
    normalized_df = heatmap_df.copy()
    
    for ex in exercises:
        ex_data = normalized_df[normalized_df['exercise'] == ex]
        
        if not ex_data.empty:
            max_value = ex_data['value'].max()
            
            if max_value > 0:
                normalized_df.loc[normalized_df['exercise'] == ex, 'normalized_value'] = normalized_df.loc[normalized_df['exercise'] == ex, 'value'] / max_value
            else:
                normalized_df.loc[normalized_df['exercise'] == ex, 'normalized_value'] = 0
    
    # إنشاء الخريطة الحرارية
    fig = px.density_heatmap(
        normalized_df,
        x='date',
        y='exercise',
        z='normalized_value',
        color_continuous_scale='Viridis',
        title='خريطة حرارية لتقدم التمارين'
    )
    
    fig.update_layout(
        xaxis_title="التاريخ",
        yaxis_title="التمرين",
        coloraxis_colorbar=dict(
            title="القيمة النسبية"
        ),
        template="plotly_white"
    )
    
    return json.dumps(fig.to_dict())

def create_weekly_summary_chart(workouts, exercises):
    """إنشاء رسم بياني للملخص الأسبوعي"""
    if workouts.empty:
        # إنشاء رسم بياني فارغ
        fig = go.Figure()
        fig.update_layout(
            title="لا توجد بيانات كافية لعرض الملخص الأسبوعي",
            template="plotly_white"
        )
        return json.dumps(fig.to_dict())
    
    # تحويل التاريخ إلى كائن datetime
    workouts['Date'] = pd.to_datetime(workouts['date'])
    
    # إضافة عمود للأسبوع
    workouts['Week'] = workouts['Date'].dt.strftime('%Y-%U')
    
    # حساب المتوسط الأسبوعي لكل تمرين
    weekly_data = []
    
    for ex in exercises:
        if ex in workouts.columns:
            ex_weekly = workouts.groupby('Week')[ex].mean().reset_index()
            
            if not ex_weekly.empty:
                for _, row in ex_weekly.iterrows():
                    weekly_data.append({
                        'week': row['Week'],
                        'exercise': ex,
                        'value': row[ex]
                    })
    
    if not weekly_data:
        # إنشاء رسم بياني فارغ
        fig = go.Figure()
        fig.update_layout(
            title="لا توجد بيانات كافية لعرض الملخص الأسبوعي",
            template="plotly_white"
        )
        return json.dumps(fig.to_dict())
    
    # تحويل البيانات إلى DataFrame
    weekly_df = pd.DataFrame(weekly_data)
    
    # إنشاء رسم بياني شريطي
    fig = px.bar(
        weekly_df,
        x='week',
        y='value',
        color='exercise',
        barmode='group',
        title='الملخص الأسبوعي للتمارين'
    )
    
    fig.update_layout(
        xaxis_title="الأسبوع",
        yaxis_title="متوسط القيمة",
        legend_title="التمرين",
        template="plotly_white"
    )
    
    return json.dumps(fig.to_dict())

def create_comparison_chart(trainee_data, exercise):
    """إنشاء رسم بياني لمقارنة المتدربين"""
    if not trainee_data:
        # إنشاء رسم بياني فارغ
        fig = go.Figure()
        fig.update_layout(
            title="لا توجد بيانات كافية للمقارنة",
            template="plotly_white"
        )
        return json.dumps(fig.to_dict())
    
    fig = go.Figure()
    
    # إضافة خط لكل متدرب
    for trainee_name, data in trainee_data.items():
        dates = [item['date'] for item in data]
        values = [item[exercise] for item in data]
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name=trainee_name
        ))
    
    # تخصيص تنسيق الرسم البياني
    fig.update_layout(
        title=f"مقارنة أداء المتدربين في تمرين {exercise}",
        xaxis_title="التاريخ",
        yaxis_title="القيمة",
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white"
    )
    
    return json.dumps(fig.to_dict())

def create_weight_tracking_chart(weight_data, exercise):
    """إنشاء رسم بياني لتتبع الأوزان"""
    if not weight_data:
        # إنشاء رسم بياني فارغ
        fig = go.Figure()
        fig.update_layout(
            title="لا توجد بيانات كافية لتتبع الأوزان",
            template="plotly_white"
        )
        return json.dumps(fig.to_dict())
    
    dates = [item['date'] for item in weight_data]
    values = [item[exercise] for item in weight_data]
    weights = [item[f"{exercise}_weight"] for item in weight_data]
    
    fig = go.Figure()
    
    # إضافة خط للقيم
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name='القيمة',
        line=dict(color='blue')
    ))
    
    # إضافة خط للأوزان
    fig.add_trace(go.Scatter(
        x=dates,
        y=weights,
        mode='lines+markers',
        name='الوزن (كجم)',
        line=dict(color='red'),
        yaxis='y2'
    ))
    
    # تخصيص تنسيق الرسم البياني
    fig.update_layout(
        title=f"تتبع الأوزان لتمرين {exercise}",
        xaxis_title="التاريخ",
        yaxis=dict(
            title="القيمة",
            titlefont=dict(color='blue'),
            tickfont=dict(color='blue')
        ),
        yaxis2=dict(
            title="الوزن (كجم)",
            titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            anchor="x",
            overlaying="y",
            side="right"
        ),
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white"
    )
    
    return json.dumps(fig.to_dict())

def create_resistance_tracking_chart(resistance_data, exercise):
    """إنشاء رسم بياني لتتبع المقاومة"""
    if not resistance_data:
        # إنشاء رسم بياني فارغ
        fig = go.Figure()
        fig.update_layout(
            title="لا توجد بيانات كافية لتتبع المقاومة",
            template="plotly_white"
        )
        return json.dumps(fig.to_dict())
    
    # تحويل مستويات المقاومة إلى قيم عددية
    resistance_values = {
        'light': 1,
        'medium': 2,
        'heavy': 3
    }
    
    dates = [item['date'] for item in resistance_data]
    values = [item[exercise] for item in resistance_data]
    resistance = [resistance_values.get(item[f"{exercise}_resistance"], 0) for item in resistance_data]
    
    fig = go.Figure()
    
    # إضافة خط للقيم
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name='القيمة',
        line=dict(color='blue')
    ))
    
    # إضافة خط للمقاومة
    fig.add_trace(go.Scatter(
        x=dates,
        y=resistance,
        mode='lines+markers',
        name='مستوى المقاومة',
        line=dict(color='green'),
        yaxis='y2'
    ))
    
    # تخصيص تنسيق الرسم البياني
    fig.update_layout(
        title=f"تتبع المقاومة لتمرين {exercise}",
        xaxis_title="التاريخ",
        yaxis=dict(
            title="القيمة",
            titlefont=dict(color='blue'),
            tickfont=dict(color='blue')
        ),
        yaxis2=dict(
            title="مستوى المقاومة",
            titlefont=dict(color='green'),
            tickfont=dict(color='green'),
            anchor="x",
            overlaying="y",
            side="right",
            range=[0, 4],
            tickvals=[1, 2, 3],
            ticktext=['خفيفة', 'متوسطة', 'ثقيلة']
        ),
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white"
    )
    
    return json.dumps(fig.to_dict())
