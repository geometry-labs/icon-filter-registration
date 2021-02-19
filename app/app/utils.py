#  Copyright 2021 Geometry Labs, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

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
