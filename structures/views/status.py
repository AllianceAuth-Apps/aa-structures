"""Status views."""

from django.http import HttpRequest, HttpResponse, HttpResponseServerError
from django.utils.translation import gettext_lazy as _

from structures.models import Owner


def service_status(request: HttpRequest):
    """Public view to 3rd party monitoring.

    This is view allows running a 3rd party monitoring on the status
    of this services. Service will be reported as down if any of the
    configured structure or notifications syncs fails or is delayed
    """
    status_ok = True
    for owner in Owner.objects.filter(is_included_in_service_status=True):
        status_ok = status_ok and owner.are_all_syncs_ok

    if status_ok:
        return HttpResponse(_("service is up"))
    return HttpResponseServerError(_("service is down"))
