from fastapi import HTTPException

from .sql.base import SessionLocal


def nonestr(s):
    if s is None:
        return "None"
    return str(s)


def acked(err, msg):
    """
    Kafka production error callback. Used to raise HTTP 500 when message production fails.
    :param err: Kakfa error
    :param msg: Kafka error message
    :return: None
    """
    if err is not None:
        raise HTTPException(
            500, "Failed to deliver message: %s: %s" % (str(msg), str(err))
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
