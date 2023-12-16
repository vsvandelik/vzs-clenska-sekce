from datetime import timedelta

from django.core.management import BaseCommand
from django.db.models import F
from django.utils.translation import gettext_lazy as _

from features.models import Feature, FeatureAssignment
from vzs import settings
from vzs.settings import CURRENT_DATETIME
from vzs.utils import send_notification_email


class Command(BaseCommand):
    help = "Sends mails to all persons whose features are about to expire and have not received the mail already."

    def handle(self, *args, **options):
        observed_feature_assignments = FeatureAssignment.objects.annotate(
            date_diff=F("date_expire") - CURRENT_DATETIME().date()
        ).filter(
            date_diff__lte=timedelta(hours=settings.FEATURE_EXPIRE_HOURS_SEND_MAIL),
            expiry_email_sent=False,
            date_returned=None,
        )

        for feature_assignment in observed_feature_assignments:
            if feature_assignment.feature.feature_type == Feature.Type.EQUIPMENT:
                email_text = _(
                    f"Vámi zapůjčenému vybavení {feature_assignment.feature} končí výpůjční lhůta dne {feature_assignment.date_expire}"
                )
            elif feature_assignment.feature.feature_type == Feature.Type.QUALIFICATION:
                email_text = _(
                    f"Dne {feature_assignment.date_expire} dojde k expiraci vaší současné kvalifikace {feature_assignment.feature}"
                )
            elif feature_assignment.feature.feature_type == Feature.Type.PERMISSION:
                email_text = _(
                    f"Dne {feature_assignment.date_expire} dojde k expiraci vašeho současného oprávnění {feature_assignment.feature.name}"
                )
            else:
                raise NotImplementedError
            send_notification_email(
                _("Zdvořilé upozornění"), email_text, [feature_assignment.person]
            )
            feature_assignment.expiry_email_sent = True
            feature_assignment.save()
