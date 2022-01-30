from sqlalchemy import Column, Text, PrimaryKeyConstraint
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import settings

engine = create_engine(URL(**settings.DB), echo=True)

Base = declarative_base()


class Url(Base):
    __tablename__ = 'url'
    __table_args__ = (
        PrimaryKeyConstraint("url", "short_url"),
    )

    url = Column(Text, unique=True)
    short_url = Column(Text, unique=True)

    def __init__(self, url, short_url):
        self.url = url
        self.short_url = short_url

    def __repr__(self):
        return "<Url('%s', '%s')>" % (self.url, self.short_url)


# Создание таблицы
Base.metadata.create_all(engine)

# Создание сессии
Session = sessionmaker(engine)

