(() => {
  const flashes = document.querySelectorAll(".flash");
  if (!flashes.length) return;

  setTimeout(() => {
    flashes.forEach((el) => {
      el.style.transition = "opacity 300ms ease, transform 300ms ease";
      el.style.opacity = "0";
      el.style.transform = "translateY(-4px)";
      setTimeout(() => el.remove(), 350);
    });
  }, 3500);
})();

(() => {
  const menu = document.querySelector("[data-side-menu]");
  const overlay = document.querySelector("[data-side-overlay]");
  const openButton = document.querySelector("[data-side-open]");
  const closeButton = document.querySelector("[data-side-close]");

  if (!menu || !overlay || !openButton || !closeButton) return;

  function openMenu() {
    menu.classList.add("is-open");
    overlay.classList.add("is-open");
    menu.setAttribute("aria-hidden", "false");
  }

  function closeMenu() {
    menu.classList.remove("is-open");
    overlay.classList.remove("is-open");
    menu.setAttribute("aria-hidden", "true");
  }

  openButton.addEventListener("click", openMenu);
  closeButton.addEventListener("click", closeMenu);
  overlay.addEventListener("click", closeMenu);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMenu();
  });
})();

(() => {
  const backButton = document.querySelector("[data-back-button]");
  if (!backButton) return;

  backButton.addEventListener("click", () => {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }

    window.location.href = "/";
  });
})();
