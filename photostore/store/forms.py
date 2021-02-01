from photostore.store.models import DEFAULT_VOL_SIZE, Volume
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from pathlib import Path

class SearchPhotosForm(FlaskForm):
    userquery = StringField('userquery')


class PhotoDetailsForm(FlaskForm):
    headline = StringField('Titular', validators=[DataRequired()])
    credit_line = StringField('Creditos', validators=[DataRequired()])
    excerpt = StringField('Caption', validators=[DataRequired()])
    tags = StringField('Keywords', validators=[DataRequired()])


def volume_path(
        model, column, 
        message="The volume directory don't exists or can't be created"):
    def volume_path_validator(form, field):
        fspath = Path(field.data)
        if fspath.is_absolute() is False:
            raise ValidationError("Must be absolute path")
        test_path = lambda a: a.exists() and a.is_dir()
        if test_path(fspath) is False:
            try:
                fspath.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValidationError(str(e))
            if test_path(fspath) is False:
                raise ValidationError(message)
    
    return volume_path_validator

class VolumeForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired()])
    capacity = IntegerField(
        'Capacidad', validators=[DataRequired()], 
        default=DEFAULT_VOL_SIZE)
    used = IntegerField('Used', validators=[], default=0)
    fspath = TextField(
        'Camino en el sistema',
        validators=[DataRequired(), volume_path(Volume, Volume.fspath)])
    is_full = BooleanField('¿Lleno?')

class CreateVolumeForm(VolumeForm):
    submit = SubmitField("Crear volumen")

class EditVolumeForm(VolumeForm):
    submit = SubmitField("Actualizar volumen")

class DeleteVolumeForm(FlaskForm):
    name = StringField('Nombre', render_kw={'readonly': True})
    fspath = StringField('Camino en el sistema', render_kw={'readonly': True})
    submit = SubmitField("Eliminar volumen")
