FROM nginx/unit:1.26.1-python3.10

RUN apt update && \
    apt install -y python3-pip iproute2 -y && \
    rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

#RUN mkdir /var/lib/unit/certs/ && chown -R unit:unit /var/lib/unit/certs/

RUN useradd -ms /bin/bash nginx

RUN chown -R nginx:nginx /var/lib/unit/
RUN mkdir /var/run/unit/ && chown -R nginx:nginx /var/run/unit/
RUN mkdir /var/log/unit/ && chown -R nginx:nginx /var/log/unit/

USER nginx:nginx

EXPOSE 8000

#ENV SOAP_URL=https://graphical.weather.gov/xml/SOAP_server/ndfdXMLserver.php?wsdl
ENV SOAP_URL=http://www.thomas-bayer.com/axis2/services/BLZService?wsdl

COPY requirements.txt /config/

RUN pip3 install -r /config/requirements.txt

COPY config.json /docker-entrypoint.d/

COPY app.py /www/

HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1