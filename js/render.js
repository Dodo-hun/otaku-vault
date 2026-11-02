// General function for loading in a <select>
export function populateSelectOptions(selectElement, optionsList) {
    // Először kiürítjük, biztos ami biztos
    selectElement.innerHTML = ''; 
    optionsList.forEach(item => {
        const option = document.createElement("option");
        option.value = item;
        option.textContent = item;
        selectElement.appendChild(option);
    });
}

// A kártyák kirajzolása (később ide kerül a bonyolultabb HTML struktúra)
export function renderMediaCards(mediaArray) {
    const container = document.querySelector('#media-container');
    container.innerHTML = ''; // Előző kártyák törlése
    
    mediaArray.forEach(media => {
        const card = document.createElement('div');
        card.className = 'media-card';
        card.innerHTML = `
            <h3><a href="${media.url}">${media.title}</a></h3>
            <p>Type: ${media.type}</p>
            <p>Status: ${media.status}</p>
            <p>Total chapters: ${media.total_chapters}</p>
            <p>Read chapters: ${media.read_chapters}</p>
            <p>Plus info: ${media.plusz_info}</p>
            <button>+</button>
        `;
        container.appendChild(card);
    });
}