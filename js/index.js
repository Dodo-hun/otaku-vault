
import { MEDIA_TYPES, STATUS_TYPES } from './config.js';
import { fetchAllMedia } from './api.js';
import { populateSelectOptions, renderMediaCards } from './render.js';
import { setupEventListeners } from './events.js';

// Az alkalmazás inicializálása
async function initApp() {
    console.log("Otaku Vault indul...");

    // 1. Felület előkészítése (Selectek feltöltése)
    populateSelectOptions(document.querySelector('.new-media-select'), MEDIA_TYPES);
    populateSelectOptions(document.querySelector('.filter-select'), ["ALL"].concat(STATUS_TYPES));

    // 2. Eseményfigyelők (Gombok) bekapcsolása
    setupEventListeners();

    // 3. Adatok lekérése a Pythontól
    const data = await fetchAllMedia();
    // 4. Adatok kirajzolása
    renderMediaCards(data);
}

// Futtatás azonnal, amint betölt a fájl
initApp();
