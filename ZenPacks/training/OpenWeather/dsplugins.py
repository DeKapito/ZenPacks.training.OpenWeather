"""Monitors current conditions using the Weather Underground API."""

# Logging
import logging
LOG = logging.getLogger('zen.OpenWeather')

# stdlib Imports
import json
import time

from Products.DataCollector.plugins.DataMaps import ObjectMap

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.client import getPage

# PythonCollector Imports
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import (
    PythonDataSourcePlugin,
    )


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
                    'https://api.openweathermap.org/data/2.5/weather?q={city_name},{country_code}&units=metric&appid={api_key}'
                    .format(
                        api_key=datasource.params['api_key'],
                        city_name=datasource.params['city_name'],
                        country_code=datasource.params['country_code']))

                response = json.loads(response)
            except Exception:
                LOG.exception(
                    "%s: failed to get conditions data for %s",
                    config.id,
                    datasource.params['location_name'])

                continue

            weather = response['weather'][0]
            main = response['main']
            wind = response['wind']
            for datapoint_id in (x.id for x in datasource.points):
                for block in (weather, main, wind):
                    if datapoint_id not in block:
                        continue

                    try:
                        value = block[datapoint_id]
                        if isinstance(value, basestring):
                            value = value.strip(' %')

                        value = float(value)

                        if datapoint_id == 'pressure':
                            value *= 100

                    except (TypeError, ValueError):
                        # Sometimes values are NA or not available.
                        continue

                    dpname = '_'.join((datasource.datasource, datapoint_id))
                    data['values'][datasource.component][dpname] = (value, 'N')

            data['maps'].append(
                ObjectMap({
                    'relname': 'oweatherLocations',
                    'modname': 'ZenPacks.training.OpenWeather.OWeatherLocation',
                    'id': datasource.component,
                    'weather': response['weather'][0]['description']
                }))

        returnValue(data)
