(function () {
  if (window.Chart) {
    document.dispatchEvent(new CustomEvent("chartjs-ready"));
    return;
  }

  const script = document.createElement("script");
  script.src = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js";
  script.crossOrigin = "anonymous";
  script.onload = () => document.dispatchEvent(new CustomEvent("chartjs-ready"));
  document.head.appendChild(script);
})();
