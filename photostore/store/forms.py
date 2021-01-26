from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class SearchPhotosForm(FlaskForm):
    userquery = StringField('userquery')


class PhotoDetailsForm(FlaskForm):
    headline = StringField('Titular', validators=[DataRequired()])
    credit_line = StringField('Creditos', validators=[DataRequired()])
    excerpt = StringField('Caption', validators=[DataRequired()])
    tags = StringField('Keywords', validators=[DataRequired()])
