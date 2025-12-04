from django_select2.forms import Select2TagWidget


class CarrerasTagWidget(Select2TagWidget):
    """Widget Select2 en modo tags para cargar listas (carreras, modalidades, comisiones)."""

    def __init__(self, *args, **kwargs):
        attrs = kwargs.pop("attrs", {})
        attrs.setdefault("data-placeholder", "Selecciona o escribe carreras")
        attrs.setdefault("style", "width: 100%;")
        # Solo consolidar con Enter o coma; permitir espacios dentro del tag.
        attrs.setdefault("data-token-separators", "[',']")
        super().__init__(attrs=attrs, *args, **kwargs)
