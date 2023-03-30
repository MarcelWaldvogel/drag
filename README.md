# Drag: A Webhook listener dragging along its dockerized service

Minimalistic GitHub/GitLab webhook listener for use in an existing Docker image.

# Problem

The basic premise for Docker and other virtualization environments is to
isolate the single service they provide from the environment, for containment,
ease of administration, and security.

Sometimes, however, it is necessary to inform the running service of changes,
without having to recreate the entire container. For example, a web or DNS
server should serve new files or use a different configuration.

The classic solution is to expose the directory tree in question to the host or
another container, which updates the contents. That works great unless the
server needs to be informed when it should start to use the new data.

Running the update process on the host is often not an option. Running it
inside another container requires either a listener in the service container
(which brings us back to square one) or exposing the Docker control socket to
the container, with security and dependency problems.

Alternatives include running a service manager inside the container.

# Solution: Webhook inside the service container

`drag` is an easy way of adding a webhook to an existing container.
Just create a `Dockerfile` inheriting from the original service, installing
`drag` and using it as a wrapper for the original command.

```Dockerfile
FROM cznic/knot:latest

RUN apt update && \
    apt install --no-install-recommends --yes python3-pip git ssh && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*
RUN pip3 install drag && rm -rf ${HOME}/.cache

# `drag` is configured by environment variables
# The secret that must be part of a GitHub- or GitLab-style request
ENV DRAG_SECRET 123
# The command to execute, passed to a shell
ENV DRAG_COMMAND cd /storage/data && git update && knotc reload
# Ensure everything is up to date at start (cannot reload daemon yet)
ENV DRAG_INIT cd /storage/data && git update

# Just prepend `drag` to the original command line
CMD ["drag", "knot", "-c", "/config/knot.cfg']
```

# Operation

`drag` forks a child process, which listen for HTTP webhook requests on port
1291, verifying them against `DRAG_SECRET`, before running `DRAG_COMMAND`.

The main process replaces itself by the service process, so it maintains
process ID 1, and termination of the service process will be managed by Docker
as usual.

# Configuration

`drag` can be configured by 4 environment variables:

* `DRAG_SECRET` (required): A secret the sender must provide to authenticate
  itself. GitHub and GitLab style are supported, detection is automatic:
  - GitLab style: The value of the HTTP request header `X-GitLab-Token` must
    match.
  - GitHub style: The HTTP request header `X-Hub-Signature` must contain the
    hex digest of the SHA-1 HMAC of the request body, keyed by `DRAG_SECRET`.
* `DRAG_INIT` (optional): A command to be run before the main process is run.
  This will be processed by the shell, see below.
* `DRAG_COMMAND` (required): The command to be run when the webhook fires.
  Again, shell processing is performed, see below.
* `DRAG_INTERVAL` (optional): Set this, if the `DRAG_COMMAND` should *also*
  be run in regular intervals. This interval is specified in human-readable
  form, e.g. `1h 3.5s`. This is especially useful, when `drag` is used to
  respond to remote repository updates. Polling the repository at a low rate
  ensures that there temporary service outages will not result in missing an
  update, only in potentially delaying it.

## Security considerations

### Shell expansion
`DRAG_INIT` and `DRAG_COMMAND` are subject to shell processing (e.g.,
variables, backquotes, pipes, redirects, splitting at spaces after
substitution, …). This greatly increases the power of these commands, but their
effects should be anticipated.

However, this is not considered a security problem itself, as only a system
admin should be able to modify the configuration file this variable is read
from (`docker-compose.yml`, `.env`, …). Anyone able to write to these files can
probably already perform privilege escalation, and probably on the host system,
not only inside the container. So, in general, this poses no additional
security risks.

### No request contents
The actual contents of the webhook request are thrown away by `drag` and *not*
passed to child processes under any circumstances. This ensures that the hook
process will never have to deal with attacker-controlled input and probably
treat it without the proper care.

### GitLab token
Anyone learning the GitLab token can call the webhook later. If this should not
happen, the GitLab token should only ever travel over trusted network
connections or inside a secure tunnel. This can be ensured with a HTTPS proxy
running on the same machine, as outlined below.

# HTTPS support

HTTPS support is missing on purpose, as it is expected that you already run
your HTTPS proxy somewhere. If not, have a look at
[https-portal](https://github.com/SteveLTN/https-portal), which can be
configured e.g. with the following lines of `docker-compose.yml`:

```yaml
version: '2'
services:
  reverse-proxy:
    image: steveltn/https-portal:1
    restart: unless-stopped
    volumes:
      - ./ssl-certs:/var/lib/https-portal
      - ./vhosts:/var/www/vhosts
    ports:
      - '80:80'
      - '443:443'
    environment:
      DOMAINS: |
        hook.example.com -> dockerhost:1291,
        (more domains here)
```
