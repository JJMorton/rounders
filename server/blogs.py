"""
Data models for blog posts in the database
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import warnings
from PIL import Image

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

import config

from . import db, app


class Attachment(db.Model):
    """A photo/picture attached to a blog post"""

    __tablename__ = "attachments"

    # Columns
    id:      Mapped[int] = mapped_column(primary_key=True, nullable=False)
    blog_id: Mapped[int] = mapped_column(ForeignKey('blogs.id'), nullable=True)
    name:    Mapped[str] = mapped_column(nullable=False)
    """Filename of this attachment"""

    # Relationships
    blog:  Mapped['Entry'] = relationship(back_populates='attachments')
    """The blog post to which this attachment belongs to"""

    @property
    def _filepath(self) -> Optional[Path]:
        """Path to the file on disk"""
        p = Path(app.config['ATTACHMENTS_FOLDER'], self.name)
        if not (p.resolve().is_relative_to(app.config['ATTACHMENTS_FOLDER'])):
            warnings.warn(f"File '{p.as_posix()}' not in attachment directory")
            return None
        return p

    @property
    def _thumbpath(self) -> Optional[Path]:
        if self._filepath is None:
            return None
        return Path(self._filepath.parent, 'thumb_' + self._filepath.name)

    def _create_thumb(self) -> None:
        """Generate a thumbnail for this attachment, if it doesn't exist"""
        if (not self._filepath) or self._thumbpath.exists():
            return
        im = Image.open(self._filepath)
        im.thumbnail((config.THUMB_SIZE, config.THUMB_SIZE))
        im.save(self._thumbpath.as_posix(), quality=95)
        print(f'Generated thumbnail for attachment {self.name}')

    def delete(self) -> None:
        if self._filepath:
            self._filepath.unlink(missing_ok=True)
            self._thumbpath.unlink(missing_ok=True)
            print(f'Deleted attachment {self.name}')

    @property
    def url(self) -> Optional[str]:
        """Relative URL of this attachment"""
        if not self._filepath:
            return None
        return self._filepath.relative_to(app.static_folder).as_posix()

    @property
    def thumb(self) -> Optional[str]:
        """Relative URL of the thumbnail"""
        if not self._filepath:
            return None
        self._create_thumb()
        return self._thumbpath.relative_to(app.static_folder).as_posix()


class Entry(db.Model):
    """A single blog post"""

    __tablename__ = "blogs"

    # Columns
    id:    Mapped[int] = mapped_column(primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    """Title of the blog"""
    text:  Mapped[Optional[str]] = mapped_column(nullable=True)
    """Text content of the blog"""
    date:  Mapped[int] = mapped_column(nullable=False)
    """Unix epoch representing the date of the blog"""

    # Relationships
    attachments: Mapped[list['Attachment']] = relationship(foreign_keys='Attachment.blog_id', back_populates='blog', lazy='dynamic')
    """Photos attached to this post"""
