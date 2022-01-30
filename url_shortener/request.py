from urllib.parse import unquote
import json
import re


class Request:
    """
    An incoming HTTP request.
    A higher level abstraction of the raw WSGI Environ dictionary.
    """

    def __init__(self, environ):
        self._method = environ["REQUEST_METHOD"]
        self._path = environ["PATH_INFO"]
        self._query_params = self.__parse_query_params(environ.get("QUERY_STRING", ""))
        self._headers = self.__parse_headers(environ)
        self._body = self.__parse_body(environ) if "CONTENT_TYPE" in environ else None
        self._wsgi_environ = environ

    @property
    def method(self):
        """
        the HTTP Method Type of this request
        """
        return self._method

    @property
    def path(self):
        """
        the path this request was made to
        """
        return self._path

    @property
    def query_params(self):
        """
        Request query parameters, represented as a dictionary of
        param name to param value
        """
        return self._query_params

    @property
    def headers(self):
        """
        Request headers, represented as a dictionary of
        header name to header value
        """
        return self._headers

    @property
    def body(self):
        """
        The Request Body
        """
        return self._body

    @property
    def wsgi_environ(self):
        """
        The raw WSGI Environment dictionary representation of the request
        """
        return self._wsgi_environ

    @staticmethod
    def __parse_query_params(query_string):
        param_list = query_string.split("&")
        params = {}
        for param in param_list:
            key_val = param.split("=")
            if len(key_val) == 2:
                params[key_val[0]] = key_val[1]
        return params

    @staticmethod
    def __parse_headers(environ):
        headers = {}

        if "CONTENT_TYPE" in environ:
            headers["content-type"] = environ["CONTENT_TYPE"]
        if "CONTENT_LENGTH" in environ:
            headers["content-length"] = environ["CONTENT_LENGTH"]

        env_header_re = re.compile(r"HTTP_(.+)")
        for key, val in environ.items():
            header = env_header_re.match(key)
            if header:
                headers[header.group(1).replace("_", "-").lower()] = val
        return headers

    def __parse_body(self, environ):
        res = {}
        body = environ["wsgi.input"].split("\r\n\r\n", 1)[1]
        if "multipart/form-data" in environ["CONTENT_TYPE"]:
            boundary = "--" + environ["CONTENT_TYPE"].split("boundary=")[1]
            for param in body.split(boundary):
                if param in ("--\n", "--\r\n", ""):
                    continue
                else:
                    param_info = param.split('\n')[1]
                    param_name = re.search('Content-Disposition: form-data; name="(.*?)"', param_info).group(1)
                    param_value = param.split(param_info + "\n")[1][1:-1]
                    res[param_name] = param_value.strip()
        elif "application/json" in environ["CONTENT_TYPE"]:
            res = json.loads(body)
        else:
            for param in body.split("&"):

                res[param.split("=")[0]] = unquote(param.split("=")[1])
        return res
