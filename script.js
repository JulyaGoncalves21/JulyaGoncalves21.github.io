const translations = {};

const getNested = (object, path) => path.split(".").reduce((value, key) => value?.[key], object);

async function loadLanguage(language) {
  if (!translations[language]) {
    const response = await fetch(`content/${language}.json`);
    if (!response.ok) throw new Error(`Unable to load ${language} content`);
    translations[language] = await response.json();
  }

  const copy = translations[language];
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const value = getNested(copy, element.dataset.i18n);
    if (typeof value === "string") element.textContent = value;
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((element) => {
    const value = getNested(copy, element.dataset.i18nAria);
    if (typeof value === "string") element.setAttribute("aria-label", value);
  });
  document.querySelectorAll("[data-i18n-alt]").forEach((element) => {
    const value = getNested(copy, element.dataset.i18nAlt);
    if (typeof value === "string") element.setAttribute("alt", value);
  });

  document.documentElement.lang = language === "pt" ? "pt-BR" : "en";
  document.querySelectorAll("[data-lang]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.lang === language));
  });
  localStorage.setItem("portfolio-language", language);
}

document.querySelectorAll("[data-lang]").forEach((button) => {
  button.addEventListener("click", () => loadLanguage(button.dataset.lang).catch(console.error));
});

const menuButton = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#site-nav");
menuButton.addEventListener("click", () => {
  const isOpen = menuButton.getAttribute("aria-expanded") === "true";
  menuButton.setAttribute("aria-expanded", String(!isOpen));
  navigation.classList.toggle("is-open", !isOpen);
});
navigation.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => {
  menuButton.setAttribute("aria-expanded", "false");
  navigation.classList.remove("is-open");
}));

document.querySelector("#year").textContent = new Date().getFullYear();

const preferredLanguage = new URLSearchParams(window.location.search).get("lang")
  || localStorage.getItem("portfolio-language");
if (preferredLanguage === "pt") loadLanguage("pt").catch(console.error);
