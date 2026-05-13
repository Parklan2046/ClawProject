// Tea Treat Menu Scraper v2 - Smart extraction for Foodpanda / Keeta
// Usage: javascript:(function(){var s=document.createElement("script");s.src="https://on9claw.com/tea-treat/scrape.js";document.body.appendChild(s);})();
(function() {
  var old = document.getElementById('teaScraper');
  if (old) old.remove();

  var panel = document.createElement('div');
  panel.id = 'teaScraper';
  panel.style.cssText = 'position:fixed;top:10px;left:10px;right:10px;z-index:999999;background:#111;color:#0f0;padding:16px;font:13px monospace;max-height:90vh;overflow:auto;border-radius:12px;box-shadow:0 4px 30px rgba(0,0,0,.9);';
  document.body.appendChild(panel);

  function log(msg, color) {
    panel.innerHTML += '<span style="color:' + (color || '#0f0') + '">' + msg + '</span><br>';
    panel.scrollTop = 999999;
  }

  function logHeader(msg) {
    log('<b style="color:#ff6b9d">' + msg + '</b>');
  }

  function logDim(msg) {
    log(msg, '#888');
  }

  logHeader('🧋 Tea Treat Menu Scraper v2');
  log('URL: ' + window.location.href);
  var site = window.location.hostname.includes('foodpanda') ? 'Foodpanda' :
             window.location.hostname.includes('keeta') ? 'Keeta' :
             window.location.hostname.includes('deliveroo') ? 'Deliveroo' : 'Unknown';
  log('Site: ' + site);
  log('');

  // ====== STRATEGY 1: Find price patterns in DOM ======
  // This works regardless of CSS class changes
  logHeader('🔍 Scanning for menu items...');

  var pricePattern = /\$\s*(\d+(?:\.\d{1,2})?)/;
  var allElements = document.querySelectorAll('*');
  var priceElements = [];
  var seen = new Set();

  // Find all elements containing a price
  allElements.forEach(function(el) {
    var text = (el.textContent || '').trim();
    // Skip huge containers
    if (text.length > 200 || text.length < 2) return;
    if (el.children.length > 10) return;
    
    var m = text.match(pricePattern);
    if (m) {
      var key = m[1] + '|' + el.tagName + '|' + text.substring(0, 30);
      if (!seen.has(key)) {
        seen.add(key);
        priceElements.push({ el: el, price: parseFloat(m[1]), text: text });
      }
    }
  });

  log('Found ' + priceElements.length + ' price elements');

  // ====== STRATEGY 2: Find menu item containers ======
  // Each menu item = name + price nearby
  var menuItems = [];
  var processed = new Set();

  priceElements.forEach(function(pe) {
    if (processed.has(pe.el)) return;

    // Walk up to find the item container
    var container = pe.el;
    for (var i = 0; i < 5 && container; i++) {
      var parent = container.parentElement;
      if (!parent) break;
      
      // Check if this container has exactly one price child (likely a menu item)
      var pricesInContainer = parent.querySelectorAll('*').length > 0 ? 
        Array.from(parent.querySelectorAll('*')).filter(function(c) {
          return pricePattern.test(c.textContent || '') && c.textContent.trim().length < 200;
        }).length : 0;
      
      if (pricesInContainer >= 1 && pricesInContainer <= 3) {
        container = parent;
        break;
      }
      container = parent;
    }

    // Now extract name from this container
    var fullText = (container.textContent || '').replace(/\s+/g, ' ').trim();
    
    // Find Chinese/English name before the price
    var priceIdx = fullText.search(pricePattern);
    var beforePrice = priceIdx > 0 ? fullText.substring(0, priceIdx).trim() : fullText.split('$')[0].trim();
    
    // Clean up the name
    var name = beforePrice
      .replace(/\$\d+(?:\.\d+)?/g, '')
      .replace(/^[\s•·\-–—]+/, '')
      .replace(/[\s•·\-–—]+$/, '')
      .trim();

    if (name && name.length > 1 && name.length < 80) {
      var key = name + '|' + pe.price;
      if (!processed.has(key)) {
        processed.add(key);
        menuItems.push({
          name: name,
          price: pe.price.toString(),
          container: container
        });
        processed.add(pe.el);
      }
    }
  });

  // Deduplicate by name
  var deduped = [];
  var names = new Set();
  menuItems.forEach(function(item) {
    var key = item.name.toLowerCase().replace(/\s+/g, '');
    if (!names.has(key)) {
      names.add(key);
      deduped.push(item);
    }
  });

  log('Extracted ' + deduped.length + ' unique menu items');
  log('');

  if (deduped.length === 0) {
    log('<b style="color:#ff5252">❌ No menu items found!</b>');
    log('');
    log('Debug info:');
    log('  Body classes: ' + (document.body.className || '(none)'));
    log('  Page title: ' + document.title);
    
    // Look for data blobs (Next.js __NEXT_DATA__, etc.)
    var dataScripts = document.querySelectorAll('script[id*="data"], script[type="application/json"]');
    log('  Data scripts: ' + dataScripts.length);
    dataScripts.forEach(function(s, i) {
      try {
        var d = JSON.parse(s.textContent);
        var keys = Object.keys(d).slice(0, 10);
        log('  Script[' + i + '] keys: ' + keys.join(', '));
      } catch(e) {}
    });

    // Show sample DOM elements that have Chinese + price
    log('');
    log('Sample elements with Chinese + price:');
    var count = 0;
    priceElements.slice(0, 15).forEach(function(pe) {
      log('  💰 $' + pe.price + ' | ' + pe.text.substring(0, 60));
    });
    return;
  }

  // ====== STRATEGY 3: Extract options (ice, sugar, size) ======
  logHeader('🔧 Extracting options...');
  var itemsWithOptions = 0;
  var idx = 0;

  function extractOptions() {
    var opts = [];
    // Look for option selectors in any visible modal/dialog
    var dialogs = document.querySelectorAll('[role="dialog"], [class*="modal"], [class*="drawer"], [class*="sheet"], [class*="overlay"]');
    var scope = dialogs.length > 0 ? dialogs[dialogs.length - 1] : document;

    // Find option groups
    var groups = scope.querySelectorAll('[class*="option-group"], [class*="modifier-group"], [class*="variant-group"], fieldset, [class*="question"]');
    
    groups.forEach(function(g) {
      var title = '';
      var titleEl = g.querySelector('h3, h4, strong, legend, [class*="title"], [class*="name"], [class*="label"]');
      if (titleEl) title = titleEl.textContent.trim();
      if (!title || title.length > 60) return;

      var required = g.textContent.includes('必選') || g.textContent.includes('Required');
      var choices = [];
      var choiceEls = g.querySelectorAll('[class*="choice"], [class*="option"], label, [class*="radio"], [class*="checkbox"], button');
      
      choiceEls.forEach(function(c) {
        var cn = c.textContent.trim();
        // Clean up - remove price from choice text
        cn = cn.replace(/\+\$\s*\d+(?:\.\d+)?/g, '').trim();
        if (cn && cn.length > 0 && cn.length < 40 && 
            cn !== '完成' && cn !== '取消' && cn !== 'Done' && cn !== 'Cancel' &&
            !cn.startsWith('$')) {
          // Check if this choice has an extra price
          var extraPrice = '0';
          var priceMatch = c.textContent.match(/\+\$\s*(\d+(?:\.\d+)?)/);
          if (priceMatch) extraPrice = priceMatch[1];
          choices.push({ name: cn, price: extraPrice });
        }
      });

      if (choices.length > 0) {
        opts.push({ title: title, required: required, choices: choices });
      }
    });

    return opts;
  }

  function closeModal() {
    // Click close/done/cancel buttons
    var btns = document.querySelectorAll('button, [role="button"]');
    for (var i = 0; i < btns.length; i++) {
      var t = (btns[i].textContent || btns[i].getAttribute('aria-label') || '').trim();
      if (t.match(/關|close|×|✕|完成|取消|done|cancel|back/i)) {
        try { btns[i].click(); return; } catch(e) {}
      }
    }
    // Escape key
    try { document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); } catch(e) {}
  }

  function processNext() {
    if (idx >= Math.min(deduped.length, 40)) {
      // Done - show result
      log('');
      logHeader('✅ 完成！提取 ' + itemsWithOptions + ' 個有選項項目');

      window._teaItems = deduped;

      // Show summary table
      log('<br><table style="width:100%;border-collapse:collapse;font-size:12px">');
      log('<tr style="color:#4de8ff"><td style="padding:4px">#</td><td>Name</td><td style="text-align:right">Price</td><td>Options</td></tr>');
      deduped.forEach(function(item, i) {
        var optCount = (item.options || []).length;
        log('<tr style="border-top:1px solid #222"><td style="padding:4px">' + (i+1) + '</td><td>' + item.name + '</td><td style="text-align:right;color:#ffc94d">$' + item.price + '</td><td style="color:' + (optCount > 0 ? '#4dff88' : '#888') + '">' + (optCount > 0 ? optCount + ' options' : 'none') + '</td></tr>');
      });
      log('</table>');

      // Copy button
      log('<br><button onclick="navigator.clipboard.writeText(JSON.stringify(window._teaItems,null,2)).then(function(){this.textContent=\\'Copied!\\'})" style="padding:10px 20px;border-radius:10px;border:none;background:#ff6b9d;color:#fff;cursor:pointer;font-size:14px;font-weight:700">📋 Copy JSON</button>');
      log('<button onclick="document.getElementById(\"teaScraper\").remove()" style="padding:10px 20px;border-radius:10px;border:1px solid #333;background:transparent;color:#888;cursor:pointer;font-size:14px;margin-left:8px">Close</button>');
      return;
    }

    var item = deduped[idx];
    var card = item.container;

    // Progress
    var pct = Math.round((idx / Math.min(deduped.length, 40)) * 100);
    log('[' + (idx+1) + '/' + Math.min(deduped.length, 40) + '] ' + item.name + ' — $' + item.price + ' (' + pct + '%)');

    // Click the item to open options modal
    try {
      // Find a clickable element within the container
      var clickable = card.querySelector('button, a, [role="button"], [onclick]');
      if (clickable) {
        clickable.click();
      } else {
        card.click();
      }
    } catch(e) {
      card.click();
    }

    setTimeout(function() {
      var opts = extractOptions();
      if (opts.length > 0) {
        itemsWithOptions++;
        logDim('  ↳ ' + opts.length + ' option groups found');
      }
      item.options = opts;

      closeModal();
      idx++;
      setTimeout(processNext, 400);
    }, 1200);
  }

  processNext();
})();
