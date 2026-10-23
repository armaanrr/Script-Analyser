/* Session-scoped persistence for completed screenplay analyses. */
(function () {
  "use strict";
  var PREFIX = "rr:analysis-session:v1:";
  var PROJECT_KEY = PREFIX + "selected-project";
  function key(screen, projectId) {
    return PREFIX + "screen:" + Number(screen) + ":project:" + String(projectId);
  }
  function rememberProject(projectId) {
    if (projectId !== undefined && projectId !== null && String(projectId).trim()) {
      sessionStorage.setItem(PROJECT_KEY, String(projectId));
    }
  }
  function getProject() { return sessionStorage.getItem(PROJECT_KEY) || ""; }
  function save(screen, projectId, data) {
    if (!projectId || !data || typeof data !== "object") return;
    try {
      sessionStorage.setItem(key(screen, projectId), JSON.stringify({ data: data, savedAt: new Date().toISOString() }));
      rememberProject(projectId);
    } catch (error) {
      console.warn("Could not retain analysis in this browser session.", error);
    }
  }
  function load(screen, projectId) {
    if (!projectId) return null;
    try {
      var raw = sessionStorage.getItem(key(screen, projectId));
      if (!raw) return null;
      var entry = JSON.parse(raw);
      return entry && entry.data && typeof entry.data === "object" ? entry.data : null;
    } catch (error) {
      console.warn("Could not restore Screen " + screen + " analysis.", error);
      return null;
    }
  }
  window.RRSessionResults = { save: save, load: load, rememberProject: rememberProject, getProject: getProject };
})();