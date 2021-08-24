
# rest-to-soap-unit

a simple python/flask rest api hosted on nginx unit for proxying/transforming a rest request to an internal soap interface  

![Diagram](diagram.png)

# Building

adjust the url of the wsdl file in the Dockerfile (or later using the environment variable SOAP_URL):

```bash
SOAP_URL=http://www.thomas-bayer.com/axis2/services/BLZService?wsdl
```

Next build the docker image:

```bash
docker build -t rest-to-soap-unit nodejs/
docker build -t rest-to-soap-unit-helper python/
```

# Usage

To run the docker container:

```bash
docker run --name rest-to-soap-unit -d -p 127.0.0.1:8080:8000 rest-to-soap-unit
docker run --name rest-to-soap-unit-helper -d -p 127.0.0.1:9090:8000 rest-to-soap-unit-helper
```

# Systemd

There are also systemd unit files included, which can be used to control the containers using systemd
There will be created a docker network to run the containers into, to be able to e.g. put a reverse proxy before and then combine each individual rest-to-soap-unit to one api
The containers will be controlled using the environment file, which should be created at
/etc/rest-to-soap-unit/<systemd service alias>.env
/etc/rest-to-soap-unit/service.env
and
/etc/rest-to-soa-unit/<systemd service alias>-helper.env
e.g. /etc/rest-to-soap-unit/service-helper.env
you can then control the service using:
```bash
systemctl start rest-to-soap-unit@service
systemctl start rest-to-soap-unit-helper@service
```

To use the app, execute a rest request to the mapped port 8080 on localhost:
e.g. when using the default wsdl (public soap service for getting details about a german bank by providing the bank code or blz):

```bash
curl -X POST -d "50010060" http://localhost:8080/api/getBank
```

the result should be:

```json
{
    "bezeichnung": "Postbank",
    "bic": "PBNKDEFFXXX",
    "ort": "Frankfurt am Main",
    "plz": "60288"
}
```

# Usage in docker-compose

```docker
version: '3'
services:
  rest-to-soap-unit:
    build: nodejs/
    image: rest-to-soap-unit:latest
    ports:
      - "127.0.0.1:8080:8000"  # Map port 8000 of docker container to 8080 on localhost
    environment:
      - SOAP_URL=http://www.thomas-bayer.com/axis2/services/BLZService?wsdl
  rest-to-soap-unit-helper:
    build: python/
    image: rest-to-soap-unit-helper:latest
    ports
      - "127.0.0.1:9090:8000"  # Map port 8000 of docker container to 9090 on localhost
    environment:
      - SOAP_URL=http://www.thomas-bayer.com/axis2/services/BLZService?wsdl
```

# Swagger-UI

The swagger-ui can be accessed on the /doc endpoint
so e.g. open [http://127.0.0.1:9090/doc](http://127.0.0.1:9090/doc) in the browser and the swagger-ui will open

# Swagger-Configuration file

The swagger-/openapi-configuration file can be retrieved on the /help endpoint
so e.g. open [http://127.0.0.1:9090/help](http://127.0.0.1:9090/help) in the browser and the swagger-configuration file will load

# BUG IN ZEEP

Because of a bug in zeep I rewrote the rest-to-soap-unit in nodejs.
The workaround currently is to have two containers, one for the translation from rest to soap and one to be able to autogenerate an openapi specification.
Because of time, I am currently using this workaround, but in the future, I will also rewrite the openapi specification generator in nodejs.
For now, the python container is generating the openapi specification
and the nodejs container is handling the translation traffic.
