=======================================
ZenPack for monitoring Open Weather API
=======================================

Description
===========

This ZenPack for monitoring weather using Open Weather API. A new OpenWeather device type is
created with a new component type to represent locations wich monitored.

The ZenPack provides a modeler plugin to collect data about locations specified in
the zOWeatherLocations which uses Weather Underground Autocomplete API.

It also provides device class `/OpenWeather`.

Objects
=======

A new device object class - `OWeatherDevice` - with a relationship of `OWeatherLocation`.
A new component object class for a `OWeatherDevice` - `OWeatherLocation` -
with a relationship `OWeatherDevice`.

Modeler Plugins
===============

A modeler plugin - Locations - which gathers id, name, short name, country code, timezone of locations.
Plugin uses Weather Underground Autocomplete API for collect data about locations.
The locations for which data is collected are read from the `zOWeatherLocations` property.

The Locations plugin is assigned to the `/OpenWeather` device class by the ZenPack.

Templates
=========

Component template Location is available for device classes from `/OpenWeather`.

Gathered data:

* current, min and max temperature (in degrees Celsius)
* atmospheric pressure (in pascals)
* humidity (in percents)
* wind speed (in mps)
* weather (short description).

There is the "Low temperature" threshold. When temperature less than -2 degrees Celsius, an
event with `/OWeather` eventClass is generated.

Graphs:

* temperatures
* humidity
* pressure
* wind speed

zProperties
===========

* `zOWeatherAPIKey` - api key is required to access the Open Weather api
* `zOWeatherAPIVersion` - version of Open Weather api (default value is 2.5)
* `zOWeatherLocations` - list of locations for monitoring (default values are: `Austin, TX\\n
  San Jose, CA\\n Annapolis, MD`).

Events
======
The performance template has a threshold which generates an event of class `/OWeather`.
event class keys such as `oweatherConditions` and `oweatherModeling` mapped in `/OWeather`
event class

Daemons
========
There is no daemon shipped with this ZenPack.

Requirements & Dependencies
===========================

    * Zenoss Versions Supported: 4.x
    * External Dependencies:
    * ZenPack Dependencies:
        * ZenPacks.zenoss.ZenPackLib
    * Installation Notes: Restart zenoss after installation
    * Configuration:

Download
========
The ZenPack will be made available on github.

ZenPack installation
======================

Beware, as with any ZenPack, if you remove the ZenPack and devices exist under
classes defined in this ZenPack - `/OWeather` - then these
devices will be removed.

To install in development mode, download the bundle from github, unpack it
in a convenient directory, change to that directory, and use:

    * zenpack --link --install ZenPacks.training.OpenWeather
    * Restart zenoss with "zenoss restart"

Change History
==============
* 1.0.0
   * Initial Release