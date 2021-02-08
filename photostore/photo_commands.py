"""Photos related operations"""
from photostore.store.models import Photo
from photostore.store import utiles
from flask import Blueprint, current_app
import click

photos_commands = Blueprint('photo-cli', __name__)

@photos_commands.cli.command('webrenditions')
@click.option(
    '--force', 
    is_flag=True,
    help='Force for all photos')
def make_web_renditions(force):
    """Prepare all photos for web rendition download"""
    stc = utiles.StorageController.getInstance()
    for p in Photo.query.all():
        click.echo(stc.makeWebRendition(p, force=force))

@photos_commands.cli.command('thumbnails')
def make_tumbnails():
    """Make thumbnails for all photos"""
    for p in Photo.query.all():
        utiles.StorageController.getInstance(
            ).generateThumbnail(p)
