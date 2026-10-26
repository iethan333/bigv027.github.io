/* 站内搜索：读 /index.json，本地过滤，无依赖。 */
(function () {
  var input = document.getElementById('q');
  var status = document.getElementById('status');
  var results = document.getElementById('results');
  if (!input || !results) return;

  var data = [];
  var ready = false;

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function render(list, query) {
    results.innerHTML = '';
    if (!query) {
      status.textContent = '';
      return;
    }
    if (!list.length) {
      status.textContent = '没有找到「' + query + '」。换个词试试。';
      return;
    }
    status.textContent = '找到 ' + list.length + ' 篇';
    var frag = document.createDocumentFragment();
    list.forEach(function (p) {
      var li = document.createElement('li');
      li.innerHTML =
        '<a class="entry" href="' + esc(p.u) + '">' +
        '<time class="entry-date">' + esc(p.d) + '</time>' +
        '<span class="entry-body">' +
        '<span class="entry-title">' + esc(p.t) + '</span>' +
        '<span class="entry-excerpt">' + esc(p.s) + ' · ' + esc(p.x) + '</span>' +
        '</span></a>';
      frag.appendChild(li);
    });
    results.appendChild(frag);
  }

  function search() {
    var q = input.value.trim().toLowerCase();
    if (!ready) return;
    if (!q) { render([], ''); return; }
    var terms = q.split(/\s+/).filter(Boolean);
    var hits = data.filter(function (p) {
      var hay = (p.t + ' ' + p.x + ' ' + p.s).toLowerCase();
      return terms.every(function (t) { return hay.indexOf(t) !== -1; });
    });
    render(hits, q);
  }

  fetch('/index.json')
    .then(function (r) { return r.json(); })
    .then(function (json) {
      data = json;
      ready = true;
      var q = new URLSearchParams(location.search).get('q');
      if (q) { input.value = q; }
      search();
    })
    .catch(function () {
      status.textContent = '搜索索引没加载成功，刷新试试。';
    });

  var timer;
  input.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(search, 120);
  });
})();
