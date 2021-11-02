from http import HTTPStatus
import re

from request import Request
from response import Response


class WSGIApp:
    """
    The base WSGI Application class.
    """

    def __init__(self):
        self._routes = []
        self._variable_re = re.compile("^<([a-zA-Z]+)>$")

    def __call__(self, environ, start_response):
        request = Request(environ)
        match = self._match_route(request.path, request.method.upper())

        if match:
            args, route = match
            response = route["func"](request, *args)
        else:
            response = Response(HTTPStatus.NOT_IMPLEMENTED)
        start_response(response.status, response.headers)
        return response.data

    def on_request(self, methods, rule, request_handler):
        """
        Register a Request Handler for a particular HTTP method and path.
        request_handler will be called whenever a matching HTTP request is received.
        request_handler should accept the following args:
            (Dict environ)
        :param list methods: the methods of the HTTP request to handle
        :param str rule: the path rule of the HTTP request
        :param func request_handler: the function to call
        """
        regex = "^"
        rule = rule.lstrip("^")
        rule_parts = rule.split("/")

        for part in rule_parts:
            var = self._variable_re.match(part)
            if var:
                regex += r"([a-zA-Z0-9_-]+)\/"
            else:
                regex += part + r"\/"

        regex += "?$"  # make last slash optional and that we only allow full matches
        self._routes.append(
            (re.compile(regex), {"methods": methods, "func": request_handler})
        )

    def route(self, rule, methods=None):
        if not methods:
            methods = ["GET"]

        def decorator(func):
            return self.on_request(methods, rule, func)
        return decorator

        # return lambda func: self.on_request(methods, rule, func)

    def _match_route(self, path, method):
        for matcher, route in self._routes:
            match = matcher.match(path)
            if match and method in route["methods"]:
                return match.groups(), route
        return None
