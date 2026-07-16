/*
 * Prefetch-on-hover: mempercepat perpindahan halaman tanpa mengubah cara
 * navigasi (tetap full page load, jadi semua <script> inline per halaman
 * tetap jalan seperti biasa).
 *
 * Cara kerja: saat kursor hover / touchstart di sebuah link internal,
 * browser diminta mengambil halaman tujuan lebih awal via
 * <link rel="prefetch">. Saat link benar-benar diklik, HTML-nya sudah ada
 * di cache browser sehingga navigasi terasa mendekati instan.
 *
 * Aman: hanya link GET internal biasa yang di-prefetch. Link yang mengubah
 * state (logout), link eksternal, download, anchor, dan yang menandai
 * dirinya no-prefetch akan dilewati.
 */
(function () {
  "use strict";

  // Hormati preferensi hemat data / koneksi lambat.
  var conn = navigator.connection;
  if (conn && (conn.saveData || /(2|3)g/.test(conn.effectiveType || ""))) {
    return;
  }

  var prefetched = new Set();

  // Pola path yang TIDAK boleh di-prefetch karena punya efek samping
  // (mengubah state di server meski diakses via GET).
  var DENY = [/\/logout/i];

  function sameOrigin(url) {
    return url.origin === window.location.origin;
  }

  function shouldPrefetch(a) {
    if (!a || !a.href) return false;
    if (a.dataset.noPrefetch !== undefined) return false; // opt-out manual
    if (a.target && a.target !== "_self") return false; // buka tab/window lain
    if (a.hasAttribute("download")) return false;

    var url;
    try {
      url = new URL(a.href, window.location.href);
    } catch (e) {
      return false;
    }

    if (!/^https?:$/.test(url.protocol)) return false; // mailto:, tel:, dst.
    if (!sameOrigin(url)) return false; // link eksternal
    if (url.pathname === window.location.pathname && url.search === window.location.search)
      return false; // halaman yang sama
    if (a.getAttribute("href").charAt(0) === "#") return false; // anchor
    if (DENY.some(function (re) { return re.test(url.pathname); })) return false;

    var key = url.pathname + url.search;
    if (prefetched.has(key)) return false;
    return key;
  }

  function prefetch(a) {
    var key = shouldPrefetch(a);
    if (!key) return;
    prefetched.add(key);

    var link = document.createElement("link");
    link.rel = "prefetch";
    link.href = a.href;
    link.as = "document";
    document.head.appendChild(link);
  }

  // Delegasi event di document supaya link yang dibuat dinamis pun tercakup.
  var timer = null;
  function onOver(e) {
    var a = e.target.closest ? e.target.closest("a") : null;
    if (!a) return;
    // Delay kecil: hindari prefetch saat kursor cuma numpang lewat.
    clearTimeout(timer);
    timer = setTimeout(function () { prefetch(a); }, 60);
  }
  function onOut() {
    clearTimeout(timer);
  }

  document.addEventListener("mouseover", onOver, { passive: true });
  document.addEventListener("mouseout", onOut, { passive: true });
  // Di perangkat sentuh, touchstart memberi ~100-200ms sebelum klik selesai.
  document.addEventListener("touchstart", function (e) {
    var a = e.target.closest ? e.target.closest("a") : null;
    if (a) prefetch(a);
  }, { passive: true });
})();
