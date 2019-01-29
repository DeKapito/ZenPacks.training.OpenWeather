"""Monitors current conditions using the Weather Underground API."""

# Logging
import logging
LOG = logging.getLogger('zen.OpenWeather')

# stdlib Imports
import json
import time

from Products.DataCollector.plugins.DataMaps import ObjectMap
from zenoss.protocols.protobufs.zep_pb2 import SEVERITY_ERROR, SEVERITY_CLEAR

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.client import getPage

# PythonCollector Imports
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import (
    PythonDataSourcePlugin,
    )

from ZenPacks.training.OpenWeather.util import camelCaseToSnake


class Conditions(PythonDataSourcePlugin):

    """Open Weather conditions data source plugin."""

    @classmethod
    def config_key(cls, datasource, context):
        return (
            context.device().id,
            datasource.getCycleTime(context),
            context.id,
            'oweather-conditions',
            )

    @classmethod
    def params(cls, datasource, context):
        return {
            'api_key': context.zOWeatherAPIKey,
            'api_version': context.zOWeatherAPIVersion,
            'city_name': context.city_name,
            'country_code': context.country_code,
            'location_name': context.title,
            }

    def _makeEvent(self, deviceId, component, severity, eventKey, summary=None, message=None):
        if severity == SEVERITY_CLEAR:
            summary = '{}: success'.format(eventKey)

        self.data['events'].append({
            'device': deviceId,
            'component': component,
            'eventKey': eventKey,
            'eventClassKey': 'oweatherConditions',
            'severity': severity,
            'summary': summary,
            'message': message,
        })

    @inlineCallbacks
    def collect(self, config):
        self.data = self.new_data()
        datasource = config.datasources[0]

        try:
            response = yield getPage(
                'https://api.openweathermap.org/data/{api_version}/weather?q={city_name},{country_code}&units=metric&appid={api_key}'
                .format(
                    api_key=datasource.params['api_key'],
                    api_version=datasource.params['api_version'],
                    city_name=datasource.params['city_name'],
                    country_code=datasource.params['country_code']))

            response = json.loads(response)
        except Exception as e:
            message = "{}: failed to get conditions data for {}. {}"\
                .format(config.id, datasource.params['location_name'], e.message)

            LOG.exception(message)

            self._makeEvent(
                config.id,
                datasource.component,
                SEVERITY_ERROR,
                'oweatherConditionsCollect_{}'.format(datasource.params['location_name']),
                summary='Failed to get conditions',
                message=message
            )
        else:
            self._makeEvent(
                config.id,
                datasource.component,
                SEVERITY_CLEAR,
                'oweatherConditionsCollect_{}'.format(datasource.params['location_name'])
            )

        try:
            weatherId = response['weather'][0]['id']
            main = response['main']
            wind = response['wind']
        except (KeyError, IndexError) as e:
            message = "{}: failed to parse conditions data for {}. {}" \
                .format(config.id, datasource.params['location_name'], e.message)

            LOG.exception(message)

            self._makeEvent(
                config.id,
                datasource.component,
                SEVERITY_ERROR,
                'oweatherConditionsParse_{}'.format(datasource.params['location_name']),
                summary='Failed to parse conditions',
                message=message
            )

            returnValue(self.data)
        else:
            self._makeEvent(
                config.id,
                datasource.component,
                SEVERITY_CLEAR,
                'oweatherConditionsParse_{}'.format(datasource.params['location_name'])
            )

        for datapointId in (x.id for x in datasource.points):
            jsonKey = camelCaseToSnake(datapointId)
            for block in (main, wind):
                if jsonKey not in block:
                    continue
                try:
                    value = float(block[jsonKey])

                    if datapointId == 'pressure':
                        value *= 100

                except (TypeError, ValueError):
                    # Sometimes values are NA or not available.
                    continue

                dpname = '_'.join((datasource.datasource, datapointId))
                self.data['values'][datasource.component][dpname] = (value, 'N')

        dpname = '_'.join((datasource.datasource, 'weather'))
        self.data['values'][datasource.component][dpname] = (weatherId, 'N')

        returnValue(self.data)
