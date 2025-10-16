from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Student, SearchHistory

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'school_id', 'department', 'year', 'block', 'section', 'email')
    list_filter = ('department', 'year', 'block', 'section')
    search_fields = ('first_name', 'last_name', 'school_id', 'email')
    list_per_page = 20
    ordering = ('last_name', 'first_name')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'first_name', 'middle_name', 'last_name', 'school_id', 'email', 'profile_photo')
        }),
        ('Academic Information', {
            'fields': ('department', 'year', 'block', 'section')
        }),
        ('Achievements', {
            'fields': ('achievements',),
            'classes': ('collapse',)
        }),
    )
    
    def make_honor_roll(self, request, queryset):
        for student in queryset:
            student.achievements = "Honor Roll Student - " + (student.achievements or "")
            student.save()
    make_honor_roll.short_description = "Mark selected students as Honor Roll"
    
    actions = ['make_honor_roll']

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'search_query', 'search_type', 'created_at')
    list_filter = ('search_type', 'created_at')
    search_fields = ('user__username', 'search_query')
    list_per_page = 20
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
