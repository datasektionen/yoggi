from os import getenv
from os.path import join, exists
from magic import from_buffer, from_file
from requests import get
from json import dumps

from werkzeug.wrappers import Request, Response
from werkzeug.urls import url_decode, url_quote

import s3


class ParseQuery:
    def any(self, request, response):
        response.params = url_decode(request.query_string)

class CORS:
    def any(serlf, request, response):
        response.headers.set('Access-Control-Allow-Origin', '*')

class ListFiles:
    def GET(self, request, response):
        list_type = response.params.get('list')
        if list_type:
            response.response = dumps(s3.list(request.path[1:], list_type))

            return True

class AuthToken:
    def __init__(self):
        self.api_key = getenv('LOGIN_API_KEY')

    def any(self, request, response):
        response.user = self.validate_user(response.params.get('token'))

    def validate_user(self, token):
        url      = 'https://login2.datasektionen.se/verify/{}'.format(token)
        params   = {'format': 'json', 'api_key': self.api_key}
        response = get(url, params=params)

        if response.status_code == 200:
            return response.json()['user']
        else:
            return False

class Static:
    def __init__(self, path='static'):
        self.path = path

    def GET(self, request, response):
        if request.path == '/':
            if not response.user:
                response.data = ''
                response.location = 'https://login2.datasektionen.se/login?callback=' + url_quote(request.base_url) + '?token='
                response.status_code = 302
                return True

            request.path = '/index.html'

        real_path = join(self.path, request.path[1:])
        if exists(real_path):
            response.response = open(real_path, 'r')
            response.mimetype = from_file(real_path)
            
            return True

class S3Handler:
    def GET(self, request, response):
        obj = s3.get(request.path[1:])

        if obj:
            response.response = obj['Body']._raw_stream
            response.mimetype = obj['ContentType']
        else:
            response.data = 'Not found'
            response.status_code = 404

        return True
    
    def POST(self, request, response):
        if response.user:
            path = request.path[1:]
    
            file = request.files['file']
    
            mimetype = from_buffer(file.stream.read(1024), mime=True)
    
            response.data = dumps(s3.put(path, file, response.user, mimetype))
        
        else:
            response.status_code = 401
            response.response = 'Not allowed'
        
        return True
    
    def DELETE(self, request, response):
        path = request.path[1:]
    
        if s3.owner(path) == response.user:
            response.data = dumps(s3.delete(path))
        else:
            response.data = 'Not allowed'
            response.status_code = 401

        return True

middlewarez = [
    ParseQuery(),
    CORS(),
    ListFiles(),
    AuthToken(),
    Static('build'),
    S3Handler()
]

@Request.application
def werk(request):
    response = Response()

    for middleware in middlewarez:
        if 'any' in dir(middleware):
            if middleware.any(request, response): break

        if request.method in dir(middleware):
            if middleware.__getattribute__(request.method)(request, response): break

    return response

if __name__ == '__main__':
    from werkzeug.serving import run_simple

    run_simple('localhost', getenv('PORT') or 5000, werk, use_debugger=True, use_reloader=True)
