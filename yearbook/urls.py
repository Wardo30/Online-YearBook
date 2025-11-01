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
    path('search/', views.search_all, name='search_all'),
    
    # Album URLs
    path('albums/', views.album_list, name='album_list'),
    path('albums/<int:album_id>/', views.album_detail, name='album_detail'),
    path('photos/<int:photo_id>/', views.photo_detail, name='photo_detail'),
    
    # Custom Admin-like URLs (avoid clashing with Django's /admin/)
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('panel/students/', views.admin_student_list, name='admin_student_list'),
    path('panel/students/add/', views.admin_student_add, name='admin_student_add'),
    path('panel/students/<int:student_id>/edit/', views.admin_student_edit, name='admin_student_edit'),
    path('panel/students/<int:student_id>/delete/', views.admin_student_delete, name='admin_student_delete'),
    path('panel/students/<int:student_id>/', views.admin_student_detail, name='admin_student_detail'),
    path('panel/bulk-operations/', views.admin_bulk_operations, name='admin_bulk_operations'),
    
    # Admin Album Management URLs
    path('panel/albums/', views.admin_album_list, name='admin_album_list'),
    path('panel/albums/add/', views.admin_album_add, name='admin_album_add'),
    path('panel/albums/<int:album_id>/edit/', views.admin_album_edit, name='admin_album_edit'),
    path('panel/albums/<int:album_id>/delete/', views.admin_album_delete, name='admin_album_delete'),
    path('panel/albums/<int:album_id>/photos/', views.admin_photo_list, name='admin_photo_list'),
    path('panel/albums/<int:album_id>/photos/add/', views.admin_photo_add, name='admin_photo_add'),
    path('panel/photos/<int:photo_id>/delete/', views.admin_photo_delete, name='admin_photo_delete'),
    
    path('logout/', views.logout_view, name='logout'),
]
