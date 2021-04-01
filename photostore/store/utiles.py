from photostore.modules.search import index_document, index_document_async
from adelacommon.ziparchive import ZipArchive
from photostore import filetools, db, celery
from photostore.store.models import Photo, PhotoCoverage, Volume
from photostore.store.schemas import PhotoIndexSchema, PhotoExportSchema
from photostore.store.schemas import PhotoCoverageExportSchema
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
from flask import current_app
from slugify import slugify
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
    current_app.logger.debug("Making tumbnail for {}".format(original))
    with Image.open(original) as im:
        im.thumbnail((360, 360), Image.ANTIALIAS)
        im.convert('RGB').save(destino, "JPEG", quality=60)


@celery.task
def makeThumbnailAsync(*args, **kwargs):
    makeThumbnail(*args, **kwargs)


@celery.task
def _makeWebRenditionAsync(photo_id: str, force=False):
    p = Photo.query.get(photo_id, force=force)
    StorageController.getInstance().makeWebRendition(
        p, force=force
    )

def makeWebRendition(photo_id: str, force=False):
    if current_app.config.get('CELERY_ENABLED'):
        # call async
        current_app.logger.debug(
            "Calling makeWebRendition Async")
        _makeWebRenditionAsync.delay(photo_id, force=force)
    else:
        # call directly
        p = Photo.query.get(photo_id)
        StorageController.getInstance().makeWebRendition(
            p, force=force
        )


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

    def makeWebRendition(self, photo: Photo, force=False) -> str:
        """Make a reb ready rendition of the photo"""
        _l = current_app.logger.debug
        # ensure path exits
        uploads_folder = os.path.join(
            current_app.config.get('UPLOAD_FOLDER'), 'images')
        Path(uploads_folder).mkdir(parents=True, exist_ok=True)
        # -- 
        _l("Web rendition for {}".format(photo.md5))
        # Is there a previous copy
        file_name = os.path.join(
            uploads_folder,
            "".join([photo.md5, Path(photo.fspath).suffix])
        )
        to_clean = file_name
        if Path(file_name).exists() and (force is False):
            _l("Web rendition already exists")
            return file_name
        else:
            # copy original photo to workdir
            with open(photo.fspath, mode="rb") as src:
                    with open(file_name, mode="wb") as dst:
                        shutil.copyfileobj(src, dst)
            # --
        
        with Image.open(file_name) as im:
            width, height = im.size
            mode = 'cuadrada'
            mode = 'vertical' if height > width else mode
            mode = 'horizontal' if width > height else mode
            escalar = False
            if im.format in ['JPEG', 'TIFF']:
                _l("Es JPEG/TIFF")
                _l("La imagen es {}".format(mode))
                if (mode in ['cuadrada', 'horizontal']) and (height > 1080):
                    nheight = 1080
                    hpercent = (nheight / float(height))
                    nwidth = int((float(width) * float(hpercent)))
                    escalar = True
                elif (mode == 'vertical') and (width > 900):
                    nwidth = 900
                    wpercent = (nwidth / float(width))
                    nheight = int((float(height) * float(wpercent)))
                    escalar = True
                else:
                    nwidth, nheight = (width, height)
                    _l("No necesita reescalado")

                if escalar is True:
                    _l("Nuevas dimensiones {}/{}".format(nwidth, nheight))
                    im.thumbnail((nwidth, nheight), resample=Image.BICUBIC)
                    _l("Sharpening")
                    out = im.filter(ImageFilter.SHARPEN)
                    if photo.taken_on:
                        text = "Editora Adelante © {}".format(
                            photo.taken_on.strftime("%Y")
                        )
                    else:
                        text = "Editora Adelante © {}".format(
                            photo.archive_on.strftime("%Y")
                        )
                    d = ImageDraw.Draw(out, "RGBA")
                    fnt = ImageFont.truetype(
                        current_app.config.get('WHATERMARK_FONT'), 18)
                    _l("Applying watermark")
                    d.text(
                        (20, nheight - 40), 
                        text,
                        fill=(255, 255, 255),
                        stroke_fill=(25, 25, 25),
                        stroke_width=2,
                        font=fnt)
                    _l("Saving {}".format(file_name))
                    out.save(
                        file_name, format='jpeg', dpi=(72, 72),
                        quality=95, optimize=True, progressive=True,
                        exif=im.info.get('exif'))
                else:
                    _l("No modifications needed. Is it an original?")
                    if photo.taken_on:
                        text = "Editora Adelante © {}".format(
                            photo.taken_on.strftime("%Y")
                        )
                    else:
                        text = "Editora Adelante © {}".format(
                            photo.archive_on.strftime("%Y")
                        )
                    d = ImageDraw.Draw(im, "RGBA")
                    fnt = ImageFont.truetype(
                        current_app.config.get('WHATERMARK_FONT'), 18)
                    _l("Applying watermark")
                    d.text(
                        (20, nheight - 40), 
                        text,
                        fill=(255, 255, 255),
                        stroke_fill=(25, 25, 25),
                        stroke_width=2,
                        font=fnt)
                    _l("Saving {}".format(file_name))
                    im.save(
                        file_name, format='jpeg', dpi=(72, 72),
                        optimize=True, progressive=True)
            else:
                _l("unsupported format")
                file_name = None

        if file_name is None:
            _l("Cleaning up unsupported format")
            os.remove(to_clean)
        return file_name

    def makePhotoZip(self, photo: Photo, web_ready=True) -> 'str':
        archive_name = os.path.join(
            tempfile.gettempdir(), photo.getExportName())
        work_dir = tempfile.TemporaryDirectory()
        foto_file_name = os.path.join(
            work_dir.name, "{}.{}".format(photo.md5, photo.extension))
        meta_file_name = os.path.join(
            work_dir.name, "META-INFO.json")

        if web_ready:
            web_rendition = self.makeWebRendition(photo)
            shutil.copy(web_rendition, foto_file_name)
        else:
            # copiar original
            shutil.copy(photo.fspath, foto_file_name)
        
        # dump de los metadatos de la foto
        with open(meta_file_name, 'w') as mf:
            json.dump(PhotoExportSchema().dump(photo), mf)

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
                makeWebRendition(photo.md5)
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

    def exportCoverage(self, cov: PhotoCoverage, web_ready=True):
        slug = slugify("{} {}".format(cov.headline, cov.id[-4:]))
        archive_name = os.path.join(
            tempfile.gettempdir(), "{}.zip".format(slug))
        work_dir = tempfile.TemporaryDirectory()
        photo_list = list()

        for p in cov.photos:
            # make the photo zip
            photo_archive = self.makePhotoZip(p, web_ready=web_ready)
            photo_list.append(shutil.move(photo_archive, work_dir.name))
            # photo_list.append(shutil.copy(p.thumbnail, work_dir.name))

        meta_file_name = os.path.join(
            work_dir.name, "META-INFO.json")

        # dump coverage metadata
        with open(meta_file_name, 'w') as mf:
            json.dump(PhotoCoverageExportSchema().dump(cov), mf)

        # ponerlo todo en un el archivo zip
        zip = ZipArchive(archive_name, 'w')
        for foto_file_name in photo_list:
            zip.addFile(foto_file_name, baseToRemove=work_dir.name)
        zip.addFile(meta_file_name, baseToRemove=work_dir.name)
        zip.close()

        # # limpiar directorio temporal
        work_dir.cleanup()
        return archive_name
