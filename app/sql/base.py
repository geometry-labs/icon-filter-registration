from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.settings import settings

SQLALCHEMY_DATABASE_URL = "postgresql://{user}:{password}@{server}:{port}/{db}".format(
    user=settings.db_user,
    password=settings.db_password,
    server=settings.db_server,
    port=settings.db_port,
    db=settings.db_database,
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
