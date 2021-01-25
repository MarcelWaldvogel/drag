# Drag: A Webook listener dragging along its dockerized service

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
FROM cznic/knot:3

RUN apt update && apt install -y python3-pip && apt clean
RUN pip3 install drag

# Set the variables
ENV DRAG_SECRET 123
ENV DRAG_COMMAND cd /storage/data && git update && knotc reload

# Just prepend `drag` to the original command line
CMD drag knot -c /config/knot.cfg
```

# Operation

`drag` forks a child process, which listen for HTTP webhook requests on port
1291, verifying them against `DRAG_SECRET`, before running `DRAG_COMMAND`.

The main process replaces itself by what the service process, so it maintains
process ID 1, and termination of the service process will be managed by Docker
as usual.

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
