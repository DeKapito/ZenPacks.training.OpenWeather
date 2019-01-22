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

    def getProperty(self, device, nameOfZProperty, log):
        prop = getattr(device, nameOfZProperty, None)
        if not prop:
            message = '{}: {} not set' \
                .format(device.id, nameOfZProperty)

            log.error(message)
            self._eventService.sendEvent({
                'device': device.id,
                'eventKey': 'oweatherMissing_%s' % nameOfZProperty,
                'eventClassKey': 'oweatherModeling',
                'severity': SEVERITY_ERROR,
                'message': message
            })
        else:
            self._eventService.sendEvent({
                'device': device.id,
                'eventKey': 'oweatherMissing_%s' % nameOfZProperty,
                'eventClassKey': 'oweatherModeling',
                'severity': SEVERITY_CLEAR,
                'summary': ''
            })

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
        if not (apikey and apiver and locations):
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

                # TODO: Maybe add event

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
            except (KeyError, IndexError, ValueError), e:
                log.error(
                    "%s: %s", device.id, e)

                # TODO: Change eventKey for avoid clearing for all cases!!!
                self._eventService.sendEvent({
                    'device': device.id,
                    'eventKey': 'oweatherModelingParse',
                    'eventClassKey': 'oweatherModeling',
                    'severity': SEVERITY_ERROR,
                    'message': e
                })
                continue
            else:
                # TODO: Change this code!!! Clearing rewrite error!!! In case when error raise before clearing.
                self._eventService.sendEvent({
                    'device': device.id,
                    'eventKey': 'oweatherModelingParse',
                    'eventClassKey': 'oweatherModeling',
                    'severity': SEVERITY_CLEAR,
                    'summary': ''
                })

        return rm
