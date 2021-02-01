from photostore.store.models import Volume
from photostore.store import forms
from flask_diced import Diced
from flask import flash, redirect, render_template, current_app
from pathlib import Path

class VolumeCRUD(Diced):
    model = Volume
    create_form_class = forms.CreateVolumeForm
    edit_form_class = forms.EditVolumeForm
    delete_form_class = forms.DeleteVolumeForm
    exclude_views = ('detail')

    def create_view(self):
        """create view function"""
        form = self.create_form_class()
        if form.validate_on_submit():
            obj = self.model()
            form.populate_obj(obj)
            if obj.testPath() is False:
                # try to create the volume folder
                Path(obj.fspath).mkdir(parents=True, exist_ok=True)
                if obj.testPath() is False:
                    # This is a problem
                    current_app.logger.error(
                        "The volume directory can't be created"
                    )
            obj.save()
            message = self.create_flash_message
            if message is None:
                message = self.object_name + ' created'
            if message:
                flash(message)
            return redirect(self.create_redirect_url)
        context = self.create_view_context({self.create_form_name: form})
        return render_template(self.create_template, **context)

    def edit_view(self, pk):
        """edit view function

        :param pk:
            the primary key of the model to be edited.
        """
        obj = self.query_object(pk)
        form = self.edit_form_class(obj=obj)
        if form.validate_on_submit():
            form.populate_obj(obj)
            obj.save()
            message = self.edit_flash_message
            if message is None:
                message = self.object_name + ' updated'
            if message:
                flash(message)
            return redirect(self.edit_redirect_url)
        context = self.edit_view_context({
            self.edit_form_name: form,
            self.object_name: obj
        })
        return render_template(self.edit_template, **context)
