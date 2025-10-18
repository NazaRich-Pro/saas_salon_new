/**
 * BeautyHub Booking Widget Embed Script
 * 
 * Usage:
 * <script src="https://{TENANT}.saas.akylman.online/widget.js"></script>
 * <div id="booking-widget"></div>
 */

(function() {
  'use strict';
  
  // Get current script to extract tenant info
  const currentScript = document.currentScript || document.querySelector('script[src*="widget.js"]');
  const scriptSrc = currentScript ? currentScript.src : '';
  
  // Extract host from script URL
  const scriptUrl = new URL(scriptSrc);
  const tenantHost = scriptUrl.host;
  
  // Configuration
  const config = {
    host: tenantHost,
    baseUrl: `https://${tenantHost}`,
    widgetUrl: `https://${tenantHost}/widget`,
    containerId: 'booking-widget',
    mode: 'iframe', // or 'inline' for future
  };
  
  /**
   * Initialize widget
   */
  function initWidget() {
    // Find container
    const container = document.getElementById(config.containerId);
    
    if (!container) {
      console.error('BeautyHub Widget: Container element not found. Add <div id="booking-widget"></div> to your page.');
      return;
    }
    
    // Create iframe
    const iframe = document.createElement('iframe');
    iframe.src = config.widgetUrl;
    iframe.style.width = '100%';
    iframe.style.minHeight = '600px';
    iframe.style.border = 'none';
    iframe.style.borderRadius = '8px';
    iframe.title = 'Booking Widget';
    
    // Allow iframe to be responsive
    iframe.setAttribute('scrolling', 'no');
    
    // Insert iframe
    container.appendChild(iframe);
    
    // Handle iframe resizing
    window.addEventListener('message', function(event) {
      // Only accept messages from our domain
      if (event.origin !== config.baseUrl) return;
      
      if (event.data.type === 'resize') {
        iframe.style.height = event.data.height + 'px';
      }
      
      if (event.data.type === 'booking-success') {
        // Trigger custom event for parent page
        const bookingEvent = new CustomEvent('beautyhub-booking-success', {
          detail: event.data.appointment
        });
        window.dispatchEvent(bookingEvent);
      }
    });
    
    // Send ready message to iframe
    iframe.onload = function() {
      iframe.contentWindow.postMessage({
        type: 'widget-ready',
        config: config
      }, config.baseUrl);
    };
  }
  
  /**
   * Auto-init when DOM is ready
   */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWidget);
  } else {
    initWidget();
  }
  
  // Expose API
  window.BeautyHubWidget = {
    version: '1.0.0',
    init: initWidget,
    config: config
  };
  
})();

