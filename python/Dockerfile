FROM nginx/unit:1.19.0-python3.7

RUN apt update && apt install -y python3-pip && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /config/

RUN pip3 install -r /config/requirements.txt

COPY app.py /www/

COPY config.json /docker-entrypoint.d/

#ENV SOAP_URL=https://graphical.weather.gov/xml/SOAP_server/ndfdXMLserver.php?wsdl
ENV SOAP_URL=http://www.thomas-bayer.com/axis2/services/BLZService?wsdl

EXPOSE 8000