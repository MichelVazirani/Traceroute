# Traceroute
My traceroute assignment from Columbia COMS 4119 Computer Networks course.

To use, simply run the tracerote.py script. This script takes one optional command line
argument, which may be the IP address or the host name of the endpoint you intend to ping.
If not provided, the traceroute.py script will ping "google.com"

Note: this traceroute program uses raw sockets, which require administrator privileges.

e.g. sudo python traceroute.py cnn.com
