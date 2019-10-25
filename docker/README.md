# Building the docker files

```
docker build -f 001-Git-Yandasoft.Dockerfile -t jacal-001-git-yandasoft . 

docker build -f 002-Libraries.Dockerfile -t jacal-002-libraries . 

docker build -f 003-Build-Yandasoft.Dockerfile -t jacal-003-build-yandasoft . 

docker build -f 004-Daliuge.Dockerfile -t jacal-004-daliuge . 

docker build -f 005-Git-Jacal.Dockerfile -t jacal-005-git-jacal . 

docker build -f 006-Build-Jacal.Dockerfile -t jacal-006-build-jacal .
```