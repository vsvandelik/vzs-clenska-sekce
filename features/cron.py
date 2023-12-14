from datetime import timedelta

from django.db.models import F
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _

from features.models import Feature, FeatureAssignment
from vzs.settings import CURRENT_DATETIME, FEATURE_EXPIRE_HOURS_SEND_MAIL
from vzs.utils import send_notification_email, today


def _create_email_text(feature_type: str, feature_assignment: FeatureAssignment):
    match feature_type:
        case Feature.Type.EQUIPMENT:
            return _(
                f"Vámi zapůjčenému vybavení {feature_assignment.feature}"
                f"končí výpůjční lhůta dne {feature_assignment.date_expire}"
            )
        case Feature.Type.QUALIFICATION:
            return _(
                f"Dne {feature_assignment.date_expire} dojde k expiraci"
                f"vaší současné kvalifikace {feature_assignment.feature}"
            )
        case Feature.Type.PERMISSION:
            return _(
                f"Dne {feature_assignment.date_expire} dojde k expiraci"
                f"vašeho současného oprávnění {feature_assignment.feature}"
            )
        case _:
            raise NotImplementedError


def features_expiry_send_mails():
    observed_feature_assignments = FeatureAssignment.objects.annotate(
        date_diff=F("date_expire") - today()
    ).filter(
        date_diff__lte=timedelta(hours=FEATURE_EXPIRE_HOURS_SEND_MAIL),
        expiry_email_sent=False,
        date_returned=None,
    )

    for feature_assignment in observed_feature_assignments:
        email_text = _create_email_text(
            feature_assignment.feature.feature_type, feature_assignment
        )

        send_notification_email(
            _("Zdvořilé upozornění"), email_text, [feature_assignment.person]
        )

        feature_assignment.expiry_email_sent = True
        feature_assignment.save()
