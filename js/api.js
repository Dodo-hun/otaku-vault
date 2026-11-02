import { API_BASE } from './config.js';

export async function fetchAllMedia() {
    try {
        const response = await fetch(`${API_BASE}/media`);
        if (!response.ok) throw new Error("Hiba az adatok letöltésekor!");
        return await response.json();
    } catch (error) {
        console.error(error);
        return [];
    }
}

// Ide jönnek majd a többi API hívások (addMedia, bulkRefresh stb.)