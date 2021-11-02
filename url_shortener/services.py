import hashlib
import json
import sqlite3
from http import HTTPStatus

from pydantic import BaseModel, AnyHttpUrl, ValidationError
from sqlalchemy.exc import SQLAlchemyError

import settings
from db.model import Url
from db.database import Session, Url as Url_model
from response import Response


class UrlCheck(BaseModel):
    url: AnyHttpUrl


class MainPageService:
    def __init__(self, request):
        self.request = request

    def get(self):
        context = {
            "title": "Сокращатель ссылок 3000",
        }
        content_type = "application/json; charset=utf-8"
        return Response(HTTPStatus.OK, data=json.dumps(context, ensure_ascii=False), content_type=content_type)

    def post(self):
        try:
            req_url = UrlCheck.parse_obj(self.request.body)
            service = CreateShortUrlService(req_url.url)
            data = service.get_url_and_short_url()
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST, data="Введен некорректный URL")
        except Exception:
            data = {"Error": "INTERNAL_SERVER_ERROR"}
            return Response(HTTPStatus.INTERNAL_SERVER_ERROR, data=data)
        return Response(HTTPStatus.CREATED, data=data, content_type="application/json")


    def get_response(self):
        if self.request.method == "GET":
            return self.get()
        elif self.request.method == "POST":
            return self.post()


class HashMaker:
    def __init__(self, url):
        self.url = url

    def generate(self):
        return hashlib.sha256(self.url.encode()).hexdigest()[:10]


class CreateShortUrlService:
    def __init__(self, url):
        self.url = url

    def create_hash(self):
        hash_maker = HashMaker(self.url)
        hash_code = hash_maker.generate()
        return hash_code

    def create_short_url(self):
        return settings.SITE_URL + "/" + self.create_hash()

    def _save_url(self):
        url = Url_model(url=self.url, short_url=self.create_hash())
        with Session() as session:
            try:
                session.add(url)
                session.commit()
            except Exception as e:
                raise SQLAlchemyError()

        # url_db = Url()
        # url_db.create_item(url=self.url, short_url=self.create_hash())

    def get_url_and_short_url(self):
        self._save_url()
        result = {
            "url": self.url,
            "short_url": self.create_short_url(),
        }
        return json.dumps(result, ensure_ascii=False)


class RedirectService:
    def __init__(self, request, hash_url):
        self.request = request
        self.hash_url = hash_url

    def get(self):
        content_type = "application/json; charset=utf-8"
        url_db = Url()
        try:
            context = url_db.read_item(short_url=self.hash_url)
        except sqlite3.Error:
            return Response(HTTPStatus.NOT_FOUND)
        finally:
            url_db.connection.close()

        headers = {"Location": f"{context['url']}"}
        return Response(HTTPStatus.FOUND, headers=headers, data=context["url"], content_type=content_type)

    def get_response(self):
        if self.request.method == "GET":
            return self.get()


