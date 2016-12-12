# Bus Times

[![Build Status](https://travis-ci.org/jclgoodwin/bustimes.org.uk.svg?branch=master)](https://travis-ci.org/jclgoodwin/bustimes.org.uk)
[![Coverage Status](https://coveralls.io/repos/github/jclgoodwin/bustimes.org.uk/badge.svg?branch=master)](https://coveralls.io/github/jclgoodwin/bustimes.org.uk?branch=master)

## What's this?

It's [a thing about buses](https://bustimes.org.uk/).

## Installing

A database supported by GeoDjango is required – I use PostgreSQL with PostGIS.

I host the production website on a single Linode server. [config/provision.sh](config/provision.sh) some of the necessary steps for setting one up.

In an emergency, it's possible to run this on Heroku, but that's relatively expensive, and things like the data import script (see below) expect a persistent file system.

## Importing data

[`import.sh`](data/import.sh) will download data from various [sources](https://bustimes.org.uk/data) and run the necessary Django [management commands](busstops/management/commands) to import it.
When run repeatedly, it will only download and import the stuff that's changed.
It expects to be run from the [`data`](data) directory, and needs a username and password to import TNDS data.
