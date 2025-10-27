from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import models
from django.urls import reverse
from .models import Student, SearchHistory
from .forms import SignUpForm, StudentForm, StudentSearchForm

def landing(request):
    return render(request, 'yearbook/landing.html')


def about(request):
    return render(request, 'yearbook/about.html')


@login_required
def profile(request):
    # Get current user's student profile
    try:
        student_profile = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        student_profile = None
    
    # Handle profile updates
    if request.method == 'POST':
        # Update user information
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        # Update or create student profile
        if student_profile:
            student_profile.middle_name = request.POST.get('middle_name', student_profile.middle_name)
            student_profile.school_id = request.POST.get('school_id', student_profile.school_id)
            student_profile.department = request.POST.get('department', student_profile.department)
            student_profile.year = request.POST.get('year', student_profile.year)
            student_profile.block = request.POST.get('block', student_profile.block)
            student_profile.section = request.POST.get('section', student_profile.section)
            student_profile.achievements = request.POST.get('achievements', student_profile.achievements)
            
            # Handle profile photo upload
            if 'profile_photo' in request.FILES:
                student_profile.profile_photo = request.FILES['profile_photo']
            
            student_profile.save()
        else:
            # Create new student profile
            student_profile = Student.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                middle_name=request.POST.get('middle_name', ''),
                school_id=request.POST.get('school_id', ''),
                email=user.email,
                department=request.POST.get('department', 'BSIT'),
                year=request.POST.get('year', '2025'),
                block=request.POST.get('block', 'A'),
                section=request.POST.get('section', '1'),
                achievements=request.POST.get('achievements', ''),
                profile_photo=request.FILES.get('profile_photo')
            )
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    context = {
        'student_profile': student_profile,
        'departments': Student.DEPARTMENTS,
        'years': Student.YEARS,
    }
    
    return render(request, 'yearbook/profile.html', context)


def signup_view(request):
    # Custom handler to match the visual design fields on the template
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        school_id = request.POST.get('school_id', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()
        # Optional field present in the UI, not stored explicitly
        _school_role = request.POST.get('school_role', '').strip()

        # Basic validations
        errors = []
        if not first_name or not last_name:
            errors.append('First name and last name are required.')
        if not school_id:
            errors.append('School ID is required.')
        if not email:
            errors.append('Email is required.')
        if not password1 or not password2:
            errors.append('Both password fields are required.')
        if password1 != password2:
            errors.append('Passwords do not match.')

        # Uniqueness checks
        from django.contrib.auth.models import User
        if User.objects.filter(username=school_id).exists():
            errors.append('An account with this School ID already exists.')
        if User.objects.filter(email=email).exists():
            errors.append('An account with this email already exists.')
        if Student.objects.filter(school_id=school_id).exists():
            errors.append('A student with this School ID already exists.')

        if errors:
            for e in errors:
                messages.error(request, e)
            # Keep the page with entered values (template reads POST values)
            return render(request, 'yearbook/signup.html')

        # Create the User
        user = User.objects.create_user(
            username=school_id,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )

        # Create a linked Student profile with sensible defaults
        Student.objects.create(
            user=user,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            school_id=school_id,
            email=email,
            department='BSIT',  # default; can be edited later
            year='2025',        # default; can be edited later
            block='A',          # default; can be edited later
            section='1',        # default; can be edited later
        )

        login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect('student_dashboard')

    return render(request, 'yearbook/signup.html')


def login_view(request):
    if request.user.is_authenticated:
        # Send staff/admin users to the admin dashboard, others to student dashboard
        return redirect('admin_dashboard' if request.user.is_staff else 'student_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect admins to admin dashboard, regular users to student dashboard
                return redirect('admin_dashboard' if user.is_staff else 'student_dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'yearbook/login.html', {'form': form})


@login_required
def student_dashboard(request):
    # Get search parameters
    search_query = request.GET.get('search', '')
    department = request.GET.get('department', '')
    year = request.GET.get('year', '')
    block = request.GET.get('block', '')
    section = request.GET.get('section', '')
    
    # Get current user's student profile
    try:
        student_profile = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        student_profile = None
    
    # Get recent searches for current user
    recent_searches = SearchHistory.objects.filter(user=request.user)[:5]
    
    # Search students
    students = Student.objects.all()
    
    if search_query:
        students = students.filter(
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query) |
            models.Q(school_id__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )
        # Save search to history
        SearchHistory.objects.create(
            user=request.user,
            search_query=search_query,
            search_type='student'
        )
    
    if department:
        students = students.filter(department=department)
    if year:
        students = students.filter(year=year)
    if block:
        students = students.filter(block=block)
    if section:
        students = students.filter(section=section)
    
    # Paginate results
    paginator = Paginator(students, 12)
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)
    
    context = {
        'student_profile': student_profile,
        'students': students,
        'recent_searches': recent_searches,
        'search_query': search_query,
        'department': department,
        'year': year,
        'block': block,
        'section': section,
        'departments': Student.DEPARTMENTS,
        'years': Student.YEARS,
    }
    
    return render(request, 'yearbook/student_dashboard.html', context)

@login_required
def search_students(request):
    if request.method == 'GET':
        query = request.GET.get('q', '')
        students = Student.objects.filter(
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(school_id__icontains=query)
        )[:10]
        
        results = []
        for student in students:
            results.append({
                'id': student.id,
                'name': student.full_name,
                'school_id': student.school_id,
                'department': student.department,
                'year': student.year,
                'section': student.section,
            })
        
        return JsonResponse({'results': results})

@login_required
def dashboard(request):
    query = request.GET.get('q', '')
    students = Student.objects.all()
    if query:
        students = students.filter(
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(school_id__icontains=query) |
            models.Q(email__icontains=query)
        )
    return render(request, 'yearbook/dashboard.html', {'students': students})


def logout_view(request):
    logout(request)
    return redirect('login')

# Admin permission check
def is_admin(user):
    return user.is_authenticated and user.is_staff

# Admin Dashboard Views
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get statistics
    total_students = Student.objects.count()
    total_users = User.objects.count()
    recent_searches = SearchHistory.objects.count()
    
    # Get recent students
    recent_students = Student.objects.order_by('-created_at')[:5]
    
    context = {
        'total_students': total_students,
        'total_users': total_users,
        'recent_searches': recent_searches,
        'recent_students': recent_students,
    }
    return render(request, 'yearbook/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_student_list(request):
    search_form = StudentSearchForm(request.GET)
    students = Student.objects.all()
    
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        department = search_form.cleaned_data.get('department')
        year = search_form.cleaned_data.get('year')
        block = search_form.cleaned_data.get('block')
        section = search_form.cleaned_data.get('section')
        
        if search:
            students = students.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(school_id__icontains=search) |
                models.Q(email__icontains=search)
            )
        
        if department:
            students = students.filter(department=department)
        if year:
            students = students.filter(year=year)
        if block:
            students = students.filter(block=block)
        if section:
            students = students.filter(section=section)
    
    # Pagination
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)
    
    context = {
        'students': students,
        'search_form': search_form,
    }
    return render(request, 'yearbook/admin_student_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_student_add(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student added successfully!')
            return redirect('admin_student_list')
    else:
        form = StudentForm()
    
    context = {'form': form, 'title': 'Add New Student'}
    return render(request, 'yearbook/admin_student_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_student_edit(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('admin_student_list')
    else:
        form = StudentForm(instance=student)
    
    context = {'form': form, 'title': f'Edit Student: {student.full_name}', 'student': student}
    return render(request, 'yearbook/admin_student_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_student_delete(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        student_name = student.full_name
        student.delete()
        messages.success(request, f'Student {student_name} deleted successfully!')
        return redirect('admin_student_list')
    
    context = {'student': student}
    return render(request, 'yearbook/admin_student_delete.html', context)

@login_required
@user_passes_test(is_admin)
def admin_student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    context = {'student': student}
    return render(request, 'yearbook/admin_student_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_bulk_operations(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        student_ids = request.POST.getlist('selected_students')
        
        if action and student_ids:
            students = Student.objects.filter(id__in=student_ids)
            
            if action == 'delete':
                count = students.count()
                students.delete()
                messages.success(request, f'{count} students deleted successfully!')
            elif action == 'honor_roll':
                count = 0
                for student in students:
                    student.achievements = "Honor Roll Student - " + (student.achievements or "")
                    student.save()
                    count += 1
                messages.success(request, f'{count} students marked as Honor Roll!')
            elif action == 'export':
                # Here you could implement CSV export
                messages.info(request, 'Export functionality would be implemented here.')
        
        return redirect('admin_student_list')
    
    return redirect('admin_student_list')
