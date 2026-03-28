// Foodpanda Menu Scraper - external script
// Loaded via bookmarklet: javascript:(function(){var s=document.createElement("script");s.src="https://on9claw.com/tea-treat/scrape.js";document.body.appendChild(s);})();
(function() {
  // Remove old panel if exists
  var old = document.getElementById('teaScraper');
  if (old) old.remove();

  // Create UI panel
  var panel = document.createElement('div');
  panel.id = 'teaScraper';
  panel.style.cssText = 'position:fixed;top:10px;left:10px;right:10px;z-index:999999;background:#111;color:#0f0;padding:16px;font:14px monospace;max-height:90vh;overflow:auto;border-radius:12px;box-shadow:0 4px 30px rgba(0,0,0,.8);';
  document.body.appendChild(panel);

  function log(msg) {
    panel.innerHTML += msg + '<br>';
    panel.scrollTop = 999999;
  }

  function q(sel, parent) {
    return [].slice.call((parent || document).querySelectorAll(sel));
  }

  log('<b style="color:#ff6b9d">🧋 Foodpanda Menu Scraper</b>');
  log('');

  // Step 1: Find menu items
  var selectors = [
    '[data-testid*="product"]',
    '[class*="product-card"]',
    '[class*="ProductCard"]',
    '[class*="menu-item"]',
    '[class*="MenuItem"]',
    '[class*="catalog-item"]',
    '[class*="CatalogItem"]',
    '[class*="dish"]',
    '[class*="Dish"]',
    '[class*="item-card"]',
    '[class*="ItemCard"]',
    'article'
  ];

  var bestSelector = null;
  var bestCards = [];
  var bestScore = 0;

  selectors.forEach(function(sel) {
    var cards = q(sel);
    if (cards.length > 0 && cards.length < 200) {
      // Score: prefer items with price-like text
      var score = 0;
      cards.forEach(function(c) {
        var text = c.innerText || '';
        if (text.match(/\$\d/)) score += 3;
        if (text.match(/免?費/)) score += 2;
        if (text.length > 10 && text.length < 200) score += 1;
      });
      log(sel + ': ' + cards.length + ' (score: ' + score + ')');
      if (score > bestScore) {
        bestScore = score;
        bestSelector = sel;
        bestCards = cards;
      }
    }
  });

  if (!bestCards.length) {
    log('');
    log('<b style="color:#ff5252">搵唔到 menu items!</b>');
    log('Body classes: ' + document.body.className.substring(0, 80));
    // Show some elements with Chinese text
    log('');
    log('Elements with Chinese text:');
    var allEls = q('*');
    var shown = 0;
    for (var i = 0; i < allEls.length && shown < 10; i++) {
      var text = (allEls[i].innerText || '').trim();
      if (text.match(/[\u4e00-\u9fff]/) && text.length > 2 && text.length < 60) {
        log('  <' + allEls[i].tagName + ' class="' + (allEls[i].className || '').substring(0, 50) + '"> ' + text.substring(0, 40));
        shown++;
      }
    }
    return;
  }

  log('');
  log('<b style="color:#4de8ff">Best: ' + bestSelector + ' (' + bestCards.length + ' items)</b>');
  log('');

  // Step 2: Extract name and price from each card
  var items = [];
  var itemsWithOpts = 0;

  function getName(card) {
    // Try multiple approaches
    var nameEl = card.querySelector('[class*="name"], [class*="Name"], [class*="title"], [class*="Title"]');
    if (nameEl) return nameEl.innerText.trim();
    // Try first meaningful text
    var texts = (card.innerText || '').split('\n');
    for (var i = 0; i < texts.length; i++) {
      var t = texts[i].trim();
      if (t.length > 1 && t.length < 60 && !t.match(/^\$/) && !t.match(/^\d/) && !t.match(/免?費/)) {
        return t;
      }
    }
    return '';
  }

  function getPrice(card) {
    var priceEl = card.querySelector('[class*="price"], [class*="Price"]');
    if (priceEl) {
      var m = priceEl.innerText.match(/\$?(\d+(?:\.\d+)?)/);
      if (m) return m[1];
    }
    // Try matching price pattern in full text
    var text = card.innerText || '';
    var m = text.match(/\$(\d+(?:\.\d+)?)/);
    if (m) return m[1];
    return '';
  }

  // Show first 3 cards for debug
  log('First 3 cards:');
  bestCards.slice(0, 3).forEach(function(card, i) {
    log('  Card ' + i + ': "' + getName(card) + '" $' + getPrice(card));
  });
  log('');

  // Step 3: Click each card, extract options, close
  log('開始提取 ' + bestCards.length + ' 個項目...');
  var idx = 0;

  function extractOptions() {
    var groups = [];
    // Look for option/modifier groups in any modal/sheet/dialog
    var containers = q('[class*="modal"], [class*="Modal"], [class*="dialog"], [class*="sheet"], [class*="Sheet"], [role="dialog"]');
    var container = containers.length ? containers[containers.length - 1] : document;

    q('[class*="option-group"], [class*="OptionGroup"], [class*="modifier"], [class*="Modifier"], [class*="question"], [class*="Question"], [class*="OptionSection"], [class*="variant"]', container).forEach(function(g) {
      var titleEl = g.querySelector('[class*="title"], [class*="name"], h3, h4, strong, legend');
      var title = titleEl ? titleEl.innerText.trim() : '';
      if (!title || title.length > 50) return;

      var required = g.innerText.indexOf('必選') > -1;
      var choices = [];
      q('[class*="choice"], [class*="option-item"], [class*="radio"], [class*="checkbox"], label, [class*="modifier-item"]', g).forEach(function(c) {
        var nameEl = c.querySelector('[class*="name"], [class*="label"]');
        var name = nameEl ? nameEl.innerText.trim() : c.innerText.trim().split('\n')[0].trim();
        if (name && name.length < 30 && name !== '完成' && name !== '取消') {
          choices.push({ name: name, price: '0' });
        }
      });

      if (choices.length) {
        groups.push({ title: title, required: required, choices: choices });
      }
    });

    return groups;
  }

  function closeModal() {
    var closeBtns = q('button');
    for (var i = 0; i < closeBtns.length; i++) {
      var text = (closeBtns[i].innerText || closeBtns[i].getAttribute('aria-label') || '').toLowerCase();
      if (text.match(/關|close|×|完成|取消|done|cancel/)) {
        closeBtns[i].click();
        return;
      }
    }
    // Try escape key
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', keyCode: 27, bubbles: true }));
  }

  function processNext() {
    if (idx >= bestCards.length) {
      // Done!
      log('');
      log('<b style="color:#4dff88">✅ 完成！提取 ' + items.length + ' 個項目 (' + itemsWithOpts + ' 個有 options)</b>');

      // Copy to clipboard
      var json = JSON.stringify(items, null, 2);
      navigator.clipboard.writeText(json).then(function() {
        log('已複製到剪貼簿！');
        log('');
        log('<button onclick="document.getElementById(\'teaScraper\').remove()" style="padding:8px 16px;border-radius:8px;border:none;background:#ff6b9d;color:#fff;cursor:pointer;font-size:14px">關閉</button>');
        log('<button onclick="var d=document.getElementById(\'teaScraper\');var t=document.createElement(\'textarea\');t.value=JSON.stringify(window._teaItems,null,2);t.style.cssText=\'width:100%;height:200px;background:#222;color:#0f0;border:none;padding:8px;font:12px monospace\';d.appendChild(t);" style="padding:8px 16px;border-radius:8px;border:none;background:#333;color:#0f0;cursor:pointer;font-size:14px;margin-left:8px">顯示 JSON</button>');
      }).catch(function() {
        log('複製失敗，請手動複製下方 JSON');
      });

      window._teaItems = items;
      return;
    }

    var card = bestCards[idx];
    var name = getName(card);
    var price = getPrice(card);

    if (!name || name.length < 2) {
      idx++;
      setTimeout(processNext, 50);
      return;
    }

    log('[' + (idx + 1) + '/' + bestCards.length + '] ' + name);

    // Click card
    card.click();

    setTimeout(function() {
      var opts = extractOptions();
      if (opts.length) {
        itemsWithOpts++;
        log('  → ⚙️ ' + opts.length + ' option groups');
      }
      items.push({ name: name, price: price, options: opts });

      closeModal();
      idx++;
      setTimeout(processNext, 500);
    }, 1000);
  }

  processNext();
})();
