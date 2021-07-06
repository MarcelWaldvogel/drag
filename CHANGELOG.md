# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).


# 0.1.3 - 2021-07-06
## Added
- `DRAG_INTERVAL` can be set to a human-readable time interval
  (e.g., "3h 8.5s") to enable regular polling of the `DRAG_COMMAND`,
  in case a webhook event went missing.

## Fixed
* Log output actually substitutes values.

## Changed
- Requires `deltat` package.


# 0.1.2 - 2021-02-08
## Added
* `DRAG_INIT` and `DRAG_COMMAND` are run inside a shell. This should not
  introduce security issues, as the command is not (yet) dependent on user
  input (only on admin configuration).

## Fixed

## Changed
* More and clearer diagnostic messages


# 0.1.1 - 2021-02-08
## Added
* If `DRAG_INIT` environment variable exists, that command is run at start-up.
  E.g., setting it to the same value as `DRAG_COMMAND` will run the hook at
  start-up, to compensate for potentially having missed events.

## Fixed

## Changed


# 0.1.0 - 2021-01-25
## Added
* First release; use `DRAG_SECRET` and `DRAG_COMMAND` environment variables to
  configure.

## Fixed

## Changed
