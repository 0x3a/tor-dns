## Tor & onionviewer ##
=============

This repository contains a modified version of Tor which allows a node setup to be a hidden service directory to log all successfully resolved hidden services.
Additionally this repository also contains tools to parse the Tor notice log for resolved hidden services. These tools will put the results in a SQLite database which can be viewed and researched with the provided *onionviewer* web application.

Complete technical details can be found on the blog article this repository accompanies: [http://blog.0x3a.com/post/153468210759/monitoring-dns-inside-the-tor-network](http://blog.0x3a.com/post/153468210759/monitoring-dns-inside-the-tor-network)