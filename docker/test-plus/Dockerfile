############################################################
# Dockerfile to build Nginx Amplify Agent with N+ container
# Based on Ubuntu 14.04
############################################################

# Set the base image to Ubuntu
FROM ubuntu:14.04

# File Author / Maintainer
MAINTAINER Mike Belov

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections \
 && apt-get update \
 && apt-get install -y -q wget apt-transport-https

# Download certificate and key from the customer portal (https://cs.nginx.com)
# and copy to the build context
ADD nginx-repo.crt /etc/ssl/nginx/
ADD nginx-repo.key /etc/ssl/nginx/

# Get other files required for installation
RUN wget -q -O /etc/ssl/nginx/CA.crt https://cs.nginx.com/static/files/CA.crt \
 && wget -q -O - http://nginx.org/keys/nginx_signing.key | apt-key add - \
 && wget -q -O /etc/apt/apt.conf.d/90nginx https://cs.nginx.com/static/files/90nginx

# Install NGINX Plus and  basic applications
RUN printf "deb https://plus-pkgs.nginx.com/ubuntu `lsb_release -cs` nginx-plus\n" >/etc/apt/sources.list.d/nginx-plus.list \
 && apt-get update \
 && apt-get install -y nginx-plus \
 && apt-get install -y --fix-missing tar curl nano wget dialog net-tools build-essential \
 && cp /usr/sbin/nginx /usr/sbin/nginx2

# Install php-fpm and configure
RUN rm -rf /run \
 && mkdir /run \
 && apt-get update \
 && apt-get install -y php5-fpm \
 && mkdir /run/php/

# add fastcgi_params and php-fpm.conf for nginx
ADD fastcgi_params /etc/nginx/fastcgi_params
ADD php-fpm.conf /etc/nginx/conf.d/php-fpm.conf
# overwrite default www.conf for php5.0-fpm and add second one
ADD php-fpm-www.conf /etc/php5/fpm/pool.d/www.conf
ADD php-fpm-www2.conf /etc/php5/fpm/pool.d/www2.conf
# add test .php file to /var/www/php-fpm root
ADD test.php /var/www/php-fpm/test.php

# Install Python and Basic Python Tools
RUN apt-get update \
 && apt-get install -y python python-dev python-distribute \
 && wget --no-check-certificate https://bootstrap.pypa.io/ez_setup.py -O - | python \
 && easy_install pip \
 && easy_install supervisor

# Copy the application folder inside the container
ADD . /amplify

# Install agent requirements:
RUN pip install \
    crossplane==0.1.1 \
    flup==1.0.2 \
    gevent==1.1.0 \
    greenlet==0.4.12 \
    lockfile==0.11.0 \
    netaddr==0.7.18 \
    netifaces==0.10.4 \
    psutil==4.0.0 \
    python-daemon==2.0.6 \
    requests==2.12.4 \
    rstr==2.2.3 \
    scandir==1.5 \
    setproctitle==1.1.10 \
    ujson==1.33

# Install test requirements
RUN pip install \
    pytest \
    pytest-xdist \
    pyhamcrest \
    requests_mock

ENV AMPLIFY_ENVIRONMENT testing
ENV PYTHONPATH /amplify

# Set the default directory where CMD will execute
WORKDIR /amplify

# add config
ADD nginx.conf /etc/nginx/nginx.conf
ADD nginx2.conf /etc/nginx/nginx2.conf
ADD nginx_bad_status.conf /etc/nginx/nginx_bad_status.conf
ADD nginx_syslog.conf /etc/nginx/nginx_syslog.conf
ADD supervisord.conf /etc/supervisord.conf

# add ssl
ADD amplify-agent-test.crt /etc/nginx/certs.d/amplify-agent-test.crt
ADD amplify-agent-test.key /etc/nginx/certs.d/amplify-agent-test.key

CMD bash
