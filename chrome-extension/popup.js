// Configuration
const API_URL = 'http://localhost:8000/api/v1';

// Get current tab URL and extract domain
async function getCurrentDomain() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.url) return null;
  
  try {
    const url = new URL(tab.url);
    return url.hostname.replace('www.', '');
  } catch {
    return null;
  }
}

// Fetch battlecard for domain
async function fetchBattlecard(domain) {
  try {
    const token = await getStoredToken();
    
    const response = await fetch(`${API_URL}/competitors/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) throw new Error('Failed to fetch competitors');
    
    const competitors = await response.json();
    const competitor = competitors.find(c => c.domain === domain);
    
    if (!competitor) return null;
    
    // Fetch battlecard for this competitor
    const battlecardResponse = await fetch(
      `${API_URL}/battlecards/competitor/${competitor.id}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (!battlecardResponse.ok) return null;
    
    return await battlecardResponse.json();
  } catch (error) {
    console.error('Error fetching battlecard:', error);
    return null;
  }
}

// Get stored auth token
async function getStoredToken() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['token'], (result) => {
      resolve(result.token || null);
    });
  });
}

// Display battlecard
function displayBattlecard(battlecard) {
  const container = document.getElementById('battlecard-container');
  
  const html = `
    <div class="card">
      <h3>${battlecard.title}</h3>
      <p>${battlecard.overview || 'No overview available'}</p>
    </div>
    
    ${battlecard.weaknesses && battlecard.weaknesses.length > 0 ? `
      <div class="card">
        <h3>Key Weaknesses</h3>
        ${battlecard.weaknesses.slice(0, 3).map(w => `<p>• ${w}</p>`).join('')}
      </div>
    ` : ''}
    
    ${battlecard.kill_points && battlecard.kill_points.length > 0 ? `
      <div class="card">
        <h3>Why We Win</h3>
        ${battlecard.kill_points.slice(0, 3).map(k => `<p>✓ ${k}</p>`).join('')}
      </div>
    ` : ''}
    
    <button class="btn" id="view-full">View Full Battlecard</button>
  `;
  
  container.innerHTML = html;
  container.style.display = 'block';
  
  document.getElementById('view-full').addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/battlecards' });
  });
}

// Initialize popup
async function init() {
  const loadingEl = document.getElementById('loading');
  const noDataEl = document.getElementById('no-data');
  
  const domain = await getCurrentDomain();
  
  if (!domain) {
    loadingEl.style.display = 'none';
    noDataEl.style.display = 'block';
    return;
  }
  
  const battlecard = await fetchBattlecard(domain);
  
  loadingEl.style.display = 'none';
  
  if (battlecard) {
    displayBattlecard(battlecard);
  } else {
    noDataEl.style.display = 'block';
  }
  
  document.getElementById('view-dashboard')?.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000' });
  });
}

// Run on load
document.addEventListener('DOMContentLoaded', init);
