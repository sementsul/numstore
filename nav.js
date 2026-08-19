/* MagzGold — выдвижное меню (шторка). Лёгкий, на всех страницах. */
(function () {
  var b = document.getElementById("burger"),
      d = document.getElementById("drawer"),
      bg = document.getElementById("drawerBg");
  if (!b || !d || !bg) return;
  function open() { d.classList.add("open"); bg.classList.add("open"); document.body.style.overflow = "hidden"; }
  function close() { d.classList.remove("open"); bg.classList.remove("open"); document.body.style.overflow = ""; }
  b.addEventListener("click", open);
  bg.addEventListener("click", close);
  d.addEventListener("click", function (e) { if (e.target.closest(".drawer-close")) close(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
})();
