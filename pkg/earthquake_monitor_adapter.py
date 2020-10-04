"""Earthquake monitor adapter for WebThings Gateway."""

from gateway_addon import Adapter, Database
import hashlib

from .earthquake_monitor_device import EarthquakeMonitorDevice


class EarthquakeMonitorAdapter(Adapter):
    """Adapter for USGS earthquake hazards."""

    def __init__(self, verbose=False):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """
        self.name = self.__class__.__name__
        Adapter.__init__(self,
                         'earthquake-monitor-adapter',
                         'earthquake-monitor-adapter',
                         verbose=verbose)

        self.pairing = False
        self.start_pairing()

    def start_pairing(self, timeout=None):
        """
        Start the pairing process.

        timeout -- Timeout in seconds at which to quit pairing
        """
        if self.pairing:
            return

        self.pairing = True

        database = Database('earthquake-monitor-adapter')
        if not database.open():
            return

        config = database.load_config()
        database.close()

        if not config or 'locations' not in config:
            return

        for location in config['locations']:
            sha = hashlib.sha1()
            sha.update(location['name'].encode('utf-8'))
            _id = 'earthquake-monitor-{}'.format(sha.hexdigest())
            if _id not in self.devices:
                device = EarthquakeMonitorDevice(
                    self,
                    _id,
                    location['name'],
                    location['latitude'],
                    location['longitude'],
                    location['radius'],
                    location['magnitude'],
                    location['pollInterval'],
                    location['activeInterval'],
                )
                self.handle_device_added(device)

        self.pairing = False

    def cancel_pairing(self):
        """Cancel the pairing process."""
        self.pairing = False
