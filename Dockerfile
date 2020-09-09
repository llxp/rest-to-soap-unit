FROM nginx/unit:1.19.0-python3.7

ENV SOAP_URL=http://www.thomas-bayer.com/axis2/services/BLZService?wsdl

COPY requirements.txt /config/

RUN apt update && apt install -y python3-pip    \
    && pip3 install -r /config/requirements.txt \
    && rm -rf /var/lib/apt/lists/*

COPY app.py /www/

COPY config.json /docker-entrypoint.d/

EXPOSE 8000