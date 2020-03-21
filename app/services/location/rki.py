from . import LocationService
from ...location import TimelinedLocation
from ...coordinates import Coordinates
from ...timeline import Timeline

class RkiLocationService(LocationService):
    """
    Service for retrieving locations from Johns Hopkins CSSE (https://github.com/CSSEGISandData/COVID-19).
    """

    def get_all(self):
        # Get the locations.
        return get_locations()
    
    def get(self, id):
        # Get location at the index equal to provided id.
        return self.get_all()[id]

# ---------------------------------------------------------------

import requests
import csv
from datetime import datetime
from cachetools import cached, TTLCache
from ...utils import countrycodes, date as date_util

"""
Base URL for fetching category.
"""
base_url = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_COVID19/FeatureServer/0/query"

def get_data(): 
    states = {
        8: 'Baden-Württemberg',
        5: 'Nordrhein-Westfalen',
        9: 'Bayern',
        6: 'Hessen',
        3: 'Niedersachsen',
        7: 'Rheinland-Pfalz',
        11: 'Berlin',
        2: 'Hamburg',
        14: 'Sachsen',
        1: 'Schleswig-Holstein',
        12: 'Brandenburg',
        15: 'Sachsen-Anhalt',
        10: 'Saarland',
        16: 'Thüringen',
        13: 'Mecklenburg-Vorpommern',
        4: 'Bremen'
    }

    for states in states:
        querystring = {
            "f": "json",
            "where": "Bundesland='Niedersachsen'",
            "returnGeometry": "false",
            "outFields": "AnzahlFall, Meldedatum",
            "spatialRel": "esriSpatialRelIntersects",
            "orderByFields": "Meldedatum",
            "cacheHInt": "true"
        }
        payload = ""
        response = requests.request("GET", base_url, data=payload, params=querystring)
        pprint.pprint(response.json())

# @cached(cache=TTLCache(maxsize=1024, ttl=3600))
def get_category(category):
    """
    Retrieves the data for the provided category. The data is cached for 1 hour.

    :returns: The data for category.
    :rtype: dict
    """

    # Adhere to category naming standard.
    category = category.lower().capitalize();

    # # Request the data
    data = get_data()

    # THIS IS FOR TESTING PURPOSES ONLY
    return  {
        'locations': [{
            'coordinates': {
                'lat': 123,
                'long': 134,
                },
            'country': "LAND",
            'province': "PROVINZ",

            }
            ]
    }
    ######################

    # The normalized locations.
    locations = []

    for item in data:
        # Filter out all the dates.
        dates = dict(filter(lambda element: date_util.is_date(element[0]), item.items()))

        # Make location history from dates.
        history = { date: int(amount or 0) for date, amount in dates.items() };

        # Country for this location.
        country = item['Country/Region']

        # Latest data insert value.
        latest = list(history.values())[-1];

        # Normalize the item and append to locations.
        locations.append({
            # General info.
            'country':  country,
            'country_code': countrycodes.country_code(country),
            'province': item['Province/State'],

            # Coordinates.
            'coordinates': {
                'lat':  item['Lat'],
                'long': item['Long'],
            },

            # History.
            'history': history,

            # Latest statistic.
            'latest': int(latest or 0),
        })

    # Latest total.
    latest = sum(map(lambda location: location['latest'], locations))

    # Return the final data.
    return {
        'locations': locations,
        'latest': latest,
        'last_updated': datetime.utcnow().isoformat() + 'Z',
        'source': 'https://github.com/ExpDev07/coronavirus-tracker-api',
    }

@cached(cache=TTLCache(maxsize=1024, ttl=3600))
def get_locations():
    """
    Retrieves the locations from the categories. The locations are cached for 1 hour.

    :returns: The locations.
    :rtype: List[Location]
    """
    # Get all of the data categories locations.
    confirmed = get_category('confirmed')['locations']
    deaths    = get_category('deaths')['locations']
    recovered = get_category('recovered')['locations']

    # Final locations to return.
    locations = []

    # Go through locations.
    for index, location in enumerate(confirmed):
        # Get the timelines.
        # Format: { "12/02/90": 25, ... }
        timelines = {
            'confirmed' : confirmed[index]['history'],
            'deaths'    : deaths[index]['history'],
            'recovered' : recovered[index]['history'],
        }

        # Grab coordinates.
        coordinates = location['coordinates']

        # Create location (supporting timelines) and append.
        locations.append(TimelinedLocation(
            # General info.
            index, location['country'], location['province'], 
            
            # Coordinates.
            Coordinates(
                coordinates['lat'], 
                coordinates['long']
            ),

            # Last update.
            datetime.utcnow().isoformat() + 'Z',
        
            # Timelines (parse dates as ISO).
            {
                'confirmed': Timeline({ datetime.strptime(date, '%m/%d/%y').isoformat() + 'Z': amount for date, amount in timelines['confirmed'].items() }),
                'deaths'   : Timeline({ datetime.strptime(date, '%m/%d/%y').isoformat() + 'Z': amount for date, amount in timelines['deaths'].items() }),
                'recovered': Timeline({ datetime.strptime(date, '%m/%d/%y').isoformat() + 'Z': amount for date, amount in timelines['recovered'].items() })
            }
        ))

    print(locations)
    
    # Finally, return the locations.
    return locations 
