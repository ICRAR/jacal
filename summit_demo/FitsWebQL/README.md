# Docker Notes

## NOTE

This is a fat build. 
It puts everything into the Docker container even though it really isn't necessary
I'll use Docker contexts later to make it smaller

### Build

```bash
docker build -t fits-web-ql .
```

### Running FitsWebQL

```bash
docker run -it --rm XXX /bin/bash

```

### Logging into Docker Container

```bash
docker exec -it devtest /bin/bash
```

### Stopping all docker containers
```bash
docker stop $(docker ps -aq)
```

```bash
docker rm $(docker ps -aq)
```

```bash
docker rmi $(docker images -q)
```
