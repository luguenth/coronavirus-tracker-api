from ..services.location.jhu import JhuLocationService
from ..services.location.rki import RkiLocationService

# Mapping of services to data-sources.
data_sources = {
    'jhu': JhuLocationService(),
    'rki': RkiLocationService(),
}

def data_source(source):
    """
    Retrieves the provided data-source service.

    :returns: The service.
    :rtype: LocationService
    """
    return data_sources.get(source.lower())