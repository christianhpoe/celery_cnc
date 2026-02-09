(function () {
  if (window.cytoscape) {
    return;
  }

  const script = document.createElement("script");
  script.src = "https://cdn.jsdelivr.net/npm/cytoscape@3.3.1/dist/cytoscape.min.js";
  script.onload = () => {
    const event = new CustomEvent("cytoscape-ready");
    document.dispatchEvent(event);
  };
  document.head.appendChild(script);
})();
