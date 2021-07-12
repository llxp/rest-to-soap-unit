FROM nginx/unit:1.23.0-node15

COPY package.json /www/package.json
#COPY package-lock.json /www/package-lock.json
#COPY node_modules /www/node_modules

WORKDIR /www/

RUN npm install

COPY app.js /www/

RUN chown -R unit:unit /www/
RUN chmod +x /www/app.js

COPY config.json /docker-entrypoint.d/

#ENV SOAP_URL=https://graphical.weather.gov/xml/SOAP_server/ndfdXMLserver.php?wsdl
ENV SOAP_URL=http://www.thomas-bayer.com/axis2/services/BLZService?wsdl

EXPOSE 8000
