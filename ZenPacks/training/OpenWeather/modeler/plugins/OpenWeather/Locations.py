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
        'zOWeatherAPIVersion',
        'zOWeatherLocations',
        )

    deviceProperties = PythonPlugin.deviceProperties + requiredProperties

    def _makeEvent(self, deviceId, severity, eventKey, summary=None, message=None):
        if severity == SEVERITY_CLEAR:
            summary = '{}: success'.format(eventKey)

        self._eventService.sendEvent({
            'device': deviceId,
            'eventKey': eventKey,
            'eventClassKey': 'oweatherModeling',
            'severity': severity,
            'summary': summary,
            'message': message,
        })

    def getProperty(self, device, nameOfZProperty, log):
        prop = getattr(device, nameOfZProperty, None)
        if not prop:
            message = '{}: {} not set' \
                .format(device.id, nameOfZProperty)

            log.error(message)

            self._makeEvent(
                device.id,
                SEVERITY_ERROR,
                'oweatherMissing_{}'.format(nameOfZProperty),
                summary='zProperty is missing',
                message=message
            )
        else:
            self._makeEvent(
                device.id,
                SEVERITY_CLEAR,
                'oweatherMissing_{}'.format(nameOfZProperty),
            )

        return prop

    @inlineCallbacks
    def collect(self, device, log):
        """Asynchronously collect data from device. Return a deferred."""
        log.info("%s: collecting data", device.id)
        self._eventService = getUtility(IEventService)

        apikey = self.getProperty(device, 'zOWeatherAPIKey', log)
        locations = self.getProperty(device, 'zOWeatherLocations', log)
        apiver = self.getProperty(device, 'zOWeatherAPIVersion', log)

        # Check apikey, apiver, locations. If one is missing then return None
        if not all((apikey, apiver, locations)):
            returnValue(None)

        responses = []
        for location in locations:
            try:
                shortLocation = location.split(',')[0]

                response = yield getPage(
                    'http://autocomplete.wunderground.com/aq?query={query}'
                    .format(query=urllib.quote(location)))

                responses.append((shortLocation, json.loads(response)))
            except Exception as e:
                message = "{}: failed to collect data. {}".format(device.id, e.message)
                log.error(message)

                self._makeEvent(
                    device.id,
                    SEVERITY_ERROR,
                    'oweatherCollect',
                    summary='Failed to collect data',
                    message=message
                )

                returnValue(None)

            else:
                self._makeEvent(
                    device.id,
                    SEVERITY_CLEAR,
                    'oweatherCollect'
                )

        returnValue(responses)

    def process(self, device, results, log):
        """Process results. Return iterable of datamaps or None."""

        rm = self.relMap()

        for location, response in results:
            try:
                if not response['RESULTS']:
                    message = '{}: failed to parse data for {}. '\
                              'Check the location. Maybe the service does not support it'\
                        .format(device.id, location)
                    log.error(message)

                    self._makeEvent(
                        device.id,
                        SEVERITY_ERROR,
                        'oweatherModelingParse_{}'.format(location),
                        summary='Failed to parse data',
                        message=message
                    )
                    continue

                for result in response['RESULTS']:
                    rm.append(self.objectMap({
                        'id': self.prepId(result['zmw']),
                        'title': result['name'],
                        'api_link': result['l'],
                        'city_name': result['name'].split(',')[0],
                        'country_code': result['c'],
                        'timezone': result['tzs'],
                        }))
            except (KeyError, IndexError, ValueError) as e:
                log.error(
                    "%s: %s", device.id, e.message)

                self._makeEvent(
                    device.id,
                    SEVERITY_ERROR,
                    'oweatherModelingParse_{}'.format(location),
                    summary='Failed to parse data',
                    message=e.message
                )
                continue
            else:
                self._makeEvent(
                    device.id,
                    SEVERITY_CLEAR,
                    'oweatherModelingParse_{}'.format(location)
                )

        return rm
