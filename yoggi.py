from typing import *;
from os import getenv, listdir
from os.path import join
from magic import from_buffer, from_file
from requests import get
import json

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.wrappers import Request, Response
from werkzeug.utils import redirect

from authlib.oidc.core import CodeIDToken
from authlib.integrations.requests_client import OAuth2Session
from authlib.integrations.base_client.errors import OAuthError, MismatchingStateError
from authlib.oidc.discovery.models import OpenIDProviderMetadata
from authlib import jose

import jwt

import s3

def _get_env_var(var: str) -> str:
    value = getenv(var)
    if value is None:
        raise Exception(f"Env var '{var}' must be set")
    return value

class Settings:
    OIDC_ID = _get_env_var("OIDC_ID")
    OIDC_SECRET = _get_env_var("OIDC_SECRET")
    OIDC_PROVIDER = _get_env_var("OIDC_PROVIDER")
    REDIRECT_URL = _get_env_var("REDIRECT_URL")
    JWT_SECRET = _get_env_var("JWT_SECRET")

class AuthToken(TypedDict, total=True):
    """
    Contains the auth information of a logged in user.
    """
    
    kth_id: str
    permissions: list[str]
    """
    The Hive scopes this user has access to.
    """

class Auth:
    def __init__(self):
        response = get(f"{Settings.OIDC_PROVIDER}/.well-known/openid-configuration")
        self.metadata = OpenIDProviderMetadata(response.json())
        self.metadata.validate()
        
        response = get(cast(str, self.metadata["jwks_uri"]))
        self.jwk_keys = jose.JsonWebKey.import_key_set(response.json())

    def any(self, request: Request, response: Response):
        session = OAuth2Session(
            client_id=Settings.OIDC_ID,
            client_secret=Settings.OIDC_SECRET,
            redirect_uri=Settings.REDIRECT_URL,
            scope="openid permissions",
        )
        
        if request.args.get("code") is not None:
            # User returned from the sso login redirect.
            # The user should be redirected to / at the end.
            response = redirect("/")
            
            if (error := request.args.get("error")) is not None:
                description = request.args.get("error_description")
                raise OAuthError(error=error, description=description)
            
            try:
                state_data = cast(dict[str, str], jwt.decode(
                    request.cookies.get("state", ""),
                    Settings.JWT_SECRET,
                    algorithms=["HS256"],
                ))
                state = state_data["state"]
                
                if state != request.args.get("state"):
                    raise MismatchingStateError()
                
                token = session.fetch_token(
                    self.metadata["token_endpoint"],
                    authorization_response=request.url,
                )
                
                user_info = jose.jwt.decode(token["id_token"], self.jwk_keys, claims_cls=CodeIDToken)
                
                auth_token = AuthToken(
                    kth_id=cast(str, user_info["sub"]),
                    permissions=[
                        cast(str, perm['scope'])
                        for perm in user_info["permissions"]
                        if perm['id'] == 'access'
                    ],
                )
                
                auth_token_jwt = jwt.encode(dict(auth_token), Settings.JWT_SECRET, algorithm="HS256")
                response.set_cookie("token", auth_token_jwt)
                response.delete_cookie("state")
                
                # Redirect to "/", clearing auth query parameters.
                return response
            except jwt.InvalidTokenError:
                # Bad state token, restart process.
                logged_in = False
        elif token_jwt := request.cookies.get("token"):
            # User has already logged in.
            try:
                auth_token = AuthToken(**jwt.decode(token_jwt, Settings.JWT_SECRET, algorithms=["HS256"]))

                logged_in = True
                request.environ["kth_id"] = auth_token["kth_id"]
                request.environ["permissions"] = auth_token["permissions"]
            except jwt.InvalidTokenError:
                # Bad token, consider user not logged in.
                logged_in = False
        else:
            # User is not logged in.
            logged_in = False
        
        if not logged_in:
            url, state = session.create_authorization_url(self.metadata["authorization_endpoint"])
            
            state_data = {
                "state": state,
            }
            state_jwt = jwt.encode(state_data, Settings.JWT_SECRET, algorithm="HS256")
            
            response = redirect(url)
            response.set_cookie("state", state_jwt)
            
            return response
        
        return response

class ListFiles:
    def GET(self, request, response):
        list_type = request.args.get('list')
        if not list_type is None:
            response.data = json.dumps(s3.list(request.path[1:]))

            return response

class Static:
    def __init__(self, path):
        self.path = path
        self.files = listdir(path)

    def GET(self, request: Request, response: Response):
        if request.path.endswith('/'):
            request.path = '/index.html'

        filename = request.path[1:]
        if filename not in self.files:
            return None

        real_path = join(self.path, filename)
        response.response = open(real_path, 'rb')
        response.mimetype = from_file(real_path)
        
        if "kth_id" in request.environ:
            response.set_cookie('kth_id', request.environ["kth_id"])
            response.set_cookie('permissions', ', '.join(request.environ["permissions"]))

        return response

class S3Handler:
    def has_access(self, request: Request, path):
        if not "kth_id" in request.environ:
            return False

        if '*' in request.environ["permissions"]:
            return True

        path_items = path.split('/')
        folder = path_items[0] if len(path_items) > 1 else '~'

        if folder == '~':
            return True

        return folder in request.environ["permissions"]

    def GET(self, request: Request, response: Response):
        url = s3.get_url(request.path[1:])

        if url:
            response = redirect(url)
            response.cache_control.max_age = 1800
        else:
            response.data = 'Cannot GET ' + request.path
            response.status_code = 404

        return response

    def POST(self, request: Request, response: Response):
        path = request.path[1:]
        folder = path.split('/')

        if self.has_access(request, path):

            file = request.files['file']

            mimetype = from_buffer(file.stream.read(1024), mime=True)

            public = request.args.get('public') or "False"

            s3.put(path, file, request.environ["kth_id"], mimetype, public)

            response.data = 'That probably worked...'

        else:
            response.data = 'Permission denied in this folder.'
            response.status_code = 401

        return response

    def PUT(self, request: Request, response: Response):
        path = request.path[1:]
        state = request.args.get('public')

        if state != "True" and state != "False":
            response.data = 'Invalid mapping for "public". Should be "?public=True" or "?public=False"'
            response.status_code = 400
            return response

        if self.has_access(request, path):

            s3.put_permissions(path, state)
            response.data = 'That probably worked...'

        else:
            response.data = 'Permission denied in this folder.'
            response.status_code = 401

        return response


    def DELETE(self, request: Request, response: Response):
        path = request.path[1:]
        folder = path.split('/')

        if s3.owner(path) == request.environ["kth_id"] or self.has_access(request, path):
            s3.delete(path)
            response.data = 'That probably worked...'
        else:
            response.data = 'Not allowed'
            response.status_code = 401

        return response

middlewarez = [
    Auth(),
    ListFiles(),
    Static('build'),
    S3Handler()
]

supported_methods = set(["GET", "PUT", "POST", "DELETE"])

@Request.application
def request_handler(request: Request):
    response = Response()

    if request.method not in supported_methods:
        response.data = 'Method Not Allowed'
        response.status_code = 405
        return response

    for middleware in middlewarez:
        d = dir(middleware)
        if isinstance(middleware, Auth):
            finished_response = middleware.any(request, response)
        elif request.method in d:
            finished_response = middleware.__getattribute__(request.method)(request, response)
        else:
            # This branch didn't exist before, but the variable could be unset
            # in the type system without it. Anyway, this behaviour should be
            # fair fallback.
            finished_response = None
        
        if finished_response == None:
            continue
        elif finished_response.data == b'':
            response = finished_response
        else:
            return finished_response
    
    raise Exception("No middleware could generate response")

yoggi = ProxyFix(request_handler)

if __name__ == '__main__':
    from werkzeug.serving import run_simple

    run_simple('localhost', int(getenv('PORT') or 5000), request_handler, use_debugger=True, use_reloader=True)
