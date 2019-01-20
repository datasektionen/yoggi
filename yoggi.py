from os import getenv
from os.path import join, exists
from magic import from_buffer, from_file
from requests import get
from json import dumps
from mimetypes import types_map

from werkzeug.contrib.fixers import ProxyFix
from werkzeug.wrappers import Request, Response
from werkzeug.urls import url_decode, url_quote
from werkzeug.utils import redirect

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
        if not list_type is None:
            response.data = dumps(s3.list(request.path[1:]))

            return response

class AuthToken:
    def __init__(self):
        self.api_key = getenv('LOGIN_API_KEY')

    def any(self, request, response):
        token = response.params.get('token') or request.form.get('token')
        response.user = self.validate_user(token)

    def validate_user(self, token):
        url      = 'https://login2.datasektionen.se/verify/{}'.format(token)
        params   = {'format': 'json', 'api_key': self.api_key}
        response = get(url, params=params)

        if response.status_code == 200:
            return response.json()['user']
        else:
            return False

class PlsPermission:
    def any(self, request, response):
        response.permissions = self.has_permission(response.user)

    def has_permission(self, user):
        url = 'https://pls.datasektionen.se/api/user/{}/yoggi/'.format(user)
        res = get(url)

        return res.json()

class Static:
    def __init__(self, path):
        self.path = path

    def GET(self, request, response):
        if request.path.endswith('/'):
            if not response.user:
                url = 'https://login2.datasektionen.se/login?callback=' + url_quote(request.base_url) + '?token='
                return redirect(url)

            request.path = '/index.html'

        real_path = join(self.path, request.path[1:])
        if exists(real_path):
            response.response = open(real_path, 'r')
            response.mimetype = from_file(real_path)

            if response.user:
                response.set_cookie('user', response.user)
                response.set_cookie('permissions', ', '.join(response.permissions))

            return response

class S3Handler:
    def has_access(self, response, path):
        if not response.user:
            return False

        if '*' in response.permissions:
            return True

        path_items = path.split('/')
        folder = path_items[0] if len(path_items) > 1 else '~'

        if folder == '~':
            return True

        return folder in response.permissions

    def GET(self, request, response):
        url = s3.get_url(request.path[1:])

        if url:
            response = redirect(url)
            response.cache_control.max_age = 1800
        else:
            response.data = 'Cannot GET ' + request.path
            response.status_code = 404

        return response

    def POST(self, request, response):
        path = request.path[1:]
        folder = path.split('/')

        if self.has_access(response, path):

            file = request.files['file']

            mimetype = from_buffer(file.stream.read(1024), mime=True)

            s3.put(path, file, response.user, mimetype)

            response.data = 'That probably worked...'

        else:
            response.data = 'Permission denied in this folder.'
            response.status_code = 401

        return response

    def DELETE(self, request, response):
        path = request.path[1:]
        folder = path.split('/')

        if s3.owner(path) == response.user or self.has_access(response, path):
            s3.delete(path)
            response.data = 'That probably worked...'
        else:
            response.data = 'Not allowed'
            response.status_code = 401

        return response

middlewarez = [
    ParseQuery(),
    CORS(),
    ListFiles(),
    AuthToken(),
    PlsPermission(),
    Static('build'),
    S3Handler()
]

@Request.application
def request_handler(request):
    response = Response()

    for middleware in middlewarez:
        if 'any' in dir(middleware):
            finished_response = middleware.any(request, response)
        elif request.method in dir(middleware):
            finished_response = middleware.__getattribute__(request.method)(request, response)

        if finished_response: return finished_response
        elif finished_response is not None: response = finished_response

yoggi = ProxyFix(request_handler, num_proxies=2)

if __name__ == '__main__':
    from werkzeug.serving import run_simple

    run_simple('localhost', getenv('PORT') or 5000, request_handler, use_debugger=True, use_reloader=True)
