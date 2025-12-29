(function ($) {
  $(function () {
    $("select.lucy-tag-select").each(function () {
      var $el = $(this);
      if ($el.data("lucy-select2")) {
        return;
      }
      $el.select2({
        tags: true,
        width: "style",
        placeholder: $el.attr("data-placeholder") || "Selecciona o escribe...",
      });
      $el.data("lucy-select2", true);
    });
  });
})(django.jQuery);
