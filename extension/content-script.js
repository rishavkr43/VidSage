(function() {
  // Store extension ID when script loads
  const EXTENSION_ID = chrome.runtime?.id || null;
  
  // Add VidSage button to YouTube video page
  function addVidSageButton() {
    // Check if we're on a video page
    const videoId = new URLSearchParams(window.location.search).get('v');
    if (!videoId) return;
    
    // Check if button already exists
    if (document.querySelector('#vidsage-button')) return;
    
    // Find the subscribe button area to place our button nearby
    const subscribeButton = document.querySelector('#subscribe-button');
    if (!subscribeButton) return;
    
    // Create VidSage button
    const button = document.createElement('button');
    button.id = 'vidsage-button';
    button.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
      </svg>
      Chat with Video
    `;
    
    // Style the button
    button.style.cssText = `
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      margin-left: 12px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 20px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.3s ease;
      box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    `;
    
    // Add hover effect
    button.addEventListener('mouseenter', () => {
      button.style.transform = 'translateY(-1px)';
      button.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
    });
    
    button.addEventListener('mouseleave', () => {
      button.style.transform = 'translateY(0)';
      button.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.3)';
    });
    
    // Add click handler with robust error handling
    button.addEventListener('click', async () => {
      console.log('VidSage button clicked for video:', videoId);
      
      // Method 1: Try to use chrome.runtime.sendMessage if available
      try {
        // Check if chrome.runtime is still valid
        if (chrome.runtime && chrome.runtime.id) {
          await new Promise((resolve, reject) => {
            chrome.runtime.sendMessage({
              action: 'openChatWithVideo',
              videoId: videoId
            }, (response) => {
              if (chrome.runtime.lastError) {
                console.log('Chrome runtime error:', chrome.runtime.lastError.message);
                reject(chrome.runtime.lastError);
              } else {
                console.log('Message sent successfully');
                resolve(response);
              }
            });
          });
          return; // Success, exit early
        }
      } catch (error) {
        console.log('Failed to send message, trying alternative method:', error);
      }
      
      // Method 2: Direct URL opening with stored extension ID
      openChatDirectly(videoId);
    });
    
    // Insert button next to subscribe button
    subscribeButton.parentNode.insertBefore(button, subscribeButton.nextSibling);
  }
  
  // Enhanced fallback function to open chat directly
  function openChatDirectly(videoId) {
    try {
      let chatUrl = null;
      
      // Method 1: Try to use chrome.runtime.getURL if still available
      if (chrome.runtime && chrome.runtime.id && chrome.runtime.getURL) {
        chatUrl = chrome.runtime.getURL('ui.html') + `?video_id=${videoId}`;
        console.log('Opening with chrome.runtime.getURL:', chatUrl);
      } 
      // Method 2: Use stored extension ID
      else if (EXTENSION_ID) {
        chatUrl = `chrome-extension://${EXTENSION_ID}/ui.html?video_id=${videoId}`;
        console.log('Opening with stored extension ID:', chatUrl);
      }
      // Method 3: Try to extract extension ID from the current script's URL
      else {
        // Get all script tags and find the one from our extension
        const scripts = document.querySelectorAll('script[src*="chrome-extension://"]');
        for (let script of scripts) {
          const match = script.src.match(/chrome-extension:\/\/([a-z0-9]+)\//i);
          if (match) {
            chatUrl = `chrome-extension://${match[1]}/ui.html?video_id=${videoId}`;
            console.log('Opening with extracted extension ID:', chatUrl);
            break;
          }
        }
      }
      
      if (chatUrl) {
        // Open in new tab
        window.open(chatUrl, '_blank');
        console.log('VidSage chat opened successfully');
      } else {
        // Last resort - show instructions
        console.error('Could not determine extension URL');
        alert(`VidSage: Unable to open chat interface. Please try:\n\n1. Refresh this YouTube page\n2. Click the VidSage extension icon in your browser toolbar\n\nVideo ID: ${videoId}`);
      }
      
    } catch (error) {
      console.error('Error opening VidSage chat:', error);
      alert(`VidSage: An error occurred. Please refresh the page and try again.\n\nVideo ID: ${videoId}`);
    }
  }
  
  // Function to check and reinject button if needed
  function checkAndReinjectButton() {
    const videoId = new URLSearchParams(window.location.search).get('v');
    if (videoId && !document.querySelector('#vidsage-button')) {
      setTimeout(addVidSageButton, 1000);
    }
  }
  
  // Run when page loads
  addVidSageButton();
  
  // Clean up any existing observers before creating new ones
  if (window.vidSageObserver) {
    window.vidSageObserver.disconnect();
  }
  
  // Run when navigation changes (YouTube is SPA)
  let currentUrl = location.href;
  const observer = new MutationObserver(() => {
    if (location.href !== currentUrl) {
      currentUrl = location.href;
      // Remove existing button first
      const existingButton = document.querySelector('#vidsage-button');
      if (existingButton) {
        existingButton.remove();
      }
      // Add new button after delay
      setTimeout(addVidSageButton, 1000);
    }
    
    // Also check periodically if button disappeared (can happen with dynamic content)
    checkAndReinjectButton();
  });
  
  // Store observer globally for cleanup
  window.vidSageObserver = observer;
  observer.observe(document.body, { subtree: true, childList: true });
  
  // Periodically check if extension context is still valid
  setInterval(() => {
    if (!chrome.runtime?.id) {
      console.log('Extension context lost - button will use fallback method');
    }
  }, 5000);
  
  // Log when script loads
  console.log('VidSage content script loaded. Extension ID:', EXTENSION_ID);
})();