const translations = new Map();
const supportedLanguages = new Set(["en", "pt"]);
const languageStatus = document.querySelector("#language-status");
const languageButtons = [...document.querySelectorAll("[data-lang]")];

const getNested = (object, path) => path
  .split(".")
  .reduce((value, key) => value?.[key], object);

const safeStorage = {
  get(key) {
    try { return window.localStorage.getItem(key); } catch { return null; }
  },
  set(key, value) {
    try { window.localStorage.setItem(key, value); } catch { /* Language still works without storage. */ }
  }
};

async function getLanguage(language) {
  if (translations.has(language)) return translations.get(language);
  const url = new URL(`content/${language}.json`, document.baseURI);
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`Unable to load ${language} content (${response.status})`);
  const copy = await response.json();
  translations.set(language, copy);
  return copy;
}

function applyLanguage(copy, language) {
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
  languageButtons.forEach((button) => {
    const isActive = button.dataset.lang === language;
    button.setAttribute("aria-pressed", String(isActive));
    button.setAttribute("aria-current", isActive ? "true" : "false");
  });
  languageStatus.textContent = copy.a11y.languageChanged;
  safeStorage.set("portfolio-language", language);

  const url = new URL(window.location.href);
  if (language === "pt") url.searchParams.set("lang", "pt");
  else url.searchParams.delete("lang");
  window.history.replaceState({}, "", url);
}

async function loadLanguage(language) {
  if (!supportedLanguages.has(language)) language = "en";
  languageButtons.forEach((button) => { button.disabled = true; });
  try {
    const copy = await getLanguage(language);
    applyLanguage(copy, language);
  } catch (error) {
    languageStatus.textContent = "Language content could not be loaded.";
    console.error(error);
  } finally {
    languageButtons.forEach((button) => { button.disabled = false; });
  }
}

languageButtons.forEach((button) => {
  button.addEventListener("click", () => loadLanguage(button.dataset.lang));
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

let dialogTrigger = null;
document.querySelectorAll("[data-dialog]").forEach((button) => {
  button.addEventListener("click", () => {
    const dialog = document.getElementById(button.dataset.dialog);
    if (!dialog) return;
    dialogTrigger = button;
    document.body.classList.add("dialog-open");
    dialog.showModal();
  });
});

document.querySelectorAll(".case-dialog").forEach((dialog) => {
  dialog.querySelector("[data-close-dialog]")?.addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
  dialog.addEventListener("close", () => {
    document.body.classList.remove("dialog-open");
    dialogTrigger?.focus();
    dialogTrigger = null;
  });
});

const requestedLanguage = new URLSearchParams(window.location.search).get("lang");
const storedLanguage = safeStorage.get("portfolio-language");
loadLanguage(supportedLanguages.has(requestedLanguage) ? requestedLanguage : storedLanguage || "en");
