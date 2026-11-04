/* Page analytics for all of paginadedicata.com: this file is the only place to change.
   Every page loads it with one line in <head>: <script src="/site.js" async></script>
   Turn it off: empty this file and keep it, so no page requests a missing script.
   Cookie consent, if it is decided later, goes here too.
   Tags: client and slug come from the address, /client/slug/. Never send a person's name.
   data-no-slug: the slug contains the person's name, send client only.
   data-no-tags: not a client page (404), send no tags. */
(function () {
  var ID = "z8dipucyb2";
  var me = document.currentScript;

  (function (c, l, a, r, i, t, y) {
    c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
    t = l.createElement(r); t.async = 1; t.src = "https://www.clarity.ms/tag/" + i;
    y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
  })(window, document, "clarity", "script", ID);

  if (!me || me.hasAttribute("data-no-tags")) return;
  var path = location.pathname.split("/").filter(Boolean);
  if (path[0]) window.clarity("set", "client", path[0]);
  if (path[1] && !me.hasAttribute("data-no-slug")) window.clarity("set", "slug", path[1]);
})();
