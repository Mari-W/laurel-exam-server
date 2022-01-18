#!/bin/bash
/usr/sbin/sshd -D -p 2222 &
uwsgi --http-socket 0.0.0.0:5003 --processes 16 --wsgi-file app.py  --callable app --log-master --enable-threads