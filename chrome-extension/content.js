// Content script - runs on all pages
// Can be used to detect competitor pages and show indicators

(function() {
  'use strict';
  
  // Initialize when page loads
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  function init() {
    // Check if current domain is a tracked competitor
    checkIfCompetitor();
  }
  
  async function checkIfCompetitor() {
    const domain = window.location.hostname.replace('www.', '');
    
    // Send message to background script
    chrome.runtime.sendMessage(
      { action: 'fetchBattlecard', domain },
      (response) => {
        if (response && response.data) {
          // Could show a subtle indicator that this is a tracked competitor
          showCompetitorIndicator();
        }
      }
    );
  }
  
  function showCompetitorIndicator() {
    // Create a small indicator in the corner
    const indicator = document.createElement('div');
    indicator.id = 'vigilai-indicator';
    indicator.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 50px;
      height: 50px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 50%;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      cursor: pointer;
      z-index: 999999;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: bold;
      font-size: 20px;
    `;
    indicator.textContent = 'V';
    indicator.title = 'Tracked Competitor - Click for Battlecard';
    
    indicator.addEventListener('click', () => {
      chrome.runtime.sendMessage({ action: 'openPopup' });
    });
    
    document.body.appendChild(indicator);
  }
})();
