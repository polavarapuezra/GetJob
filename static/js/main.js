// Skill chip counter
(function () {
  const checkboxes = document.querySelectorAll(".skill-checkbox");
  const countEl = document.getElementById("selectedCount");
  if (!checkboxes.length || !countEl) return;
  function updateCount() {
    const n = document.querySelectorAll(".skill-checkbox:checked").length;
    countEl.textContent = n + " skill" + (n !== 1 ? "s" : "") + " selected";
  }
  checkboxes.forEach((cb) => cb.addEventListener("change", updateCount));
  updateCount();
})();

// Open portal link in new tab before form submit
function openPortal(url) {
  if (url && url !== "#") {
    window.open(url, "_blank", "noopener,noreferrer");
  }
}

// Auto-dismiss flash alerts after 4 seconds
(function () {
  const alerts = document.querySelectorAll(".gj-alert");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 4000);
  });
})();
