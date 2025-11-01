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
from .models import Student, Album, Photo, SearchHistory
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
                print(f"Profile photo uploaded: {request.FILES['profile_photo']}")
                student_profile.profile_photo = request.FILES['profile_photo']
                print(f"Profile photo saved to: {student_profile.profile_photo}")
            else:
                print("No profile photo in request.FILES")
            
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

# Unified search across albums and students
@login_required
def search_all(request):
    """Search albums and students by a single query string.
    Matches partial, case-insensitive values across multiple fields.
    """
    query = (request.GET.get('q') or request.GET.get('search') or '').strip()
    albums = Album.objects.none()
    students = Student.objects.none()

    if query:
        albums = Album.objects.filter(is_active=True).filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(department__icontains=query) |
            models.Q(year__icontains=query)
        ).order_by('-created_at')

        students = Student.objects.filter(
            models.Q(first_name__icontains=query) |
            models.Q(middle_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(school_id__icontains=query) |
            models.Q(email__icontains=query) |
            models.Q(department__icontains=query) |
            models.Q(block__icontains=query) |
            models.Q(section__icontains=query)
        ).order_by('first_name', 'last_name')

    context = {
        'q': query,
        'albums': albums,
        'students': students,
    }
    return render(request, 'yearbook/search_results.html', context)

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
    total_albums = Album.objects.count()
    total_photos = Photo.objects.count()
    recent_searches = SearchHistory.objects.count()
    
    # Get recent students
    recent_students = Student.objects.order_by('-created_at')[:5]
    
    # Get recent albums
    recent_albums = Album.objects.order_by('-created_at')[:5]
    
    context = {
        'total_students': total_students,
        'total_users': total_users,
        'total_albums': total_albums,
        'total_photos': total_photos,
        'recent_searches': recent_searches,
        'recent_students': recent_students,
        'recent_albums': recent_albums,
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

# Album Views
@login_required
def album_list(request):
    """Display all available albums with optional search"""
    search_query = request.GET.get('search', '').strip()
    albums = Album.objects.filter(is_active=True)
    
    if search_query:
        albums = albums.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(department__icontains=search_query) |
            models.Q(year__icontains=search_query)
        )
    
    albums = albums.order_by('-created_at')
    
    context = {
        'albums': albums,
        'search': search_query,
    }
    return render(request, 'yearbook/album_list.html', context)

@login_required
def album_detail(request, album_id):
    """Display photos in a specific album"""
    album = get_object_or_404(Album, id=album_id, is_active=True)
    photos = album.photos.all().order_by('-is_featured', '-created_at')
    
    # Paginate photos
    paginator = Paginator(photos, 12)  # Show 12 photos per page
    page_number = request.GET.get('page')
    photos = paginator.get_page(page_number)
    
    context = {
        'album': album,
        'photos': photos,
    }
    return render(request, 'yearbook/album_detail.html', context)

@login_required
def photo_detail(request, photo_id):
    """Display individual photo with details"""
    photo = get_object_or_404(Photo, id=photo_id)
    
    context = {
        'photo': photo,
    }
    return render(request, 'yearbook/photo_detail.html', context)

# Admin Album Management Views
@login_required
@user_passes_test(is_admin)
def admin_album_list(request):
    """Admin view to manage all albums"""
    albums = Album.objects.all().order_by('-created_at')
    
    context = {
        'albums': albums,
    }
    return render(request, 'yearbook/admin_album_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_album_add(request):
    """Admin view to add new album"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        department = request.POST.get('department')
        year = request.POST.get('year')
        cover_photo = request.FILES.get('cover_photo')
        
        if title and department and year:
            album = Album.objects.create(
                title=title,
                description=description,
                department=department,
                year=year,
                cover_photo=cover_photo
            )
            messages.success(request, f'Album "{album.title}" created successfully!')
            return redirect('admin_album_list')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {
        'title': 'Add New Album',
        'departments': Student.DEPARTMENTS,
        'years': Student.YEARS,
    }
    return render(request, 'yearbook/admin_album_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_album_edit(request, album_id):
    """Admin view to edit existing album"""
    album = get_object_or_404(Album, id=album_id)
    
    if request.method == 'POST':
        album.title = request.POST.get('title')
        album.description = request.POST.get('description')
        album.department = request.POST.get('department')
        album.year = request.POST.get('year')
        album.is_active = request.POST.get('is_active') == 'on'
        
        if request.FILES.get('cover_photo'):
            album.cover_photo = request.FILES.get('cover_photo')
        
        album.save()
        messages.success(request, f'Album "{album.title}" updated successfully!')
        return redirect('admin_album_list')
    
    context = {
        'title': 'Edit Album',
        'album': album,
        'departments': Student.DEPARTMENTS,
        'years': Student.YEARS,
    }
    return render(request, 'yearbook/admin_album_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_album_delete(request, album_id):
    """Admin view to delete album"""
    album = get_object_or_404(Album, id=album_id)
    
    if request.method == 'POST':
        album_title = album.title
        album.delete()
        messages.success(request, f'Album "{album_title}" deleted successfully!')
        return redirect('admin_album_list')
    
    context = {
        'album': album,
    }
    return render(request, 'yearbook/admin_album_delete.html', context)

@login_required
@user_passes_test(is_admin)
def admin_photo_list(request, album_id):
    """Admin view to manage photos in an album"""
    album = get_object_or_404(Album, id=album_id)
    photos = album.photos.all().order_by('-is_featured', '-created_at')
    
    context = {
        'album': album,
        'photos': photos,
    }
    return render(request, 'yearbook/admin_photo_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_photo_add(request, album_id):
    """Admin view to add photos to an album"""
    album = get_object_or_404(Album, id=album_id)
    
    if request.method == 'POST':
        images = request.FILES.getlist('images')
        student_id = request.POST.get('student')
        caption = request.POST.get('caption')
        is_featured = request.POST.get('is_featured') == 'on'
        
        if images:
            student = None
            if student_id:
                try:
                    student = Student.objects.get(id=student_id)
                except Student.DoesNotExist:
                    pass
            
            for image in images:
                Photo.objects.create(
                    album=album,
                    student=student,
                    image=image,
                    caption=caption,
                    is_featured=is_featured,
                    uploaded_by=request.user
                )
            
            messages.success(request, f'{len(images)} photo(s) added to "{album.title}" successfully!')
            return redirect('admin_photo_list', album_id=album.id)
        else:
            messages.error(request, 'Please select at least one image.')
    
    # Get students for dropdown
    students = Student.objects.all().order_by('first_name', 'last_name')
    
    context = {
        'title': f'Add Photos to {album.title}',
        'album': album,
        'students': students,
    }
    return render(request, 'yearbook/admin_photo_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_photo_delete(request, photo_id):
    """Admin view to delete photo"""
    photo = get_object_or_404(Photo, id=photo_id)
    album = photo.album
    
    if request.method == 'POST':
        photo.delete()
        messages.success(request, 'Photo deleted successfully!')
        return redirect('admin_photo_list', album_id=album.id)
    
    context = {
        'photo': photo,
    }
    return render(request, 'yearbook/admin_photo_delete.html', context)
