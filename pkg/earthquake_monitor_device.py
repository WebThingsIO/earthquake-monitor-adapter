"""Earthquake monitor adapter for WebThings Gateway."""

from gateway_addon import Device
from geojson_client import UPDATE_ERROR, UPDATE_OK
from geojson_client.usgs_earthquake_hazards_program_feed import (
    UsgsEarthquakeHazardsProgramFeed
)
import datetime
import threading
import time

from .earthquake_monitor_property import EarthquakeMonitorProperty


class EarthquakeMonitorDevice(Device):
    """Earthquake monitor device type."""

    def __init__(self, adapter, _id, name, latitude, longitude, radius,
                 magnitude, poll_interval, active_interval):
        """
        Initialize the object.

        adapter -- the Adapter managing this device
        _id -- ID of this device
        name -- location name
        latitude -- latitude of center point
        longitude -- longitude of center point
        radius -- radius in kilometers around center point to include
        magnitude -- minimum event magnitude to include
        """
        Device.__init__(self, adapter, _id)
        self._type = ['BinarySensor']

        self.latitude = latitude
        self.longitude = longitude
        self.radius = radius
        self.magnitude = magnitude
        self.poll_interval = poll_interval
        self.active_interval = active_interval

        self.name = 'Earthquake Monitor ({})'.format(name)
        self.description = self.name

        self.properties['earthquake'] = EarthquakeMonitorProperty(
            self,
            'earthquake',
            {
                '@type': 'BooleanProperty',
                'title': 'Earthquake',
                'type': 'boolean',
                'readOnly': True,
            },
            False
        )

        self.properties['magnitude'] = EarthquakeMonitorProperty(
            self,
            'magnitude',
            {
                'title': 'Magnitude',
                'type': 'number',
                'readOnly': True,
            },
            0
        )

        self.properties['distance'] = EarthquakeMonitorProperty(
            self,
            'distance',
            {
                'title': 'Distance',
                'type': 'integer',
                'unit': 'kilometer',
                'readOnly': True,
            },
            0
        )

        self.properties['time'] = EarthquakeMonitorProperty(
            self,
            'time',
            {
                'title': 'Time (UTC)',
                'type': 'string',
                'readOnly': True,
            },
            ''
        )

        self.properties['place'] = EarthquakeMonitorProperty(
            self,
            'place',
            {
                'title': 'Place',
                'type': 'string',
                'readOnly': True,
            },
            ''
        )

        self.links = [
            {
                'rel': 'alternate',
                'mediaType': 'text/html',
                'href': 'https://earthquake.usgs.gov/earthquakes/map/',
            },
        ]

        t = threading.Thread(target=self.poll)
        t.daemon = True
        t.start()

    def poll(self):
        """Poll USGS for changes."""
        feed = UsgsEarthquakeHazardsProgramFeed(
            (self.latitude, self.longitude),
            'past_day_all_earthquakes',
            filter_radius=self.radius,
            filter_minimum_magnitude=self.magnitude
        )

        while True:
            status, entries = feed.update()

            if status == UPDATE_OK and len(entries) > 0:
                self.connected_notify(True)
                latest = entries[0]

                now = datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc
                )
                delta = now - latest.time

                if delta < datetime.timedelta(minutes=self.active_interval):
                    self.properties['earthquake'].update(True)
                    self.properties['magnitude'].update(latest.magnitude)
                    self.properties['distance'].update(
                        round(latest.distance_to_home)
                    )
                    self.properties['time'].update(
                        str(latest.time).split('.')[0]
                    )
                    self.properties['place'].update(latest.place)
                else:
                    self.properties['earthquake'].update(False)
                    self.properties['magnitude'].update(0)
                    self.properties['distance'].update(0)
                    self.properties['time'].update('')
                    self.properties['place'].update('')
            elif status == UPDATE_ERROR:
                self.connected_notify(False)

            time.sleep(self.poll_interval)
