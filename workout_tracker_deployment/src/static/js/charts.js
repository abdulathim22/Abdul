// تهيئة الرسوم البيانية التفاعلية
document.addEventListener('DOMContentLoaded', function() {
    // تهيئة القوائم المنسدلة
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (toggle && menu) {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                menu.classList.toggle('show');
            });
            
            // إغلاق القائمة عند النقر خارجها
            document.addEventListener('click', function(e) {
                if (!dropdown.contains(e.target)) {
                    menu.classList.remove('show');
                }
            });
        }
    });
    
    // تهيئة الرسوم البيانية إذا كانت موجودة
    if (typeof Plotly !== 'undefined') {
        // تعديل الرسوم البيانية لدعم اللغة العربية
        const lang = document.documentElement.lang;
        const isRTL = document.dir === 'rtl';
        
        if (isRTL) {
            // تعديل إعدادات Plotly للغة العربية
            Plotly.setPlotConfig({
                locale: 'ar',
                locales: {
                    'ar': {
                        dictionary: {
                            'Click to enter Colorscale title': 'انقر لإدخال عنوان مقياس الألوان',
                            'Zoom': 'تكبير',
                            'Pan': 'تحريك',
                            'Box Select': 'تحديد مربع',
                            'Lasso Select': 'تحديد حر',
                            'Reset': 'إعادة تعيين',
                            'Download plot as a png': 'تنزيل الرسم البياني كصورة png',
                            'Zoom in': 'تكبير',
                            'Zoom out': 'تصغير',
                            'Autoscale': 'مقياس تلقائي'
                        },
                        format: {
                            days: ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'],
                            shortDays: ['أحد', 'إثن', 'ثلا', 'أرب', 'خمي', 'جمع', 'سبت'],
                            months: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'],
                            shortMonths: ['ينا', 'فبر', 'مار', 'أبر', 'ماي', 'يون', 'يول', 'أغس', 'سبت', 'أكت', 'نوف', 'ديس'],
                            date: '%d/%m/%Y'
                        }
                    }
                }
            });
        }
        
        // تهيئة الرسم البياني للتقدم إذا كان موجوداً
        const progressChart = document.getElementById('progress-chart');
        if (progressChart && typeof chartData !== 'undefined') {
            try {
                const chartObj = JSON.parse(chartData);
                
                // تعديل الإعدادات حسب اللغة
                if (isRTL) {
                    if (chartObj.layout) {
                        chartObj.layout.font = chartObj.layout.font || {};
                        chartObj.layout.font.family = 'Arial, sans-serif';
                        
                        // تعديل عناوين المحاور
                        if (chartObj.layout.xaxis) {
                            chartObj.layout.xaxis.title = lang === 'ar' ? 'التاريخ' : 'Date';
                            chartObj.layout.xaxis.autorange = 'reversed';
                        }
                        
                        if (chartObj.layout.yaxis) {
                            chartObj.layout.yaxis.title = lang === 'ar' ? 'القيمة' : 'Value';
                        }
                        
                        // تعديل العنوان
                        chartObj.layout.title = lang === 'ar' ? 'تطور أداء التمارين' : 'Exercise Progress';
                    }
                }
                
                Plotly.newPlot('progress-chart', chartObj.data, chartObj.layout);
            } catch (e) {
                console.error('Error initializing progress chart:', e);
            }
        }
        
        // تهيئة رسم المقارنة إذا كان موجوداً
        const comparisonChart = document.getElementById('comparison-chart');
        if (comparisonChart) {
            // سيتم تحديثه عند تغيير التمرين
            const exerciseSelect = document.getElementById('exercise-select');
            if (exerciseSelect) {
                updateComparisonChart();
            }
        }
    }
    
    // تهيئة مربع البحث في سجل التمارين
    const workoutSearch = document.getElementById('workout-search');
    if (workoutSearch) {
        workoutSearch.addEventListener('keyup', searchWorkouts);
    }
    
    // تهيئة النافذة المنبثقة
    const modal = document.getElementById('editModal');
    if (modal) {
        const closeBtn = modal.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                modal.style.display = 'none';
            });
        }
        
        // إغلاق النافذة المنبثقة عند النقر خارجها
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
});

// دالة تحديث نوع الرسم البياني
function updateChartType() {
    const chartType = document.getElementById('chart-type').value;
    const timeRange = document.getElementById('time-range').value;
    const traineeId = getTraineeIdFromUrl();
    
    let url = traineeId 
        ? `/coach/update_trainee_chart/${traineeId}?type=${chartType}&range=${timeRange}`
        : `/trainee/update_chart?type=${chartType}&range=${timeRange}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const chartObj = JSON.parse(data.chart_data);
            Plotly.react('progress-chart', chartObj.data, chartObj.layout);
        })
        .catch(error => console.error('Error updating chart type:', error));
}

// دالة تحديث الفترة الزمنية
function updateTimeRange() {
    const chartType = document.getElementById('chart-type').value;
    const timeRange = document.getElementById('time-range').value;
    const traineeId = getTraineeIdFromUrl();
    
    let url = traineeId 
        ? `/coach/update_trainee_chart/${traineeId}?type=${chartType}&range=${timeRange}`
        : `/trainee/update_chart?type=${chartType}&range=${timeRange}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const chartObj = JSON.parse(data.chart_data);
            Plotly.react('progress-chart', chartObj.data, chartObj.layout);
        })
        .catch(error => console.error('Error updating time range:', error));
}

// دالة تحديث رسم المقارنة
function updateComparisonChart() {
    const exercise = document.getElementById('exercise-select').value;
    
    fetch(`/coach/get_comparison_data?exercise=${exercise}`)
        .then(response => response.json())
        .then(data => {
            const chartObj = JSON.parse(data.chart_data);
            Plotly.newPlot('comparison-chart', chartObj.data, chartObj.layout);
        })
        .catch(error => console.error('Error updating comparison chart:', error));
}

// دالة البحث في سجل التمارين
function searchWorkouts() {
    const input = document.getElementById('workout-search');
    const filter = input.value.toUpperCase();
    const table = document.getElementById('workout-table');
    const tr = table.getElementsByTagName('tr');
    
    for (let i = 1; i < tr.length; i++) {
        let found = false;
        const td = tr[i].getElementsByTagName('td');
        
        for (let j = 0; j < td.length; j++) {
            if (td[j]) {
                const txtValue = td[j].textContent || td[j].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
        }
        
        tr[i].style.display = found ? '' : 'none';
    }
}

// دالة لفتح نافذة تعديل التمرين
function editWorkout(index) {
    const modal = document.getElementById('editModal');
    const workouts = window.workouts || [];
    
    if (modal && workouts.length > index) {
        const workout = workouts[index];
        
        // تعيين عنوان النموذج
        const editForm = document.getElementById('editForm');
        if (editForm) {
            editForm.action = `/trainee/update/${workout.id}`;
            
            // تعبئة البيانات
            document.getElementById('edit_date').value = workout.date;
            
            // تعبئة بيانات التمارين
            const exerciseInputs = document.querySelectorAll('[id^="edit_"]');
            exerciseInputs.forEach(input => {
                const fieldName = input.id.replace('edit_', '');
                
                if (workout[fieldName] !== undefined && workout[fieldName] !== null) {
                    input.value = workout[fieldName];
                } else {
                    input.value = '';
                }
            });
            
            // عرض النافذة المنبثقة
            modal.style.display = 'block';
        }
    }
}

// دالة للحصول على معرف المتدرب من الرابط
function getTraineeIdFromUrl() {
    const path = window.location.pathname;
    const matches = path.match(/\/trainee\/(\d+)/);
    return matches ? matches[1] : null;
}

// دالة لتبديل عرض تفاصيل التمرين
function toggleExerciseDetails(exerciseId) {
    const details = document.getElementById(`details_${exerciseId}`);
    if (details) {
        details.classList.toggle('show');
    }
}

// دالة لتعليم جميع الإشعارات كمقروءة
function markAllNotificationsRead() {
    fetch('/trainee/mark_all_notifications_read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // إخفاء جميع الإشعارات
            const notifications = document.querySelectorAll('.notification-item');
            notifications.forEach(notification => {
                notification.style.display = 'none';
            });
            
            // عرض رسالة نجاح
            const notificationList = document.querySelector('.notification-list');
            if (notificationList) {
                notificationList.innerHTML = '<p class="empty-notification">لا توجد إشعارات جديدة</p>';
            }
        }
    })
    .catch(error => console.error('Error marking notifications as read:', error));
}

// دالة لمشاركة التمرين
function shareWorkout(workoutId) {
    fetch(`/trainee/share/${workoutId}`)
        .then(response => response.json())
        .then(data => {
            if (data.share_url) {
                // إنشاء مربع حوار للمشاركة
                const shareModal = document.createElement('div');
                shareModal.className = 'modal';
                shareModal.style.display = 'block';
                
                shareModal.innerHTML = `
                    <div class="modal-content">
                        <div class="modal-header">
                            <h2>مشاركة التمرين</h2>
                            <span class="close">&times;</span>
                        </div>
                        <div class="modal-body">
                            <p>يمكنك مشاركة هذا الرابط مع الآخرين:</p>
                            <div class="share-url">
                                <input type="text" value="${data.share_url}" readonly>
                                <button class="btn btn-primary copy-btn">نسخ</button>
                            </div>
                            <div class="social-share">
                                <a href="https://wa.me/?text=${encodeURIComponent(data.share_url)}" target="_blank" class="btn btn-whatsapp">
                                    <i class="fab fa-whatsapp"></i> واتساب
                                </a>
                                <a href="https://t.me/share/url?url=${encodeURIComponent(data.share_url)}" target="_blank" class="btn btn-telegram">
                                    <i class="fab fa-telegram"></i> تلجرام
                                </a>
                                <a href="https://twitter.com/intent/tweet?text=${encodeURIComponent(data.share_url)}" target="_blank" class="btn btn-twitter">
                                    <i class="fab fa-twitter"></i> تويتر
                                </a>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(shareModal);
                
                // إضافة وظيفة النسخ
                const copyBtn = shareModal.querySelector('.copy-btn');
                const urlInput = shareModal.querySelector('input');
                
                copyBtn.addEventListener('click', function() {
                    urlInput.select();
                    document.execCommand('copy');
                    copyBtn.textContent = 'تم النسخ!';
                    setTimeout(() => {
                        copyBtn.textContent = 'نسخ';
                    }, 2000);
                });
                
                // إضافة وظيفة الإغلاق
                const closeBtn = shareModal.querySelector('.close');
                closeBtn.addEventListener('click', function() {
                    shareModal.style.display = 'none';
                    setTimeout(() => {
                        shareModal.remove();
                    }, 300);
                });
                
                // إغلاق النافذة عند النقر خارجها
                window.addEventListener('click', function(event) {
                    if (event.target === shareModal) {
                        shareModal.style.display = 'none';
                        setTimeout(() => {
                            shareModal.remove();
                        }, 300);
                    }
                });
            }
        })
        .catch(error => console.error('Error sharing workout:', error));
}
