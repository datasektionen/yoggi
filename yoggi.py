from os import getenv, listdir
from os.path import join
from magic import from_buffer, from_file
from requests import get
from json import dumps
from mimetypes import types_map
import string
from urllib.parse import urlencode

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.wrappers import Request, Response
from werkzeug.utils import redirect

import s3

class Auth:
    def __init__(self):
        self.login_frontend_url = getenv('LOGIN_FRONTEND_URL', 'https://sso.datasektionen.se/legacyapi')
        self.login_api_url = getenv('LOGIN_API_URL', 'https://sso.datasektionen.se/legacyapi')
        self.api_key = getenv('LOGIN_API_KEY')
        self.token_alphabet = set(string.ascii_letters + string.digits + "-_")

    def any(self, request, response):
        login_url = self.login_frontend_url + '/login?' + urlencode({'callback': request.base_url + '?token='})
        token = request.cookies.get('token') or request.args.get('token') or request.form.get('token')
        if token == None or token == "":
            return redirect(login_url)
        response.user = self.validate_user(token)
        if not response.user:
            # The token might have been invalidated. Clear cookies.
            resp = redirect(login_url)
            resp.set_cookie('token', max_age=0) # max_age=0 unsets the cookie.
            return resp

        response.set_cookie('token', token, httponly=True, samesite='Lax')
        return response

    def validate_user(self, token):
        if not self.validate_token(token):
            return False

        url      = '{}/verify/{}'.format(self.login_api_url, token)
        params   = {'api_key': self.api_key}
        response = get(url, params=params)

        if response.status_code != 200:
            return False
        return response.json()['user']

    def validate_token(self, token):
        for letter in token:
            if letter not in self.token_alphabet:
                return False
        return True

class ListFiles:
    def GET(self, request, response):
        list_type = request.args.get('list')
        if not list_type is None:
            response.data = dumps(s3.list(request.path[1:]))

            return response

class HivePermission:
    def any(self, request, response):
        self.hive_url = getenv('HIVE_URL', 'https://hive.datasektionen.se/api/v1')
        self.hive_api_key = getenv('HIVE_API_KEY')
        response.permissions = self.has_permission(response.user)

    def has_permission(self, user):
        url = self.hive_url + '/user/{}/permissions'.format(user)
        headers = {"Authorization": "Bearer" + self.hive_api_key}
        res = get(url, headers=headers)

        permissions = []
        for perm in res:
            if perm['id'] == 'access':
                permissions.append(perm['scope'])

        return permissions


class Static:
    def __init__(self, path):
        self.path = path
        self.files = listdir(path)

    def GET(self, request, response):
        if request.path.endswith('/'):
            request.path = '/index.html'

        filename = request.path[1:]
        if filename not in self.files:
            return None

        real_path = join(self.path, filename)
        response.response = open(real_path, 'rb')
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

            public = request.args.get('public') or "False"

            s3.put(path, file, response.user, mimetype, public)

            response.data = 'That probably worked...'

        else:
            response.data = 'Permission denied in this folder.'
            response.status_code = 401

        return response

    def PUT(self, request, response):
        path = request.path[1:]
        state = request.args.get('public')

        if state != "True" and state != "False":
            response.data = 'Invalid mapping for "public". Should be "?public=True" or "?public=False"'
            response.status_code = 400
            return response

        if self.has_access(response, path):

            s3.put_permissions(path, state)
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
    Auth(),
    ListFiles(),
    HivePermission(),
    Static('build'),
    S3Handler()
]

supported_methods = set(["GET", "PUT", "POST", "DELETE"])

@Request.application
def request_handler(request):
    response = Response()

    if request.method not in supported_methods:
        response.data = 'Method Not Allowed'
        response.status_code = 405
        return response

    for middleware in middlewarez:
        d = dir(middleware)
        if 'any' in d:
            finished_response = middleware.any(request, response)
        elif request.method in d:
            finished_response = middleware.__getattribute__(request.method)(request, response)

        if finished_response == None:
            continue
        elif finished_response.data == b'':
            response = finished_response
        else:
            return finished_response


yoggi = ProxyFix(request_handler)

if __name__ == '__main__':
    from werkzeug.serving import run_simple

    run_simple('localhost', getenv('PORT') or 5000, request_handler, use_debugger=True, use_reloader=True)
