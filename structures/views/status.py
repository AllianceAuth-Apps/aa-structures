"""Status views."""

from django.http import HttpRequest, HttpResponse, HttpResponseServerError

from structures.models import Owner


def service_status(request: HttpRequest):
    """Public view to 3rd party monitoring.

    This is view allows running a 3rd party monitoring on the status
    of this services. Service will be reported as down if any of the
    configured structure or notifications syncs fails or is delayed
    """
    active_owners = Owner.objects.filter(
        is_included_in_service_status=True, is_active=True
    )
    for owner in active_owners:
        if not owner.are_all_syncs_ok:
            return HttpResponseServerError("service is down")

    return HttpResponse("service is up")
