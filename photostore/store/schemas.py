from photostore.store.models import PhotoCoverage, Photo
from photostore.modules.editorjs import renderBlock
from photostore.models.security import User
from photostore import ma
from marshmallow import fields, post_dump
from flask import json, current_app
from flask import render_template
from datetime import datetime


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User

    id = ma.auto_field()
    name = ma.auto_field()
    email = ma.auto_field()
    username = ma.auto_field()
    version = fields.Constant("User:v1")


class PhotoCoverageSchema(ma.SQLAlchemySchema):
    class Meta:
        model = PhotoCoverage
    id = ma.auto_field()
    headline = ma.auto_field()
    excerpt = ma.auto_field()
    credit_line = ma.auto_field()
    keywords = fields.List(fields.Str())
    photos = fields.List(fields.Str())


class PhotoCoverageExportSchema(ma.SQLAlchemySchema):
    class Meta:
        model = PhotoCoverage

    id = ma.auto_field()
    headline = ma.auto_field()
    excerpt = fields.Method('get_excerpt')
    keywords = fields.Method('get_keywords')
    credit_line = ma.auto_field()
    author = fields.Nested(UserSchema)
    photos = fields.List(
        fields.Nested(lambda: PhotoExportSchema(only=("md5",)))
    )
    version = fields.Constant("PhotoCoverage:v1")

    def get_excerpt(self, obj: PhotoCoverage):
        return json.loads(obj.excerpt)

    def get_keywords(self, obj: PhotoCoverage):
        return obj.keywords


class PhotoIndexSchema(ma.Schema):
    """Schema de la foto para indexar con Whoosh"""

    md5 = fields.Str()
    archive_on = fields.DateTime(format="%Y%m%d%H%M%S")
    taken_on = fields.DateTime(format="%Y%m%d%H%M%S")
    taken_by = fields.Str()
    archived = fields.Boolean()
    keywords = fields.List(fields.Str())
    credit_line = fields.Str()
    excerpt = fields.Str()
    headline = fields.Str()

    @post_dump
    def process_excerpt(self, data, many, **kwargs):
        field_data = json.loads(data.get('excerpt'))
        data['keywords'] = ",".join(data.get('keywords'))
        data['excerpt'] = render_template(
            'store/editorjs/photo_excerpt.txt',
            data=field_data,
            block_renderer=renderBlock)
        return data


class PhotoExportSchema(ma.SQLAlchemySchema):
    """Photo export schema"""
    class Meta:
        model = Photo

    # image related data
    md5 = ma.auto_field()
    image_width = ma.auto_field()
    image_height = ma.auto_field()
    fnumber = ma.auto_field()
    camera = ma.auto_field()
    focal = ma.auto_field()
    isovalue = ma.auto_field()
    software = ma.auto_field()
    exposuretime = ma.auto_field()
    # news related data
    headline = ma.auto_field()
    excerpt = fields.Method('get_excerpt')
    keywords = fields.Method('get_keywords')
    credit_line = ma.auto_field()
    taken_on = ma.auto_field()
    taken_by = ma.auto_field()
    uploader = fields.Nested(UserSchema)
    version = fields.Constant("Photo:v1")

    def get_excerpt(self, obj: Photo):
        return json.loads(obj.excerpt)

    def get_keywords(self, obj: Photo):
        return obj.keywords
