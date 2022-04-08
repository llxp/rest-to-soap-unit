FROM nginx/unit:1.26.1-php8.0

RUN apt update && \
    apt install lsb-release ca-certificates apt-transport-https software-properties-common gnupg2 libxml2-dev libzip-dev git -y && \
    dpkg -l && \
    rm -rf /var/lib/apt/lists/*

RUN curl -L https://www.php.net/distributions/php-8.0.11.tar.gz > /usr/local/src/php-8.0.11.tar.gz && gunzip /usr/local/src/php-8.0.11.tar.gz && tar xvf /usr/local/src/php-8.0.11.tar -C /usr/local/src/ && rm /usr/local/src/php-8.0.11.tar
WORKDIR /usr/local/src/php-8.0.11/ext/zip
RUN phpize && ./configure && make && cp modules/zip.so /usr/local/lib/php/extensions/no-debug-non-zts-20200930
WORKDIR /usr/local/src/php-8.0.11/ext/soap
RUN phpize && ./configure && make && cp modules/soap.so /usr/local/lib/php/extensions/no-debug-non-zts-20200930
RUN echo "extension=zip" > /usr/local/etc/php/conf.d/zip.ini
RUN echo "extension=soap" > /usr/local/etc/php/conf.d/soap.ini

# RUN apt update && \
#     echo "deb https://packages.sury.org/php/ $(lsb_release -sc) main" | tee /etc/apt/sources.list.d/sury-php.list && \
#     curl -L https://packages.sury.org/php/apt.gpg | apt-key add - && \
#     apt update && apt upgrade && \
#     apt search php8.0-zip && \
#     apt install -y git zip unzip php8.0-zip && \
#     rm -rf /var/lib/apt/lists/*

RUN curl -sS https://getcomposer.org/installer -o composer-setup.php
RUN php -r "if (hash_file('sha384', 'composer-setup.php') === '906a84df04cea2aa72f40b5f787e49f22d4c2f19492ac310e8cba5b96ac8b64115ac402c8cd292b8a03482574915d1a8') { echo 'Installer verified'; } else { echo 'Installer corrupt'; unlink('composer-setup.php'); } echo PHP_EOL;"
RUN php composer-setup.php
RUN php -r "unlink('composer-setup.php');"
RUN mv composer.phar /usr/bin/composer

COPY composer.json /www/
COPY composer.lock /www/
COPY phpunit.xml /www/
COPY artisan /www/

WORKDIR /www/

RUN composer update

COPY app /www/app
COPY bootstrap /www/bootstrap
COPY public /www/public
COPY storage /www/storage
COPY routes /www/routes

RUN ls -l /www/

RUN chown -R unit:unit /www/

COPY config.json /docker-entrypoint.d/

#ENV SOAP_URL=https://graphical.weather.gov/xml/SOAP_server/ndfdXMLserver.php?wsdl
ENV SOAP_URL=http://www.thomas-bayer.com/axis2/services/BLZService?wsdl

COPY entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

#RUN mkdir /var/lib/unit/certs/ && chown -R unit:unit /var/lib/unit/certs/

RUN useradd -ms /bin/bash nginx

RUN chown -R nginx:nginx /var/lib/unit/
RUN mkdir /var/run/unit/ && chown -R nginx:nginx /var/run/unit/
RUN mkdir /var/log/unit/ && chown -R nginx:nginx /var/log/unit/

USER nginx:nginx

EXPOSE 8000

HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1