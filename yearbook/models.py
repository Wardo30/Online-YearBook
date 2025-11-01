from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Student(models.Model):
    DEPARTMENTS = [
        ('BSHM', 'BSHM'),
        ('STEM', 'STEM'),
        ('ABM', 'ABM'),
        ('BSIT', 'BSIT'),
        ('BSED', 'BSED'),
    ]
    
    YEARS = [
        ('2021', '2021'),
        ('2022', '2022'),
        ('2023', '2023'),
        ('2024', '2024'),
        ('2025', '2025'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    school_id = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    department = models.CharField(max_length=10, choices=DEPARTMENTS)
    year = models.CharField(max_length=4, choices=YEARS)
    block = models.CharField(max_length=10)
    section = models.CharField(max_length=50)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    achievements = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def full_name(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.full_name} ({self.department}-{self.year})"

class Album(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.CharField(max_length=10, choices=Student.DEPARTMENTS)
    year = models.CharField(max_length=4, choices=Student.YEARS)
    cover_photo = models.ImageField(upload_to='albums/covers/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['department', 'year']

    def __str__(self):
        return f"{self.title} ({self.department}-{self.year})"

    @property
    def photo_count(self):
        return self.photos.count()

class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='photos')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='albums/photos/')
    caption = models.CharField(max_length=300, blank=True)
    is_featured = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        if self.student:
            return f"{self.student.full_name} - {self.album.title}"
        return f"Photo - {self.album.title}"

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_query = models.CharField(max_length=255)
    search_type = models.CharField(max_length=50, default='student')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Search Histories'
