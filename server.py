from blogfetch import DB
from bottle import get, route, run, template, request
import urllib


g = DB()

@route('/')
def index():
    return 'GET /add/<url>'

@get('/add')
def add():
    url = request.query['url']
    output = g.add(url)
    json_result = '{"result": "success", "output":"{{output}}", "url": "{{url}}"}'
    return template(json_result, url=url, output = output)

@get('/send')
def send():
    g.send()

run(host='0.0.0.0', port=9002)
