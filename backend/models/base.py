from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from backend.core.db.mysql import Base

class IBaseModel(Base):

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


    def to_dict(self) -> dict:
        result = {}
        for column in self.__table__.columns:
            result[column.name] = getattr(self, column.name)
        return result



