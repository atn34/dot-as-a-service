from bottle import abort, get, post, route, request, response, template
from paste import httpserver
import base64
import bottle
import subprocess

img_max_age = '31536000'
page_max_age = '600'

output_to_mime = {
    'gif': 'image/gif',
    'jpg': 'image/jpg',
    'pdf': 'application/pdf',
    'png': 'image/png',
    'svg': 'image/svg+xml',
}


def render(encoded_dot, output):
    p = subprocess.Popen(['/usr/bin/dot', '-T' + output],
                         stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    return p.communicate(
        input=base64.urlsafe_b64decode(encoded_dot).decode('zlib'))[0]


@route('/o/<output>/<encoded_dot>')
def o(output, encoded_dot):
    if output not in output_to_mime:
        abort(404, output + " is not an available output type")
    response.content_type = output_to_mime[output]
    response.set_header('Cache-Control', 'public, max-age=' + img_max_age)
    return render(encoded_dot, output)


@get('/create')
def create():
    response.set_header('Cache-Control', 'public, max-age=' + page_max_age)
    return '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width">
    <title>Dot as a Service - create</title>
  </head>
  <body>
    <form method="POST" action="/create" id="dotform">
      <input type="submit" />
    </form>
    <textarea name="dot"
              form="dotform"
              rows="50"
              cols="50"
              placeholder="digraph G {Hello->World}"></textarea>
    <br/>
    <a href="http://mdaines.github.io/viz.js/">Online dot editor here</a>
  </body>
</html>
'''


@post('/create')
def create():
    dot = request.forms.get('dot')
    response.status = 303
    response.set_header(
        'Location', '/created/' +
        base64.urlsafe_b64encode(' '.join(dot.split()).encode('zlib')))

created_template = template('''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width">
    <title>Dot as a Service - created</title>
  </head>
  <body>
    <img src="/o/png/{encoded_dot}"/>
    <br/>
    % for output in outputs:
    <a href="/o/{{output}}/{encoded_dot}">{{output}} link</a>
    % end
  </body>
</html>
''', outputs=output_to_mime.keys())


@route('/created/<encoded_dot>')
def created(encoded_dot):
    response.set_header('Cache-Control', 'public, max-age=' + page_max_age)
    return created_template.format(encoded_dot=encoded_dot)


@route('/')
def home():
    response.set_header('Cache-Control', 'public, max-age=' + page_max_age)
    return '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width">
    <title>Dot as a Service</title>
  </head>
  <body>
    This is a service for creating links to rendered
    <a href="http://www.graphviz.org/">dot</a> diagrams.
    The dot source is gzipped and base64 encoded directly into the url, so this
    will only work for small dot diagrams. <a href="/create">Try it out!</a>
  </body>
</html>
'''


@route('/z/health')
def health():
    return 'OK'


application = bottle.default_app()
httpserver.serve(application, host='0.0.0.0', port=8080)
