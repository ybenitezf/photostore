from photostore.store.whoosh_schemas import PhotoIndexSchema
from photostore.store.models import Photo
from photostore.store.utiles import StorageController
from whoosh import index
from flask import Blueprint, current_app
from pathlib import Path

cmd = Blueprint('index', __name__)

@cmd.cli.command('create')
def create():
    """Crea los indices de whoosh"""
    base = Path(current_app.config.get('INDEX_BASE_DIR'))
    base.mkdir(
        parents=True, exist_ok=True)

    current_app.logger.debug("Creado indice para las fotos en {}".format(
        base / 'photos'
    ))
    photos_dir = base / 'photos'
    photos_dir.mkdir(parents=True, exist_ok=True)
    index.create_in(base / 'photos', PhotoIndexSchema)

@cmd.cli.command('reindex')
def reindex():
    """Indexar todos los objetos"""
    current_app.logger.debug("Indexando photos")


    ctrl = StorageController.getInstance()
    for photo in Photo.query.all():
        ctrl.indexPhoto(photo)
