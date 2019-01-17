"""Models locations using the Open Weather API."""

# stdlib Imports
import json
import urllib

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.client import getPage

# Zenoss Imports
from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin


class Locations(PythonPlugin):

    """Open Weather locations modeler plugin."""

    relname = 'oweatherLocations'
    modname = 'ZenPacks.training.OpenWeather.OWeatherLocation'

    requiredProperties = (
        'zOWeatherAPIKey',
        'zOWeatherLocations',
        )

    deviceProperties = PythonPlugin.deviceProperties + requiredProperties

    @inlineCallbacks
    def collect(self, device, log):
        """Asynchronously collect data from device. Return a deferred."""
        log.info("%s: collecting data", device.id)

        apikey = getattr(device, 'zOWeatherAPIKey', None)
        if not apikey:
            log.error(
                "%s: %s not set. Get one from https://openweathermap.org/api",
                device.id,
                'zOWeatherAPIKey')

            returnValue(None)

        locations = getattr(device, 'zOWeatherLocations', None)
        if not locations:
            log.error(
                "%s: %s not set.",
                device.id,
                'zOWeatherLocations')

            returnValue(None)

        responses = []
        for location in locations:
            try:
                response = yield getPage(
                    'http://autocomplete.wunderground.com/aq?query={query}'
                    .format(query=urllib.quote(location)))

                responses.append(json.loads(response))
            except Exception, e:
                log.error(
                    "%s: %s", device.id, e)

                returnValue(None)

        returnValue(responses)

    def process(self, device, results, log):
        """Process results. Return iterable of datamaps or None."""

        rm = self.relMap()

        for response in results:
            try:
                for result in response['RESULTS']:
                    rm.append(self.objectMap({
                        'id': self.prepId(result['zmw']),
                        'title': result['name'],
                        'api_link': result['l'],
                        'city_name': result['name'].split(',')[0],
                        'country_code': result['c'],
                        'timezone': result['tzs'],
                        }))
            except (KeyError, TypeError), e:
                log.error(
                    "%s: %s", device.id, e)
                continue

        return rm
