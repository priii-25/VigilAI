// Background service worker for Chrome extension

chrome.runtime.onInstalled.addListener(() => {
  console.log('VigilAI Companion installed');
});

// Listen for messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'fetchBattlecard') {
    handleFetchBattlecard(request.domain)
      .then(sendResponse)
      .catch(error => sendResponse({ error: error.message }));
    return true; // Keep message channel open for async response
  }
});

async function handleFetchBattlecard(domain) {
  const API_URL = 'http://localhost:8000/api/v1';
  
  try {
    // Get stored token
    const result = await chrome.storage.local.get(['token']);
    const token = result.token;
    
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/competitors/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) throw new Error('Failed to fetch data');
    
    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: error.message };
  }
}
