// Settings page interactivity.
(function () {
  function initThemePicker() {
    const form = document.querySelector("[data-theme-form]");
    if (!form) {
      return;
    }
    const radios = Array.from(form.querySelectorAll("input[name='theme']"));
    if (!radios.length) {
      return;
    }

    const themeApi = window.CeleryTheme;
    const current = themeApi?.getTheme ? themeApi.getTheme() : null;
    if (current) {
      const selected = radios.find((radio) => radio.value === current);
      if (selected) {
        selected.checked = true;
      }
    }

    radios.forEach((radio) => {
      radio.addEventListener("change", () => {
        if (!radio.checked) {
          return;
        }
        if (themeApi?.setTheme) {
          themeApi.setTheme(radio.value);
          return;
        }
        localStorage.setItem("celery_cnc_theme", radio.value);
        document.documentElement.setAttribute("data-theme", radio.value);
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initThemePicker);
  } else {
    initThemePicker();
  }

  return;
})();
