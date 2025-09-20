chrome.action.onClicked.addListener((tab) => {
  // Get video ID from current YouTube tab if available
  let videoId = null;
  
  if (tab.url && tab.url.includes('youtube.com/watch')) {
    const url = new URL(tab.url);
    videoId = url.searchParams.get('v');
  }
  
  // Create new tab with the chat interface
  const chatUrl = chrome.runtime.getURL('ui.html') + (videoId ? `?video_id=${videoId}` : '');
  
  chrome.tabs.create({
    url: chatUrl
  });
});

// Listen for messages from content script with enhanced error handling
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  try {
    if (request.action === 'openChatWithVideo') {
      const chatUrl = chrome.runtime.getURL('ui.html') + `?video_id=${request.videoId}`;
      
      chrome.tabs.create({
        url: chatUrl
      }, (tab) => {
        if (chrome.runtime.lastError) {
          console.error('Error creating tab:', chrome.runtime.lastError);
          sendResponse({ success: false, error: chrome.runtime.lastError.message });
        } else {
          console.log('Successfully opened VidSage chat for video:', request.videoId);
          sendResponse({ success: true, tabId: tab.id });
        }
      });
      
      // Return true to indicate we will respond asynchronously
      return true;
    }
  } catch (error) {
    console.error('Error in message listener:', error);
    sendResponse({ success: false, error: error.message });
    return true;
  }
});

// Keep service worker alive longer by listening to various events
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // This helps keep the service worker active
  if (changeInfo.status === 'complete' && tab.url && tab.url.includes('youtube.com/watch')) {
    // Service worker stays active when YouTube tabs are being watched
  }
});

// Handle startup to ensure service worker is ready
chrome.runtime.onStartup.addListener(() => {
  console.log('VidSage extension started');
});

chrome.runtime.onInstalled.addListener(() => {
  console.log('VidSage extension installed/updated');
});