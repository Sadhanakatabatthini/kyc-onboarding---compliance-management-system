from datetime import datetime
from backend.extensions import db

class BaseModel(db.Model):
    __abstract__ = True

    def to_dict(self):
        d = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                d[column.name] = value.isoformat()
            else:
                d[column.name] = value
        return d
