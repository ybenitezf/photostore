from photostore.permissions import admin_perm
from flask import Blueprint, render_template
from photostore.store.cruds import VolumeCRUD
from flask_menu import current_menu, register_menu

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/crud')
volume_bp = Blueprint('volume_bp', __name__, url_prefix='/crud/volume')

admin_decore = [admin_perm.require(http_exception=403)]
VolumeCRUD(
    create_decorators=admin_decore,
    index_decorators=admin_decore,
    edit_decorators=admin_decore,
).register(volume_bp)


@volume_bp.before_app_first_request
def setupMenus():
    # sidebar entries
    actions = current_menu.submenu("actions.admin")
    actions._text = "Administración"
    actions._endpoint = None
    actions._external_url = "#!"

@admin_bp.route("/", methods=['GET'])
@admin_perm.require(http_exception=403)
@register_menu(
    admin_bp, "actions.admin.models", "Modelos",
    visible_when=lambda: admin_perm.can())
def admin_view():
    return render_template("admin/admin_view.html")
