"""Models locations using the Open Weather API."""

# stdlib Imports
import json
import urllib

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.client import getPage

# Zenoss Imports
from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.ZenCollector.interfaces import IEventService
from zope.component import getUtility
from zenoss.protocols.protobufs.zep_pb2 import SEVERITY_ERROR, SEVERITY_CLEAR

class Locations(PythonPlugin):

    """Open Weather locations modeler plugin."""

    relname = 'oweatherLocations'
    modname = 'ZenPacks.training.OpenWeather.OWeatherLocation'

    requiredProperties = (
        'zOWeatherAPIKey',
        'zOWeatherLocations',
        )

    deviceProperties = PythonPlugin.deviceProperties + requiredProperties

    def makeEvent(self, eventService, deviceId, severity, message):
        eventService.sendEvent({
            'device': deviceId,
            'eventKey': 'oweather-collect',
            'eventClassKey': 'oweather',
            'severity': severity,
            'message': message
        })

    @inlineCallbacks
    def collect(self, device, log):
        """Asynchronously collect data from device. Return a deferred."""
        log.info("%s: collecting data", device.id)
        self._eventService = getUtility(IEventService)

        apikey = getattr(device, 'zOWeatherAPIKey', None)
        if not apikey:
            message = '{}: {} not set. Get one from https://openweathermap.org/api'\
                .format(device.id, 'zOWeatherAPIKey')

            log.error(message)

            self.makeEvent(
                self._eventService,
                device.id,
                SEVERITY_ERROR,
                message
            )

            returnValue(None)

        locations = getattr(device, 'zOWeatherLocations', None)
        if not locations:
            message = '{}: {} not set'\
                .format(device.id, 'zOWeatherLocations')

            log.error(message)

            self.makeEvent(
                self._eventService,
                device.id,
                SEVERITY_ERROR,
                message
            )

            returnValue(None)

        self.makeEvent(
                self._eventService,
                device.id,
                SEVERITY_CLEAR,
                'All good'
            )

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
