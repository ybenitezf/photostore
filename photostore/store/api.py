from photostore import db, ma
from photostore.store.utiles import StorageController
from photostore.store.schemas import PhotoCoverageSchema
from photostore.store.models import Photo, PhotoCoverage
from photostore.store.permissions import DOWNLOAD_COVERAGE
from apifairy import arguments, body, response, other_responses
from flask_login import login_required, current_user
from flask import Blueprint, abort, jsonify


photostore_api = Blueprint(
    'photos_api', __name__, template_folder='templates')


class UpdateCovArhsSchema(ma.Schema):
    updatephotos =  ma.Boolean(missing=False)

@photostore_api.route('/v1/photocoverage/<id>', methods=['PUT'])
@login_required
@body(PhotoCoverageSchema)
@response(PhotoCoverageSchema)
@arguments(UpdateCovArhsSchema)
@other_responses({400: 'Invalid request.', 404: 'PhotoCoverage not found.'})
def update_coverage(data, query, id):
    """Actualizar los datos de la cobertura
    
    Las photos pasadas no se tendran en cuenta, puede dejarse esa lista
    vacia. Si quiere actualizar las fotos debe usarse en el endpoint 
    /.../photocoverage/photos/...
    """
    cov = PhotoCoverage.query.get_or_404(id)
    cov.credit_line = data.get('credit_line')
    tags = list(filter(None, data.get('keywords')))
    cov.keywords = [t.lower() for t in tags]
    cov.headline = data.get('headline')
    cov.excerpt = data.get('excerpt')
    db.session.add(cov)
    if query.get('updatephotos'):
        # actualizar cada una de las fotos con los nuevos
        # datos
        for p in cov.photos:
            p.credit_line = data.get('credit_line')
            p.keywords = [t.lower() for t in tags]
            p.headline = data.get('headline')
            p.excerpt = data.get('excerpt')
            db.session.add(p)
        
    db.session.commit()

    if query.get('updatephotos'):
        # mandar a actualizar tambien el indice para las
        # busquedas
        for p in cov.photos:
            StorageController.getInstance().indexPhoto(p)
    return cov

@photostore_api.route('/v1/photocoverage', methods=['POST'])
@login_required
@body(PhotoCoverageSchema)
@response(PhotoCoverageSchema)
@other_responses({400: 'Invalid request.', 404: 'Photo not found.'})
def create_coverage(data):
    """Crea una cobertura de fotos"""   
    pc = PhotoCoverage(
        headline=data.get('headline'),
        credit_line=data.get('credit_line'),
        excerpt=data.get('excerpt')
    )

    pc.author_id = current_user.id
    tags = list(filter(None, data.get('keywords')))
    pc.keywords = [t.lower() for t in tags]
    # agregar las fotos
    for p_id in data.get('photos'):
        photo = Photo.query.get_or_404(p_id)
        pc.photos.append(photo)
    db.session.add(pc)
    db.session.commit()
    current_user.getUserRole().addPermission(
        DOWNLOAD_COVERAGE, pc.id, 'cobertura')
    return pc

@photostore_api.route('/v1/photocoverage/<id>')
@response(PhotoCoverageSchema)
@other_responses({404: 'Coverage not found'})
def get_coverage(id):
    """Retorna cobertura de fotos"""
    return PhotoCoverage.query.get_or_404(id)


class PhotoListSchema(ma.Schema):
    photos = ma.List(ma.Str())

@photostore_api.route(
    '/v1/photocoverage/photos/<id_cov>', methods=['DELETE']
)
@login_required
@body(PhotoListSchema)
@other_responses({400: 'Invalid request.', 404: 'PhotoCoverage not found.'})
def detach_photo(photos_data, id_cov):
    """Quitar fotos de la cobertura"""
    cov = PhotoCoverage.query.get_or_404(id_cov)
    if photos_data.get("photos"):
        for p_id in photos_data.get("photos"):
            p = Photo.query.get_or_404(p_id)
            if p in cov.photos:
                cov.photos.remove(p)
            else:
                abort(
                    400, 
                    message="{} no pertenece a {}".format(p_id, id_cov)
                )
        db.session.add(cov)
        db.session.commit()
    else:
        abort(400, message="Invalid Request")

    return {'message': "OK"}, 200


@photostore_api.route(
    '/v1/photocoverage/photos/<id_cov>', methods=['POST']
)
@login_required
@body(PhotoListSchema)
@other_responses({400: 'Invalid request.', 404: 'PhotoCoverage not found.'})
def attach_photo(photos_data, id_cov):
    """Agrega fotos a la cobertura"""
    cov = PhotoCoverage.query.get_or_404(id_cov)
    if photos_data.get("photos"):
        for p_id in photos_data.get("photos"):
            p = Photo.query.get_or_404(p_id)
            cov.photos.append(p)
        db.session.add(cov)
        db.session.commit()
    else:
        abort(400, message="Invalid Request")

    return {'message': "OK"}, 200


@photostore_api.errorhandler(404)
def object_not_found(e):
    return jsonify(error=str(e)), 404
