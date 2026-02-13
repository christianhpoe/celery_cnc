// Start dashboard-style polling on the workers page.
(function () {
  function init() {
    if (window.CeleryDashboardWorkers?.init) {
      window.CeleryDashboardWorkers.init(document);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
