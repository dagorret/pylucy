from django import forms


class CarrerasTagWidget(forms.SelectMultiple):
    """
    Renderiza un select múltiple con select2 en modo tags (usando assets del admin).
    Permite buscar y añadir, construyendo el array de carreras.
    """

    class Media:
        js = [
            "admin/js/vendor/select2/select2.full.js",
            "admin/js/jquery.init.js",
            "cursos/js/carreras_widget.js",
        ]
        css = {
            "all": ["admin/css/autocomplete.css"],
        }

    def __init__(self, *args, **kwargs):
        attrs = kwargs.pop("attrs", {})
        css_class = attrs.get("class", "")
        attrs["class"] = f"{css_class} lucy-tag-select".strip()
        attrs.setdefault("style", "width: 100%;")
        super().__init__(attrs=attrs, *args, **kwargs)
