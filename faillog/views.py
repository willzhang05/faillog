from flask import request, render_template, Response
from faillog import app
from faillog.database import db_session
from faillog.models import Address

import re
import json
import requests

API_URL = 'http://geoip.nekudo.com/api/'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api')
def api():
    limit = request.args.get('limit')
    max_len = 10000
    if limit:
        try:
            max_len = int(limit)
        except:
            return render_template('error.html'), 400

    addresses = []
    with open('./sshd.json', 'r') as f:
        lines = 0
        for line in f:
            line_split = re.split('(\{.*?\})(?= *\{)', line.rstrip())
            objects = [o for o in line_split if not re.match(r'\s', o)]
#            print(len(objects))
#            print(objects)
            for o in objects:
                if o != '':
                    if lines < max_len:
                        data = json.loads(o)
                        found = re.findall(
                            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', data['MESSAGE'])
                        if found:
                            addresses.append(''.join(found))
                            lines += 1

    out = []
    for ip in addresses:
        result = Address.query.filter(Address.ip == ip)
        if result.count() != 0:
            new_dict = dict()
            new_dict[ip] = result.first().data
            out.append(new_dict)
        else:
            r = requests.get(API_URL + ip)
            if r.status_code == 200:
                response = r.json()
                new_dict = dict()
                new_dict[ip] = response
                out.append(new_dict)
                a = Address(ip, response)
                db_session.add(a)
                db_session.commit()
#                print(ip, response)
    return Response(json.dumps(out), mimetype='application/json')
