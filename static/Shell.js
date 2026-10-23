/* Shared app shell: sidebar with the 10-screen pipeline, identity, next/previous navigation. */
(function () {
  "use strict";
  var STAGES = { 1: "Stage 1 · Concept", 2: "Stage 2 · Screenplay" };
  var SCREENS = [
    { n: 1, stage: 1, live: true, url: "/", title: "Concept approval", short: "Is it worth a screenplay?",
      question: "Is this concept worth developing into a screenplay?" },
    { n: 2, stage: 2, live: true, url: "/screen2", title: "Overview & genre", short: "What does the script show?",
      question: "What does the completed screenplay show, and how is it classified?" },
    { n: 3, stage: 2, live: true, url: "/screen/3", title: "Scorecard", short: "Why this score?",
      question: "Why did the screenplay receive this score?",
      purpose: "Show the exact 16-dimension screenplay rubric with ratings, weights, calculated points and evidence.",
      needs: "A screenplay extracted on Screen 2.",
      panels: ["16 weighted dimensions, each rated 0-10", "Points calculated by the backend, never by the AI", "Evidence excerpt with episode and scene reference for every rating", "Incomplete ratings shown as incomplete, not zero", "AI assessment kept separate from any human override"] },
    { n: 4, stage: 2, live: true, url: "/screen/4", title: "Gates & meters", short: "Anything blocking approval?",
      question: "Are any mandatory checks unresolved, and where are the intensity levels strongest?",
      purpose: "Surface editorial and completeness checks that may block approval, plus the three intensity meters.",
      needs: "A screenplay extracted on Screen 2.",
      panels: ["Zero erotic scenes check with human resolution of each flag", "Originality and similarity review", "Script completeness (expected vs detected episodes)", "Human sign-off status", "Cringe, humiliation and high-romance meters, each out of 10", "5-6 high-romance moments linked to their source"] },
    { n: 5, stage: 2, live: true, url: "/screen/5", title: "Episode diagnostics", short: "Where does it lose momentum?",
      question: "Where does the series work, weaken, repeat itself or lose forward momentum?",
      purpose: "Analyse hooks, conflict progression, revelations, cliffhangers, continuity and payoff links for each episode.",
      needs: "Episodes extracted on Screen 2.",
      panels: ["Episode grid with completeness and missing-episode flags", "Opening hook and ending cliffhanger per episode", "Conflict progression and repeated beats", "Reveals and emotional shifts", "Continuity and setup/payoff links", "Rewrite tasks with priority, owner and status"] },
    { n: 6, stage: 2, live: true, url: "/screen/6", title: "Characters & emotion", short: "Are the characters compelling?",
      question: "Are the characters compelling, consistent and emotionally connected to the story engine?",
      purpose: "Provide a dedicated character-level analysis instead of a single scorecard dimension.",
      needs: "Episodes extracted on Screen 2.",
      panels: ["Character profiles: goals, motivation, fear, stakes, agency", "Character arcs and whether change is earned", "Relationship map with power balance and shifts", "Consistency checks across episodes", "Emotional beats linked to source evidence", "Casting requirements per role"] },
    { n: 7, stage: 2, live: true, url: "/screen/7", title: "Audience, title & world", short: "Who connects with it?",
      question: "Who might connect with the series, what emotional journey does it offer, and how distinct is its world?",
      purpose: "Assess audience hypotheses, mood progression, title marketability and setting distinctiveness.",
      needs: "A screenplay extracted on Screen 2.",
      panels: ["Primary and secondary audience segments with confidence", "Women 24-45 development lens", "Family suitability flags for human review", "Emotional journey across the series", "Title strength", "World-building and verified historical performance"] },
    { n: 8, stage: 2, live: true, url: "/screen/8", title: "Promo, season & casting", short: "What can we promote?",
      question: "What can be promoted, what is the sequel engine, and which candidates fit the role and positioning?",
      purpose: "Extract marketable assets, assess standalone vs Season 2 strategy and compare casting candidates.",
      needs: "A screenplay extracted on Screen 2 and a confirmed genre.",
      panels: ["4-5 promotional scenes with spoiler risk", "4-5 exact dialogue lines, verified against the source", "Standalone / Season 2 strategy", "Casting context and candidate comparison", "Human casting decision with audit record"] },
    { n: 9, stage: 2, live: true, url: "/screen/9", title: "Production & rewrite", short: "What will it take?",
      question: "What will production need, what should change first, and what improved between versions?",
      purpose: "Turn screenplay findings into transparent planning estimates and trackable development work.",
      needs: "Findings from Screens 3-6.",
      panels: ["Cast, roles and locations", "Scene count and complexity", "Shooting-day estimate with visible formula", "Prioritised rewrite plan", "Version comparison: what was fixed, what is new"] },
    { n: 10, stage: 2, live: true, url: "/screen/10", title: "Review & export", short: "Who decided, and why?",
      question: "Who approved or rejected the concept or screenplay, on what evidence, and what happens next?",
      purpose: "Record accountable creative decisions, overrides, version history, exports and post-launch learning.",
      needs: "Completed analysis from earlier screens.",
      panels: ["Concept and screenplay decisions with rationale", "Review checklist before final approval", "Overrides that keep the original AI output", "Full audit history", "PDF and JSON export", "Post-launch performance learning"] }
  ];

  var path = location.pathname.replace(/\/+$/, "") || "/";
  var current = null, m;
  if (path === "/") current = 1;
  else if (path === "/screen2") current = 2;
  else if ((m = path.match(/^\/screen\/(\d+)$/))) current = +m[1];

  var LOGO = '<svg viewBox="0 0 32 34" width="30" height="32" aria-hidden="true"><rect x="8" y="2" width="16" height="24" rx="4" fill="#8B7CFF"/><path d="M14 10l7 4.5-7 4.5z" fill="#14152E"/><path d="M11.5 27l4.5 6 4.5-6z" fill="#F2A93B"/></svg>';
  var CHEV = '<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3L5 8l5 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var MENU = '<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><path d="M2 4h14M2 9h14M2 14h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';

  function item(s) {
    var cls = (s.live ? "live" : "soon") + (s.n === current ? " current" : "");
    return '<li><a class="nav-item ' + cls + '" href="' + s.url + '" title="Screen ' + s.n + ': ' + s.title + '"' +
      (s.n === current ? ' aria-current="page"' : "") + '><span class="node">' + s.n + '</span>' +
      '<span class="nav-text"><span class="nav-title">' + s.title + '</span><span class="nav-sub">' +
      (s.live ? s.short : "Coming soon") + '</span></span>' + (s.live ? "" : '<span class="tag-soon">Soon</span>') + '</a></li>';
  }
  var nav = [1, 2].map(function (st) {
    return '<div class="stage">' + STAGES[st] + '</div><ol>' + SCREENS.filter(function (s) { return s.stage === st; }).map(item).join("") + '</ol>';
  }).join("");

  var html =
    '<header class="topbar"><button class="icon-btn" id="side-open" aria-label="Open navigation" aria-controls="side">' + MENU + '</button>' +
    '<b>Rocket Reels</b><span class="where">' + (current ? "Screen " + current + " of 10" : "") + '</span></header>' +
    '<aside class="side" id="side" aria-label="Script Analyzer navigation">' +
      '<div class="side-top"><a class="brand" href="/">' + LOGO + '<span class="brand-text"><b>Rocket Reels</b><small>Script Analyzer</small></span></a>' +
      '<button class="icon-btn" id="side-collapse" aria-label="Collapse sidebar" aria-pressed="false">' + CHEV + '</button></div>' +
      '<nav class="rail" aria-label="Analysis pipeline">' + nav + '</nav>' +
      '<div class="side-user"><span class="avatar" id="avatar" aria-hidden="true">?</span>' +
        '<div class="user-fields"><label class="sr-only" for="uname">Your name</label><input id="uname" placeholder="Your name" autocomplete="off">' +
        '<label class="sr-only" for="urole">Your role</label><select id="urole"><option>writer</option><option>director</option><option>producer</option><option>owner</option></select></div></div>' +
    '</aside><div class="scrim" id="scrim"></div>';

  var body = document.body;
  body.classList.add("has-shell");
  if (localStorage.getItem("rr_side") === "collapsed") body.classList.add("side-collapsed");
  body.insertAdjacentHTML("afterbegin", html);

  var un = document.getElementById("uname"), ur = document.getElementById("urole"), av = document.getElementById("avatar");
  un.value = localStorage.getItem("rr_name") || "";
  ur.value = localStorage.getItem("rr_role") || "writer";
  function initials() { av.textContent = (un.value.trim().split(/\s+/).map(function (w) { return w[0]; }).slice(0, 2).join("") || "?").toUpperCase(); }
  initials();
  un.addEventListener("input", initials);
  un.addEventListener("change", function () { localStorage.setItem("rr_name", un.value); });
  ur.addEventListener("change", function () { localStorage.setItem("rr_role", ur.value); });

  var col = document.getElementById("side-collapse");
  function syncCollapse() { var c = body.classList.contains("side-collapsed"); col.setAttribute("aria-pressed", c); col.setAttribute("aria-label", c ? "Expand sidebar" : "Collapse sidebar"); }
  syncCollapse();
  col.addEventListener("click", function () {
    body.classList.toggle("side-collapsed");
    localStorage.setItem("rr_side", body.classList.contains("side-collapsed") ? "collapsed" : "open");
    syncCollapse();
  });
  function drawer(open) { body.classList.toggle("drawer-open", open); }
  document.getElementById("side-open").addEventListener("click", function () { drawer(true); });
  document.getElementById("scrim").addEventListener("click", function () { drawer(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") drawer(false); });

  document.addEventListener("DOMContentLoaded", function () {
    var prev = SCREENS[current - 2], next = SCREENS[current];
    var ticks = document.getElementById("ticks");
    if (ticks && current) {
      ticks.setAttribute("role", "img"); ticks.setAttribute("aria-label", "Screen " + current + " of 10");
      ticks.innerHTML = SCREENS.map(function (s) { return '<i class="' + (s.n < current ? "on" : s.n === current ? "cur" : "") + '"></i>'; }).join("");
    }
    var act = document.getElementById("head-actions");
    if (act && next) act.innerHTML = '<a class="btn amber" href="' + next.url + '">Next: Screen ' + next.n + ' · ' + next.title + ' &rarr;</a>';
    var main = document.querySelector(".shell-main");
    if (main && current) {
      main.insertAdjacentHTML("beforeend", '<nav class="pager" aria-label="Screen navigation">' +
        (prev ? '<a class="prev" href="' + prev.url + '"><small>&larr; Previous</small><strong>Screen ' + prev.n + ' · ' + prev.title + '</strong></a>' : '<span class="spacer"></span>') +
        (next ? '<a class="next" href="' + next.url + '"><small>Next &rarr;</small><strong>Screen ' + next.n + ' · ' + next.title + '</strong></a>' : "") + '</nav>');
    }
  });

  window.Shell = { SCREENS: SCREENS, current: current };
})();