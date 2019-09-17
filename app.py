# -*-: coding: utf-8 -*-
import os
from flask import Flask, request, abort
import lightsail
import route53


def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    if 'FLASK_CONF' in os.environ:
        app.config.from_envvar('FLASK_CONF')
    return app


app = create_app()


@app.route('/', methods=['POST'])
def change():
    print(request.json)
    sesame = str(request.json.get("sesame", ""))
    if sesame != app.config['SESAME_OPENS']:
        abort(403)
    ok, new, old = lightsail.change_public_ip(
        app.config['INSTANCE_NAME'],
        app.config['IP_NAME_PREFIX'])
    if not ok:
        return 'failed'

    ok = route53.change_a_record_set(
        app.config['HOSTED_ZONE_ID'],
        app.config['RECORD_SET_NAME'],
        new)

    return 'ok' if ok else 'failed'


if __name__ == '__main__':
    app.run()