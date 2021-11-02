from http import HTTPStatus


class Response:
    def __init__(self, status, reason=None, headers=None, data="", content_type=None, charset="utf8"):
        self.headers = headers or {}
        self.data = data
        self.reason = reason

        self.charset = charset
        if content_type and "Content-Type" in self.headers:
            raise ValueError(
                "'headers' must not contain 'Content-Type' when the "
                "'content_type' parameter is provided."
            )
        if "Content-Type" not in self.headers:
            if content_type is None:
                content_type = f"text/html; charset={self.charset}"
            self.headers.update({"Content-Type": content_type})

        if status is not None:
            try:
                self._status = int(status)
            except (ValueError, TypeError):
                raise TypeError('HTTP status code must be an integer.')

            if not 100 <= self._status <= 599:
                raise ValueError('HTTP status code must be an integer from 100 to 599.')

        if reason:
            self.reason = reason
        else:
            self.reason = HTTPStatus(self._status).phrase

    @property
    def status(self):
        return str(self._status) + " " + self.reason
