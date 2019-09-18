# -*-: coding: utf-8 -*-
# Copyright 2019 Euclidr.  All rights reserved.
# Use of this source code is governed by a MIT style
# license that can be found in the LICENSE file.

import os
from datetime import datetime, timedelta
from flask import Flask, request, flash, redirect, abort,\
    render_template, url_for

import lightsail
import route53


def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    if 'FLASK_CONF' in os.environ:
        app.config.from_envvar('FLASK_CONF')
    return app


app = create_app()


def can_modify_now():
    '''restrict the interval between two modification is
    greater than half an hour
    '''
    if not os.path.isfile(app.config['RECORD_BASE_PATH'] +
                          'change_records.log'):
        return True
    line = ''
    with open(app.config['RECORD_BASE_PATH'] +
              'change_records.log') as f:
        for tmp in f:
            tmp = tmp.strip()
            line = tmp if tmp else line

    parts = line.split('\t')
    if len(parts) != 3:
        return True

    try:
        t = datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S')
        delta = datetime.now() - t
        min_delta = timedelta(seconds=1800)
        return delta > min_delta
    except Exception as e:
        app.logger.error('convert time error: {}'.format(e))
    return True


@app.route('/', methods=['POST'])
def sesame_opens():
    '''change lightsail's public ip'''
    # validate sesame code
    data = request.json or request.form
    if not data:
        abort(403)
    sesame = str(data.get('sesame', ''))
    if sesame != app.config['SESAME_OPENS']:
        abort(403)

    if not can_modify_now():
        flash('can not change record set now, try later', 'warn')
        return redirect(url_for('index'))

    ok, new, old = lightsail.change_public_ip(
        app.config['INSTANCE_NAME'],
        app.config['IP_NAME_PREFIX'])
    if not ok:
        flash('Change public IP failed!', 'error')
        return redirect(url_for('index'))

    ok = route53.change_a_record_set(
        app.config['HOSTED_ZONE_ID'],
        app.config['RECORD_SET_NAME'],
        new)

    if not ok:
        flash('Change record set failed!', 'error')
    else:
        flash('Ok! ip changed from {} to {}.'.format(
            old, new
        ), 'success')
        with open(app.config['RECORD_BASE_PATH'] +
                  'change_records.log', 'a') as f:
            f.write('{}\t{}\t{}\n'.format(
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                old,
                new
            ))

    return redirect(url_for('index'))


@app.route('/', methods=['GET'])
def index():
    '''show the form and recent change records
    '''
    records = []
    if not os.path.isfile(app.config['RECORD_BASE_PATH'] +
                          'change_records.log'):
        return render_template('index.html', records=records)

    with open(app.config['RECORD_BASE_PATH'] +
              'change_records.log') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 3:
                records.append(parts)

    records.reverse()
    records = records[:10]
    return render_template('index.html', records=records)


if __name__ == '__main__':
    app.run()
