from sqlalchemy.orm import DeclarativeBase,mapped_column,Mapped
from sqlalchemy import TEXT,INTEGER,ForeignKey,Index,DATETIME,UniqueConstraint
from datetime import datetime

class TimestampMixin:
    created_at:Mapped[datetime]=mapped_column(DATETIME,default=datetime.now,nullable=False)
    updated_at:Mapped[datetime]=mapped_column(DATETIME,default=datetime.now,nullable=False)

class BaseModel(DeclarativeBase):
    pass

class Folders(BaseModel):
    __tablename__ = "folders"
    id:Mapped[int]=mapped_column(INTEGER,primary_key=True,autoincrement=True)
    folder_path:Mapped[str]=mapped_column(TEXT,nullable=False,unique=True)
    name:Mapped[str]=mapped_column(TEXT,nullable=False)
    indicate:Mapped[str]=mapped_column(TEXT,nullable=False,unique=True)

class Images(TimestampMixin, BaseModel):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True
    )

    folder_id: Mapped[int] = mapped_column(
        INTEGER,
        ForeignKey(
            "folders.id",
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        nullable=False
    )

    path: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        unique=True
    )

    name: Mapped[str] = mapped_column(
        TEXT,
        nullable=False
    )

    extension: Mapped[str] = mapped_column(
        TEXT,
        nullable=False
    )

    thumbnail_path:Mapped[str]=mapped_column(
        TEXT,
        nullable=False,
    )

    __table_args__ = (
        Index("index_name", "name"),
        Index("index_folder_index", "folder_id"),
    )

class ImageFeatures(BaseModel):
    __tablename__ = "imagefeatures"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    model: Mapped[str] = mapped_column(
        TEXT,
        nullable=False
    )

    path: Mapped[str] = mapped_column(
        TEXT,
        ForeignKey(
            "images.path",
            onupdate="CASCADE",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    feature: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        unique=True
    )

    __table_args__ = (
        UniqueConstraint(
            "model",
            "path",
            name="model_path_unique"
        ),
    )