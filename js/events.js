export function setupEventListeners() {
    const refreshBtn = document.querySelector('#btn-api-refresh');
    const addMediaBtn = document.querySelector('.btn-success');

    refreshBtn.addEventListener('click', () => {
        console.log('API Refresh gomb megnyomva!');
        // Később itt hívjuk a frissítő funkciókat
    });

    addMediaBtn.addEventListener('click', () => {
        const titleInput = document.querySelector('#new-titles').value;
        const typeSelect = document.querySelector('.new-media-select').value;
        console.log(`Hozzáadásra vár: ${titleInput}, típus: ${typeSelect}`);
    });
}