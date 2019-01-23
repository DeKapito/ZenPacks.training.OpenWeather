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

    @inlineCallbacks
    def collect(self, config):
        data = self.new_data()

        for datasource in config.datasources:
            try:
                response = yield getPage(
                    'https://api.openweathermap.org/data/{api_version}/weather?q={city_name},{country_code}&units=metric&appid={api_key}'
                    .format(
                        api_key=datasource.params['api_key'],
                        api_version=datasource.params['api_version'],
                        city_name=datasource.params['city_name'],
                        country_code=datasource.params['country_code']))

                response = json.loads(response)
            except Exception, e:
                message = "{}: failed to get conditions data for {}"\
                    .format(config.id, datasource.params['location_name'])

                LOG.exception(message)

                data['events'].append({
                    'device': config.id,
                    'component': datasource.component,
                    'eventKey': 'oweatherConditionsCollect_%s' % datasource.params['location_name'],
                    'eventClassKey': 'oweatherConditions',
                    'severity': SEVERITY_ERROR,
                    'summary': message,
                    'message': e,
                })
                continue
            else:
                data['events'].append({
                    'device': config.id,
                    'component': datasource.component,
                    'eventKey': 'oweatherConditionsCollect_%s' % datasource.params['location_name'],
                    'eventClassKey': 'oweatherConditions',
                    'severity': SEVERITY_CLEAR,
                    'summary': '',
                })

            try:
                weather = response['weather'][0]['description']
                main = response['main']
                wind = response['wind']
            except (KeyError, IndexError), e:
                message = "{}: failed to parse conditions data for {}" \
                    .format(config.id, datasource.params['location_name'])

                LOG.exception(message)

                data['events'].append({
                    'device': config.id,
                    'component': datasource.component,
                    'eventKey': 'oweatherConditionsParse_%s' % datasource.params['location_name'],
                    'eventClassKey': 'oweatherConditions',
                    'severity': SEVERITY_ERROR,
                    'summary': message,
                    'message': e
                })

                returnValue(data)
            else:
                data['events'].append({
                    'device': config.id,
                    'component': datasource.component,
                    'eventKey': 'oweatherConditionsParse_%s' % datasource.params['location_name'],
                    'eventClassKey': 'oweatherConditions',
                    'severity': SEVERITY_CLEAR,
                    'summary': '',
                })

            for datapointId in (x.id for x in datasource.points):
                jsonKey = camelCaseToSnake(datapointId)
                for block in (weather, main, wind):
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
                    data['values'][datasource.component][dpname] = (value, 'N')

            data['maps'].append(
                ObjectMap({
                    'relname': 'oweatherLocations',
                    'modname': 'ZenPacks.training.OpenWeather.OWeatherLocation',
                    'id': datasource.component,
                    'weather': weather
                }))

        returnValue(data)
