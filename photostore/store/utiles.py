from photostore.modules.search import index_document, index_document_async
from photostore.modules.ziparchive import ZipArchive
from photostore import filetools, db, celery
from photostore.store.models import Photo, Volume
from photostore.store.schemas import PhotoIndexSchema, PhotoToEditorJSSchema
from PIL import Image
from PIL.ExifTags import TAGS
from flask import current_app
from pathlib import Path
import tempfile
import os
import shutil
import logging
import json


def getImageInfo(filename):
    """Read Image Exif Info

    retorna dict con las llaves:
    {
        ExifImageWidth: 0
        ExifImageHeight: 0
        DateTimeOriginal: '2020:12:15 14:45:17'
        DateTimeDigitized: '2020:12:15 14:45:17'
        FocalLength: 35.0
        FocalLengthIn35mmFilm: 52
        Make: 'NIKON CORPORATION'
        Model: 'NIKON D90'
        FNumber: 5.6
        XResolution: 72
        YResolution: 72
        ISOSpeedRatings: 400
        Software: GIMP X.Y.Z
        DateTime: '2020:12:16 13:29:30'
        Artist: 'Fulano de tal'
    }
    """
    ret = {}
    # -- reduce PIL logging
    pil_logger = logging.getLogger('PIL')
    pil_logger.setLevel(logging.ERROR)
    # --
    with Image.open(filename) as im:
        info = im._getexif()
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            ret[decoded] = value

    return ret


def makeThumbnail(original, destino):
    current_app.logger.debug("Haciendo tumbnail para {}".format(original))
    with Image.open(original) as im:
        im.thumbnail((360, 360), Image.ANTIALIAS)
        im.convert('RGB').save(destino, "JPEG", quality=60)


@celery.task
def makeThumbnailAsync(*args, **kwargs):
    makeThumbnail(*args, **kwargs)


class StorageController(object):

    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if StorageController.__instance is None:
            StorageController()
        return StorageController.__instance

    def __init__(self):
        if StorageController.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            StorageController.__instance = self

    def indexPhoto(self, photo: Photo):
        base = Path(current_app.config.get('INDEX_BASE_DIR'))
        s = PhotoIndexSchema()
        if current_app.config.get('CELERY_ENABLED'):
            index_document_async.delay(str(base / 'photos'), s.dump(photo))
        else:
            index_document(base / 'photos', s.dump(photo))

    def generateThumbnail(self, photo: Photo):
        # agregamos a la base de datos la información
        thumb_dst = os.path.join(
            current_app.config['UPLOAD_FOLDER'], 'thumb_{}{}'.format(
                photo.md5, '.jpg'))
        if current_app.config.get('CELERY_ENABLED'):
            makeThumbnailAsync.delay(photo.fspath, thumb_dst)
        else:
            makeThumbnail(photo.fspath, thumb_dst)
        photo.thumbnail = thumb_dst
        db.session.add(photo)
        db.session.commit()

    def makePhotoZip(self, photo: Photo) -> 'str':
        with tempfile.NamedTemporaryFile(delete=True) as f:
            archive_name = f.name

        work_dir = tempfile.TemporaryDirectory()
        foto_file_name = os.path.join(
            work_dir.name, "{}.{}".format(photo.md5, photo.extension))
        meta_file_name = os.path.join(
            work_dir.name, "META-{}-INFO.json".format(photo.md5))
        # copiar original
        shutil.copy(photo.fspath, foto_file_name)
        # dump de los metadatos de la foto
        with open(meta_file_name, 'w') as mf:
            json.dump(PhotoToEditorJSSchema().dump(photo), mf)

        # ponerlo todo en un el archivo zip
        zip = ZipArchive(archive_name, 'w')
        zip.addFile(foto_file_name, baseToRemove=work_dir.name)
        zip.addFile(meta_file_name, baseToRemove=work_dir.name)
        zip.close()

        # limpiar directorio temporal
        work_dir.cleanup()
        return archive_name

    def processPhoto(self, file_name, user_data):
        """Inteta procesar y almacenar en el archivo una foto

        retorna None en caso de que no se pueda almacenar la foto
        en caso contrario una instancia de Photo

        user_data son los datos recopilados del usuario a estos se intentara
        adicionar la información en el archivo de imagen
        """
        img_info = None
        _l = current_app.logger

        md5 = filetools.md5(file_name)
        _l.debug("File hash: {}".format(md5))
        photo = self.getPhotoByMD5(md5)
        if photo:
            # ya la tenia, este proceso no debe actualizar el archivo, esta
            # repetida
            _l.debug("Ya tenia esa foto")
            self.cleanUpFile(file_name)
            return photo

        _l.debug("Procesando nueva foto")
        try:
            img_info = getImageInfo(file_name)
        except IOError as e:
            _l.exception('Image file is not valid: {}'.format(file_name))
            self.cleanUpFile(file_name)
            return None
        except AttributeError:
            _l.debug('Image without ExifTags: {}'.format(file_name))

        bts = os.path.getsize(file_name)  # bytes to allocate
        vol = self.getVolumeFor(bts)
        if vol is not None:
            photo = vol.storePhoto(
                file_name, md5, user_data, bts, exif=img_info)
            self.cleanUpFile(file_name)
            if photo is not None:
                # make thumbnails and index for search
                self.generateThumbnail(photo)
                self.indexPhoto(photo)
            return photo

        _l.debug("No se encontro un volumen para almacenar la foto")
        self.cleanUpFile(file_name)
        return None

    def getVolumeFor(self, bts: int) -> Volume:
        """Find a volume where to store file_name"""
        return Volume.getStorageFor(bts)

    def getPhotoByMD5(self, md5: str) -> Photo:
        return Photo.query.get(md5)

    def cleanUpFile(self, file_name):
        try:
            os.remove(file_name)
        except Exception as e:
            current_app.logger.error(
                "Error cleaning up a file: {}".format(file_name))
        return
