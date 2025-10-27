from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('about/', views.about, name='about'),
    path('profile/', views.profile, name='profile'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('search-students/', views.search_students, name='search_students'),
    
    # Custom Admin-like URLs (avoid clashing with Django's /admin/)
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('panel/students/', views.admin_student_list, name='admin_student_list'),
    path('panel/students/add/', views.admin_student_add, name='admin_student_add'),
    path('panel/students/<int:student_id>/edit/', views.admin_student_edit, name='admin_student_edit'),
    path('panel/students/<int:student_id>/delete/', views.admin_student_delete, name='admin_student_delete'),
    path('panel/students/<int:student_id>/', views.admin_student_detail, name='admin_student_detail'),
    path('panel/bulk-operations/', views.admin_bulk_operations, name='admin_bulk_operations'),
    
    path('logout/', views.logout_view, name='logout'),
]
