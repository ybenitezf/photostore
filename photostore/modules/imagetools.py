from flask import current_app
from PIL import Image, ImageFilter


def checkImageSize(file_name):
    _l = current_app.logger.debug

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
                out.save(
                    file_name, format='jpeg', dpi=(72, 72),
                    quality=95, optimize=True, progressive=True,
                    exif=im.info.get('exif'))
                out.close()
        else:
            _l("formato soportado")
