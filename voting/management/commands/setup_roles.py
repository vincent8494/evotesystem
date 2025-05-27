"""
Management command to set up initial roles and permissions.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps


class Command(BaseCommand):
    help = 'Sets up initial user groups and permissions for the voting system'

    def handle(self, *args, **options):
        # Get or create groups
        manager_group, created = Group.objects.get_or_create(name='Election Managers')
        voter_group, created = Group.objects.get_or_create(name='Voters')
        
        # Get permissions
        election_permissions = [
            'add_election',
            'change_election',
            'delete_election',
            'view_election',
            'can_manage_elections',
            'can_verify_election',
            'can_view_results',
            'can_export_results',
        ]
        
        # Get the content type for the Election model
        election_content_type = ContentType.objects.get_for_model(
            apps.get_model('voting', 'Election')
        )
        
        # Add permissions to manager group
        for codename in election_permissions:
            try:
                perm = Permission.objects.get(
                    content_type=election_content_type,
                    codename=codename
                )
                manager_group.permissions.add(perm)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'Permission {codename} does not exist. Skipping...'
                ))
        
        # Voter group gets basic view permissions
        try:
            view_perm = Permission.objects.get(
                content_type=election_content_type,
                codename='view_election'
            )
            voter_group.permissions.add(view_perm)
        except Permission.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Failed to assign view_election permission to Voters group.'
            ))
        
        self.stdout.write(self.style.SUCCESS(
            'Successfully set up user groups and permissions.'
        ))
        self.stdout.write(f'- Election Managers: {manager_group.permissions.count()} permissions')
        self.stdout.write(f'- Voters: {voter_group.permissions.count()} permissions')
