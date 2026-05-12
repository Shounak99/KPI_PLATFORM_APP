from django.db import models
from django.core.validators import MinValueValidator
from projects.models import Project


class KPI(models.Model):
    STATUS_CHOICES = [
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('off_track', 'Off Track'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='kpis'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=50, blank=True)
    target_value = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    actual_value = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='on_track')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.project.name})'

    @property
    def progress_percent(self):
        if self.target_value == 0:
            return 0
        return min(round((self.actual_value / self.target_value) * 100, 1), 100)

    @property
    def suggested_status(self):
        if self.target_value == 0:
            return 'on_track'
        ratio = float(self.actual_value) / float(self.target_value)
        if ratio >= 0.9:
            return 'on_track'
        elif ratio >= 0.7:
            return 'at_risk'
        return 'off_track'
