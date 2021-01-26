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

    if current_app.config.get('PHOTOSTORE_ENABLED'):
        from .store.whoosh_schemas import PhotoIndexSchema

        current_app.logger.debug("Creado indice para las fotos en {}".format(
            base / 'photos'
        ))
        photos_dir = base / 'photos'
        photos_dir.mkdir(parents=True, exist_ok=True)
        index.create_in(base / 'photos', PhotoIndexSchema)

@cmd.cli.command('reindex')
def reindex():
    """Indexar todos los objetos"""
    if current_app.config.get('PHOTOSTORE_ENABLED'):
        current_app.logger.debug("Indexando photos")
        from .store.models import Photo
        from .store.utiles import StorageController

        ctrl = StorageController.getInstance()
        for photo in Photo.query.all():
            ctrl.indexPhoto(photo)
