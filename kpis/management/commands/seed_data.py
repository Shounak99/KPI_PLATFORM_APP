from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from projects.models import Project
from kpis.models import KPI
import random

User = get_user_model()

PROJECTS = [
    "Website Redesign", "Mobile App Launch", "Q4 Sales Drive", "Customer Retention",
    "Infrastructure Upgrade", "Data Migration", "Brand Awareness Campaign", "Product Beta",
    "API Integration", "Security Audit", "Employee Onboarding", "CRM Implementation",
    "Supply Chain Optimization", "Market Expansion", "Cost Reduction Initiative",
    "User Research Program", "Analytics Dashboard", "Compliance Review", "Partner Portal",
    "DevOps Transformation",
]

KPI_TEMPLATES = [
    ("Revenue", "$"), ("Customer Satisfaction", "score"), ("Bug Count", "bugs"),
    ("Uptime", "%"), ("Response Time", "ms"), ("User Signups", "users"),
    ("Churn Rate", "%"), ("NPS Score", "score"), ("Page Load Time", "ms"),
    ("Test Coverage", "%"), ("Support Tickets", "tickets"), ("Conversion Rate", "%"),
    ("Active Users", "users"), ("Deployment Frequency", "deploys"), ("Error Rate", "%"),
]

STATUSES = ['on_track', 'at_risk', 'off_track']


class Command(BaseCommand):
    help = 'Seed database with dummy projects and KPIs'

    def handle(self, *args, **kwargs):
        # get or create a seed user
        user, _ = User.objects.get_or_create(
            username='seed_owner',
            defaults={'role': 'owner', 'email': 'seed@example.com'}
        )
        user.set_password('seed1234')
        user.save()

        created_projects = 0
        created_kpis = 0

        for name in PROJECTS:
            project, created = Project.objects.get_or_create(
                name=name,
                defaults={'description': f'Auto-generated project: {name}', 'owner': user}
            )
            if created:
                created_projects += 1

            # 3 KPIs per project = 60 KPIs total
            for kpi_name, unit in random.sample(KPI_TEMPLATES, 3):
                target = round(random.uniform(50, 1000), 2)
                actual = round(random.uniform(0, target * 1.1), 2)
                status = random.choice(STATUSES)

                KPI.objects.get_or_create(
                    name=kpi_name,
                    project=project,
                    defaults={
                        'unit': unit,
                        'target_value': target,
                        'actual_value': actual,
                        'status': status,
                        'description': f'Tracking {kpi_name} for {name}',
                    }
                )
                created_kpis += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {created_projects} projects and {created_kpis} KPIs. Login: seed_owner / seed1234'
        ))
