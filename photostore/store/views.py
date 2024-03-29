from photostore import filetools, db
from photostore.modules.editorjs import renderBlock
from photostore.permissions import admin_perm
from photostore.store.whoosh_schemas import PhotoIndexSchema
from photostore.store.forms import PhotoDetailsForm, SearchPhotosForm
from photostore.store.models import Photo, PhotoCoverage, PhotoPaginaBusqueda
from photostore.store.utiles import StorageController
from photostore.store.permissions import DownloadCoveragePermission
from photostore.store.permissions import EditPhotoPermission
from photostore.store.permissions import DownloadPhotoPermission
from photostore.store.permissions import EDIT_PHOTO, DOWNLOAD_PHOTO
from whoosh.filedb.filestore import FileStorage
from whoosh.qparser import QueryParser
from whoosh import sorting
from flask_login import login_required, current_user
from flask_breadcrumbs import register_breadcrumb, default_breadcrumb_root
from flask_menu import register_menu, current_menu
from flask import Blueprint, current_app, render_template, abort
from flask import request, json, send_file, request, url_for
from flask import stream_with_context
from flask import Response
from pathlib import Path
from werkzeug.utils import redirect, secure_filename
import os
import tempfile
import datetime


bp = Blueprint(
    'photos', __name__, template_folder='templates')
default_breadcrumb_root(bp, '.index')


def can_edit_cobertura(cob: PhotoCoverage):
    return (cob.author_id == current_user.id) or admin_perm.can()


@bp.context_processor
def bp_context():
    def can_download(id):
        """Can download original image"""
        return DownloadPhotoPermission(id=id).can()

    def can_download_coverage(id):
        return DownloadCoveragePermission(id).can()

    return {
        'can_download_photo': can_download,
        'can_download_coverage': can_download_coverage
    }


@bp.before_app_first_request
def setupMenus():
    navbar = current_menu.submenu("navbar.photostore")
    navbar._external_url = "#!"
    navbar._endpoint = None
    navbar._text = "NAVBAR"

    # mis actions
    actions = current_menu.submenu("actions.photostore")
    actions._text = "Fotos"
    actions._endpoint = None
    actions._external_url = "#!"


@bp.route('/photo/preview/<id>')
def photo_thumbnail(id):
    p = Photo.query.get_or_404(id)
    if Path(p.thumbnail).is_file() is False:
        # this is slow but ensure the thumbnail is there in the next load
        StorageController.getInstance().generateThumbnail(p)
        abort(404)
    return send_file(p.thumbnail)


@bp.route('/photo/download/archive/<id>')
@login_required
def photo_download(id):
    """Descargar el zip con la foto y la información de la foto"""
    web_ready = True if request.args.get('web') else False
    if DownloadPhotoPermission(id=id).can() is False and web_ready is False:
        abort(403)
    p = Photo.query.get_or_404(id)
    file_name = StorageController.getInstance().makePhotoZip(
        p, web_ready=web_ready)
    file_handle = open(file_name, 'rb')

    def stream_and_remove():
        yield from file_handle
        file_handle.close()
        os.remove(file_name)

    return Response(
        stream_with_context(stream_and_remove()),
        headers={
            'Content-Type': 'application/zip',
            'Content-Disposition': 'attachment; filename="{}"'.format(
                Path(file_name).name)
        }
    )


def view_photo_download_page_dlc(*args, **kwargs):
    id = request.view_args['id']
    return [
        {
            'text': 'Exportar',
            'url': url_for('.photo_download_page', id=id)
        }
    ]


@bp.route('/photo/download/<id>')
@register_breadcrumb(
    bp, '.index.photo_download_page', '',
    dynamic_list_constructor=view_photo_download_page_dlc)
@login_required
def photo_download_page(id):
    """Present page with export options"""
    photo = Photo.query.get_or_404(id)
    return render_template(
        'store/photo_download_page.html',
        foto=photo)


def view_photo_details_dlc(*args, **kwargs):
    id = request.view_args['id']
    return [
        {
            'text': 'Detalles',
            'url': url_for('.photo_details', id=id)
        }
    ]


@bp.route('/photo/details/<id>')
@register_breadcrumb(
    bp, '.index.photo_details.id', 'Detalles',
    dynamic_list_constructor=view_photo_details_dlc)
@login_required
def photo_details(id):
    p = Photo.query.get_or_404(id)
    can_edit = EditPhotoPermission(p.md5)
    return render_template(
        'store/photo_details.html', foto=p, can_edit=can_edit)


@bp.route('/photo/edit/<id>', methods=['GET', 'POST'])
@register_breadcrumb(bp, '.index.photo_edit.id', 'Editar datos de la foto')
def photo_edit(id):
    p = Photo.query.get_or_404(id)
    can_edit = EditPhotoPermission(p.md5)
    if can_edit is False:
        abort(403)

    form = PhotoDetailsForm()
    if form.validate_on_submit():
        p.headline = form.headline.data
        p.credit_line = form.credit_line.data
        p.excerpt = form.excerpt.data
        tags = list(filter(None, json.loads(form.tags.data)))
        p.keywords = [t.lower() for t in tags]
        db.session.add(p)
        db.session.commit()
        # reindexar la foto para que consten los cambios
        StorageController.getInstance().indexPhoto(p)
        return redirect(url_for('.photo_details', id=p.md5))

    return render_template(
        'store/photo_edit.html', foto=p, form=form)


@bp.route('/')
@register_breadcrumb(bp, '.index', 'Fotos')
@register_menu(bp, 'navbar.photostore.index', 'Fotos')
@register_menu(bp, 'actions.photostore.index', 'Galerias')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    form = SearchPhotosForm()
    coberturas = PhotoCoverage.query.order_by(
        PhotoCoverage.archive_on.desc()).paginate(page, per_page=4)

    return render_template(
        'store/index.html', coberturas=coberturas,
        form=form, can_edit=can_edit_cobertura)


def verCobertura_dlc(*args, **kwargs):
    id = request.view_args['id']
    cob = PhotoCoverage.query.get_or_404(id)
    return [
        {
            'text': cob.headline,
            'url': url_for('.verCobertura', id=cob.id)
        }
    ]


@bp.route('/ver/cobertura/<id>')
@register_breadcrumb(
    bp, '.index.verCobertura', '',
    dynamic_list_constructor=verCobertura_dlc)
def verCobertura(id):
    cobertura = PhotoCoverage.query.get_or_404(id)
    form = SearchPhotosForm()
    return render_template(
        "store/ver_cobertura.html",
        cobertura=cobertura,
        form=form,
        can_edit=can_edit_cobertura)


def view_editarCobertura_dlc(*args, **kwargs):
    id = request.view_args['id']
    cob = PhotoCoverage.query.get_or_404(id)
    return [
        {
            'text': 'Editar Cobertura',
            'url': url_for('.editarCobertura', id=cob.id)
        }
    ]


@bp.route('/editar/cobertura/<id>')
@register_breadcrumb(
    bp, '.index.editarCobertura', '',
    dynamic_list_constructor=view_editarCobertura_dlc)
@login_required
def editarCobertura(id):
    cobertura = PhotoCoverage.query.get_or_404(id)
    if can_edit_cobertura(cobertura) is False:
        abort(403)

    return render_template(
        'store/editar_cobertura.html', cobertura=cobertura)


@bp.route('/myphotos')
@register_breadcrumb(bp, '.index.mis_fotos', 'Mis fotos')
@register_menu(bp, 'actions.photostore.mis_fotos', 'Mis fotos')
@login_required
def mis_fotos():
    """Las fotos de este usuario"""
    page = request.args.get('page', 1, type=int)
    form = SearchPhotosForm()
    photos = Photo.query.filter_by(
        upload_by=current_user.id
    ).order_by(
        Photo.archive_on.desc()).paginate(page, per_page=12)
    return render_template(
        'store/mis_fotos.html', fotos=photos, search_form=form)


@bp.route('/search', methods=['GET', 'POST'])
@register_breadcrumb(bp, '.index.buscar_indice', 'Buscar')
@register_menu(
    bp, 'actions.photostore.buscar_indice', 'Buscar Fotos')
@login_required
def buscar_indice():
    form = SearchPhotosForm()
    userquery = request.args.get('userquery', "")
    try:
        page = int(request.args.get('page', '1'))
        page = page if page > 0 else 1
    except ValueError:
        page = 1

    if form.validate_on_submit():
        userquery = form.userquery.data

    # hacer la busqueda aqui
    base = Path(current_app.config.get('INDEX_BASE_DIR'))
    store = FileStorage(str(base / 'photos'))
    ix = store.open_index()
    qp = QueryParser("excerpt", PhotoIndexSchema())
    keywords_facet = sorting.FieldFacet("keywords", maptype=sorting.Count)
    taken_facet = sorting.DateRangeFacet(
        "taken_on",
        datetime.datetime(2002, 1, 1),
        datetime.datetime.now(),
        datetime.timedelta(days=30),
        maptype=sorting.Count
    )

    with ix.searcher() as s:
        results = PhotoPaginaBusqueda(s.search_page(
            qp.parse(userquery, debug=False), page, pagelen=9,
            groupedby={
                "keywords": keywords_facet,
                "taken_on": taken_facet,
            },
            sortedby="taken_on", reverse=True)
        )

        keywords_grp = dict()
        # extraer las agrupaciones por keywords de los resultados
        for k, v in results.groups(name="keywords").items():
            keywords_grp[k] = {
                "documents": v,
                "text": k,
                "link": url_for(
                    '.buscar_indice',
                    userquery='keywords:"{}" {}'.format(
                        k, userquery))
            }
        # --

        # extraer los rangos de fechas
        taken_grp = dict()
        for k, v in results.groups(name="taken_on").items():
            if k is not None:
                start, end = k  # es una tupla
                taken_grp[k] = {  # range name
                    "documents": v,  # cantidad de documentos
                    "start": start,
                    "end": end,
                    "link": url_for(
                        '.buscar_indice',
                        userquery='taken_on:[{} TO {}] {}'.format(
                            start.strftime("%Y%m%d"),
                            end.strftime("%Y%m%d"),
                            userquery
                        ))
                }
        # --

    return render_template(
        'store/search.html',
        form=form, results=results, keywords_grp=keywords_grp,
        taken_grp=taken_grp, userquery=userquery)


@bp.route('/upload-form')
@register_breadcrumb(bp, '.index.upload_coverture', 'Subir cobertura')
@register_menu(
    bp, 'actions.photostore.upload_coverture', 'Subir cobertura')
@login_required
def upload_coverture():
    return render_template('store/upload.html')


def view_download_coverture_dlc(*args, **kwargs):
    id = request.view_args['id']
    cob = PhotoCoverage.query.get_or_404(id)
    return [
        {
            'text': 'Exportar',
            'url': url_for('.download_coverture', id=cob.id)
        }
    ]


@bp.route('/exportar/cobertura/<id>')
@register_breadcrumb(
    bp, '.index.download_coverture', '',
    dynamic_list_constructor=view_download_coverture_dlc)
@login_required
def download_coverture(id):
    cobertura = PhotoCoverage.query.get_or_404(id)
    return render_template(
        'store/download_coverture.html', cobertura=cobertura)


@bp.route('/exportar/cobertura/archive/<id>')
@login_required
def download_coberture_archive(id):
    """Download the coverture .zip archive"""
    web_ready = True if request.args.get('web') else False

    if DownloadCoveragePermission(id=id).can() is False and web_ready is False:
        abort(403)

    cov = PhotoCoverage.query.get_or_404(id)
    file_name = StorageController.getInstance().exportCoverage(
        cov, web_ready=web_ready)
    file_handle = open(file_name, 'rb')

    def stream_and_remove():
        yield from file_handle
        file_handle.close()
        os.remove(file_name)

    return Response(
        stream_with_context(stream_and_remove()),
        headers={
            'Content-Type': 'application/zip',
            'Content-Disposition': 'attachment; filename="{}"'.format(
                Path(file_name).name)
        }
    )


@bp.route('/upload', methods=['POST'])
@login_required
def handle_upload():
    """Handle uploads of photos"""
    if 'image' not in request.files:
        current_app.logger.debug("not file send")
        abort(400)

    file = request.files.get('image')
    if file.filename == '':
        return {'message': 'Ivalid image'}, 400

    if filetools.allowed_file(file.filename):
        filename = secure_filename(file.filename)
        fullname = os.path.join(tempfile.mkdtemp(), filename)
        file.save(fullname)
        # Procesar la imagen aqui
        # --
        keywords = json.loads(request.form.get('keywords'))
        user_data = {
            'headline': request.form.get('headline'),
            'creditline': request.form.get('creditline'),
            'keywords': list(filter(None, keywords)),
            'excerpt': request.form.get('excerpt'),
            'uploader': current_user.id,
            'taken_by': request.form.get('takenby')
        }
        im = StorageController.getInstance().processPhoto(
            fullname, user_data)
        if im:
            # darle permiso de edición al usuario que sube la foto
            # para que pueda modificiar los datos
            # REVIEW: puede sobre escribir los permisos
            current_user.getUserRole().addPermission(
                EDIT_PHOTO, im.md5, 'foto')
            current_user.getUserRole().addPermission(
                DOWNLOAD_PHOTO, im.md5, 'foto')
            # retornar la información de la imagen procesada, sobre
            # todo el md5 o id de la imagen
            db.session.add(im)
            db.session.commit()
            return {'md5': im.md5}, 200
        else:
            return {"message": "Invalid image"}, 400

    return {"message": "Something went worng"}, 400


@bp.context_processor
def render_excerpt_to_html():
    def render_excerpt(in_data):
        data = json.loads(in_data)
        return render_template(
            'store/editorjs/photo_excerpt.html',
            data=data,
            block_renderer=renderBlock)

    return dict(render_excerpt=render_excerpt)
