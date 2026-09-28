"""
Management command: send_weekly_digest
Usage: python manage.py send_weekly_digest

Sends each user a personalised weekly email listing new posts
from the authors they follow, published in the last 7 days.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

from accounts.models import Follow
from blog.models import Post


class Command(BaseCommand):
    help = "Send weekly digest emails to users listing new posts from their followed authors."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print digest content to stdout instead of sending emails.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        since = timezone.now() - timedelta(days=7)

        # Get all distinct followers who follow at least one author
        follower_ids = Follow.objects.values_list('follower_id', flat=True).distinct()

        sent = 0
        skipped = 0

        for follower_id in follower_ids:
            follows = Follow.objects.filter(follower_id=follower_id).select_related('follower', 'following')
            if not follows.exists():
                continue

            follower = follows.first().follower
            following_ids = follows.values_list('following_id', flat=True)

            # New posts from followed authors in the last 7 days
            new_posts = Post.objects.filter(
                author_id__in=following_ids,
                status=Post.STATUS_PUBLISHED,
                published_at__gte=since,
            ).select_related('author').order_by('-published_at')

            if not new_posts.exists():
                skipped += 1
                continue

            # Build email body
            lines = [
                f"Hi {follower.get_full_name() or follower.username},",
                "",
                "Here are the latest stories from authors you follow on Chronicle:",
                "",
            ]
            for post in new_posts:
                lines.append(f"  ▶  {post.title}")
                lines.append(f"     by {post.author.get_full_name() or post.author.username}")
                lines.append(f"     {post.excerpt[:120] if post.excerpt else ''}...")
                lines.append(f"     Read: http://127.0.0.1:8000{post.get_absolute_url()}")
                lines.append("")

            lines += [
                "Happy reading!",
                "— The Chronicle Team",
                "",
                "To manage your email preferences, visit your profile settings.",
            ]

            body = "\n".join(lines)
            subject = f"Your Chronicle Weekly Digest — {timezone.now().strftime('%b %d, %Y')}"

            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
                self.stdout.write(f"TO: {follower.email}")
                self.stdout.write(f"SUBJECT: {subject}")
                self.stdout.write(body)
            else:
                if follower.email:
                    send_mail(
                        subject=subject,
                        message=body,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'chronicle@example.com'),
                        recipient_list=[follower.email],
                        fail_silently=True,
                    )
                    sent += 1
                else:
                    skipped += 1

        if dry_run:
            self.stdout.write(self.style.SUCCESS("\n[Dry run complete — no emails were sent]"))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Weekly digest sent to {sent} users. {skipped} skipped (no email / no new posts).")
            )
