from django.db import models
from django.utils import timezone


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.CharField(max_length=200)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def kpi_summary(self):
        kpis = self.kpis.all()
        total = kpis.count()

        if total == 0:
            return {
                'total': 0,
                'on_track': 0,
                'at_risk': 0,
                'off_track': 0,
                'overall_status': 'no_kpis',
            }

        on_track = kpis.filter(status='on_track').count()
        at_risk = kpis.filter(status='at_risk').count()
        off_track = kpis.filter(status='off_track').count()

        if off_track > 0:
            overall = 'off_track'
        elif at_risk > 0:
            overall = 'at_risk'
        else:
            overall = 'on_track'

        return {
            'total': total,
            'on_track': on_track,
            'at_risk': at_risk,
            'off_track': off_track,
            'overall_status': overall,
        }
