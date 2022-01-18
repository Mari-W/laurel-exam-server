FROM ubuntu:20.04

ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update -y && \
    apt-get install -y openssh-server python3 python3-pip libpq-dev libpcre3 libpcre3-dev git sudo

COPY sshd_config /etc/ssh/sshd_config

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app

ENV FLASK_APP=app.py
ENV AUTHLIB_INSECURE_TRANSPORT=1

RUN chown -R root:root /app && chmod -R 700 /app

COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod u+x /app/entrypoint.sh
RUN addgroup student

RUN service ssh start
ENTRYPOINT [ "./entrypoint.sh" ]