from datetime import datetime, timedelta
from django.utils import timezone

from features.models import FeatureAssignment, Feature
from django.db.models import F
from django.utils.translation import gettext_lazy as _

from vzs import settings
from vzs.utils import send_notification_email


def features_expiry_send_mails():
    observed_feature_assignments = FeatureAssignment.objects.annotate(
        date_diff=F("date_expire")
        - datetime.now(tz=timezone.get_default_timezone()).date()
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
