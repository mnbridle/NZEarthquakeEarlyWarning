# NZEarthquakeEarlyWarning

This script polls Geonet's API for earthquakes every 15 seconds and, if a large earthquake has been detected, it sends a notification to a mobile device using SimplePush.io and/or plays an audio alert.

As Geonet is pretty good at detecting and reporting the approximate location/magnitude of earthquakes (usually within 1 or 2 minutes), depending on how far away the user is from the epicenter, this script might give at least a few seconds' warning to take cover.

Please note this script is only to be used for educational purposes, and use commonsense; this may give some warning, but if the earthquake is locally-sourced then an alert will likely be received after the event.  If you feel an earthquake, don't wait for a notification - drop, cover and hold.
