// Site behaviour: menu, back to top, scroll reveal, count-up, bracket lines and replay,
// team explorer, match filters, photo lightbox. No dependencies.
(function () {
  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  root.classList.add('js');
  if (!reduce && 'IntersectionObserver' in window) root.classList.add('motion');

  function $all(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

  /* ---------- Menu ---------- */
  var btn = document.querySelector('.menu-btn');
  var menu = document.getElementById('menu');
  function setMenu(open) { btn.setAttribute('aria-expanded', String(open)); menu.hidden = !open; }
  if (btn && menu) {
    btn.addEventListener('click', function () { setMenu(menu.hidden); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !menu.hidden) { setMenu(false); btn.focus(); }
    });
    window.matchMedia('(min-width: 1024px)').addEventListener('change', function (mq) { if (mq.matches) setMenu(false); });
  }

  /* ---------- Back to top ---------- */
  var top = document.querySelector('.totop');
  if (top) {
    var onScroll = function () { top.hidden = window.scrollY < 600; };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------- Scroll reveal and count-up ---------- */
  if (root.classList.contains('motion')) {
    var targets = $all('main h2, .card, .place, .items > li, .toc li, .table-wrap, .bk, .stats > div, .timeline li, .callout, .champion, .explorer, .sb-grid > .scoreboard, .facts, .g-item');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target;
        io.unobserve(el);
        el.classList.add('in');
        // Drop the reveal classes afterwards so they never fight with other states.
        setTimeout(function () { el.classList.remove('rv', 'in'); }, 650);
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    targets.forEach(function (el, i) {
      el.classList.add('rv');
      el.style.transitionDelay = (i % 4) * 60 + 'ms';
      io.observe(el);
    });

    var counters = $all('[data-count]');
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        cio.unobserve(en.target);
        var el = en.target, end = +el.dataset.count, t0 = null;
        function frame(t) {
          if (!t0) t0 = t;
          var p = Math.min((t - t0) / 900, 1);
          el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
          if (p < 1) requestAnimationFrame(frame);
        }
        el.textContent = '0';
        requestAnimationFrame(frame);
      });
    });
    counters.forEach(function (el) { cio.observe(el); });
  }

  /* ---------- Team data ---------- */
  var dataEl = document.getElementById('team-data');
  var TEAMS = dataEl ? JSON.parse(dataEl.textContent) : null;
  var NAMES = {};
  $all('[data-pick]').forEach(function (b) {
    var lab = b.getAttribute('aria-label');
    if (b.dataset.pick && lab) NAMES[b.dataset.pick] = lab.replace(/^Follow team \w+, /, '');
  });

  /* ---------- Bracket lines ---------- */
  var brackets = $all('[data-bracket]');
  var SVGNS = 'http://www.w3.org/2000/svg';
  function hasTeam(el, t) {
    return !!t && (el.dataset.team === t || !!el.querySelector('[data-team="' + t + '"]'));
  }
  function drawLines(bk) {
    var svg = bk.querySelector('.bk-lines');
    if (!svg || getComputedStyle(svg).display === 'none') return;
    var box = bk.getBoundingClientRect();
    svg.setAttribute('viewBox', '0 0 ' + box.width + ' ' + box.height);
    svg.innerHTML = '';
    bk.dataset.links.split(',').forEach(function (spec) {
      var parts = spec.split(':'), ends = parts[0].split('>');
      var a = bk.querySelector('[data-node="' + ends[0] + '"]'), b = bk.querySelector('[data-node="' + ends[1] + '"]');
      if (!a || !b) return;
      var ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
      var sx = ra.right - box.left, sy = ra.top + ra.height / 2 - box.top;
      var tx = rb.left - box.left, ty = rb.top + rb.height / 2 - box.top;
      var mx = sx + (tx - sx) / 2;
      var path = document.createElementNS(SVGNS, 'path');
      path.setAttribute('d', 'M' + sx + ' ' + sy + ' H' + mx + ' V' + ty + ' H' + tx);
      path.dataset.from = ends[0]; path.dataset.to = ends[1]; path.dataset.step = parts[1];
      svg.appendChild(path);
    });
    paintLines(bk);
    if (bk.classList.contains('replaying')) applyStep(bk, +bk.dataset.at);
  }
  function paintLines(bk) {
    var t = selected;
    $all('.bk-lines path', bk).forEach(function (p) {
      var a = bk.querySelector('[data-node="' + p.dataset.from + '"]'), b = bk.querySelector('[data-node="' + p.dataset.to + '"]');
      p.classList.toggle('on', hasTeam(a, t) && hasTeam(b, t));
    });
  }
  function redrawAll() { brackets.forEach(drawLines); }
  if (brackets.length) {
    window.addEventListener('resize', redrawAll);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(redrawAll);
    window.addEventListener('load', redrawAll);
    redrawAll();
  }

  /* ---------- Bracket replay ---------- */
  var STEP_TEXT = ['Before the first serve', 'Round 1: M1 on Court 1, M2 on Court 2', 'Round 2: M3 and M4',
    'Round 3: M5 and M6. Pools decided', 'Round 4: the Final and the third-place match', 'Champions crowned'];
  function applyStep(bk, step) {
    bk.dataset.at = step;
    $all('[data-step]', bk).forEach(function (el) { el.classList.toggle('ahead', +el.dataset.step > step); });
    $all('.bk-lines path', bk).forEach(function (p) { p.classList.toggle('ahead', +p.dataset.step > step); });
    var st = bk.querySelector('.bk-status'), hint = bk.querySelector('.bk-hint');
    if (st) st.textContent = STEP_TEXT[step];
    if (hint) hint.textContent = STEP_TEXT[step];
  }
  brackets.forEach(function (bk) {
    var rb = bk.querySelector('.bk-replay'), hint = bk.querySelector('.bk-hint');
    var hintText = hint ? hint.textContent : '', timer = null;
    function stop() {
      clearInterval(timer); timer = null;
      bk.classList.remove('replaying');
      $all('.ahead', bk).forEach(function (el) { el.classList.remove('ahead'); });
      rb.textContent = 'Replay the tournament';
      if (hint) hint.textContent = hintText;
    }
    if (!rb) return;
    rb.addEventListener('click', function () {
      if (timer) { stop(); return; }
      var step = 0;
      bk.classList.add('replaying');
      rb.textContent = 'Stop replay';
      applyStep(bk, 0);
      timer = setInterval(function () {
        step += 1;
        if (step > 5) { stop(); return; }
        applyStep(bk, step);
        if (step === 5) setTimeout(function () { if (timer) stop(); if (hint) hint.textContent = STEP_TEXT[5]; }, 1600);
      }, 1200);
    });
  });

  /* ---------- Team selection (explorer + bracket) ---------- */
  var selected = '';
  var card = document.querySelector('.team-card');
  var ORD = ['', '1st', '2nd', '3rd', '4th', '5th', '6th'];
  var PLACE_LABEL = ['', 'Champions', 'Runners-up', 'Third place', 'Fourth place', 'Fifth place', 'Sixth place'];
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function renderCard(t) {
    if (!card) return;
    if (!t || !TEAMS || !TEAMS[t]) { card.hidden = true; card.innerHTML = ''; return; }
    var d = TEAMS[t], diff = d.pf - d.pa;
    var path = d.matches.map(function (m) {
      return '<li><span class="tc-res ' + (m.won ? 'w' : 'l') + '">' + (m.won ? 'W ' : 'L ') + m.us + '–' + m.them + '</span>' +
        '<span>vs <strong>' + esc(m.opp) + '</strong> ' + esc(m.oppName) + '</span>' +
        '<span class="tc-meta">' + esc(m.id + ' · ' + m.stage + ' · Round ' + m.round + ' · Court ' + m.court + (m.cap ? ' · time cap' : '')) + '</span></li>';
    }).join('');
    card.innerHTML = '<div class="tc-head"><p class="tc-name">' + esc(d.name) + '</p>' +
      '<p class="tc-place">' + PLACE_LABEL[d.place] + ' · Team ' + d.id + ' · ' + ORD[d.poolRank] + ' in Pool ' + d.pool + '</p></div>' +
      '<dl class="tc-stats"><div><dt>Record</dt><dd>' + d.w + '–' + d.l + '</dd></div><div><dt>Points for</dt><dd>' + d.pf + '</dd></div>' +
      '<div><dt>Against</dt><dd>' + d.pa + '</dd></div><div><dt>Diff</dt><dd>' + (diff > 0 ? '+' : diff < 0 ? '−' : '') + Math.abs(diff) + '</dd></div></dl>' +
      '<p class="label" style="color:inherit">Path through the tournament</p><ol class="tc-path">' + path + '</ol>';
    card.hidden = false;
  }
  function select(t, fromUser) {
    selected = t || '';
    document.body.classList.toggle('has-sel', !!selected);
    $all('[data-team]').forEach(function (el) { el.classList.toggle('is-sel', !!selected && el.dataset.team === selected); });
    $all('[data-teams]').forEach(function (el) { el.classList.toggle('is-sel', !!selected && el.dataset.teams.split(' ').indexOf(selected) > -1); });
    $all('.pick[data-pick]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.pick === selected)); });
    brackets.forEach(function (bk) {
      paintLines(bk);
      var st = bk.querySelector('.bk-status');
      if (st && !card) st.textContent = selected ? 'Following team ' + selected + ', ' + (NAMES[selected] || '') : 'Showing all teams';
    });
    renderCard(selected);
    if (fromUser && history.replaceState) {
      history.replaceState(null, '', selected ? '#team=' + selected : location.pathname + location.search);
    }
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-pick]');
    if (!b) return;
    var t = b.dataset.pick;
    // Tapping the team that is already followed clears it (except the "All teams" chip).
    select(t && t === selected && !b.classList.contains('pick') ? '' : t, true);
  });
  var m = location.hash.match(/team=([AB][123])/);
  if (m && document.querySelector('[data-team="' + m[1] + '"]')) select(m[1]);

  /* ---------- Match filters ---------- */
  var filters = document.querySelector('[data-filters]');
  if (filters) {
    var state = { court: '', round: '' };
    var boards = $all('.scoreboard');
    var count = filters.querySelector('.filter-count');
    filters.addEventListener('click', function (e) {
      var f = e.target.closest('[data-filter]');
      if (!f) return;
      state[f.dataset.filter] = f.dataset.value;
      $all('[data-filter="' + f.dataset.filter + '"]', filters).forEach(function (b) { b.setAttribute('aria-pressed', String(b === f)); });
      var shown = 0;
      boards.forEach(function (sb) {
        var ok = (!state.court || sb.dataset.court === state.court) && (!state.round || sb.dataset.round === state.round);
        sb.hidden = !ok;
        if (ok) shown++;
      });
      count.textContent = shown === boards.length ? 'Showing all ' + shown + ' matches' : 'Showing ' + shown + ' of ' + boards.length + ' matches';
    });
  }


  /* ---------- Interactive court (Rules page) ---------- */
  var court = document.querySelector('[data-court]');
  if (court) (function () {
    var D = JSON.parse(document.getElementById('court-data').textContent);
    var svg = court.querySelector('.cx-svg'), NS = 'http://www.w3.org/2000/svg';
    var title = court.querySelector('.cx-title'), text = court.querySelector('.cx-text'), note = court.querySelector('.cx-class'), kicker = court.querySelector('.cx-kicker');
    var ball = svg.querySelector('.cx-ball'), trail = svg.querySelector('.cx-trail'), marks = svg.querySelector('.cx-marks'),
        players = svg.querySelector('.cx-players'), fault = svg.querySelector('.cx-fault');
    var running = null;

    function highlight(zone) {
      $all('[data-zone]', court).forEach(function (el) {
        var on = el.dataset.zone === zone;
        if (el.tagName === 'BUTTON') el.setAttribute('aria-pressed', String(on)); else el.classList.toggle('on', on);
      });
    }
    function show(zone) {
      stopDemo(true);
      var z = D.zones[zone]; if (!z) return;
      highlight(zone);
      kicker.textContent = 'Court guide';
      title.textContent = z.t; text.textContent = z.p;
      note.hidden = !z.c; note.textContent = z.c ? 'At our tournament: ' + z.c.replace(/^At our tournament /, '') : '';
    }
    court.addEventListener('click', function (e) {
      var z = e.target.closest('[data-zone]');
      if (z) show(z.dataset.zone);
      var d = e.target.closest('[data-demo]');
      if (d) { if (d.getAttribute('aria-pressed') === 'true') stopDemo(); else playDemo(d.dataset.demo); }
    });
    court.addEventListener('keydown', function (e) {
      var z = e.target.closest('g[data-zone]');
      if (z && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); show(z.dataset.zone); }
    });

    function el(tag, attrs, parent) {
      var n = document.createElementNS(NS, tag);
      for (var k in attrs) n.setAttribute(k, attrs[k]);
      parent.appendChild(n); return n;
    }
    function clearDemo() {
      marks.innerHTML = ''; players.innerHTML = ''; trail.setAttribute('points', '');
      ball.setAttribute('cx', -20); ball.setAttribute('cy', -20); fault.classList.remove('show');
    }
    function stopDemo(keepPanel) {
      if (running) { running.cancelled = true; running = null; }
      $all('[data-demo]', court).forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
      clearDemo();
      if (!keepPanel) { highlight(''); title.textContent = 'Tap a part of the court'; text.textContent = 'Select an area on the court or a button below it, or watch a demo.'; note.hidden = true; kicker.textContent = 'Court guide'; }
    }
    function playDemo(name) {
      stopDemo(true);
      var d = D.demos[name], run = { cancelled: false }; running = run;
      $all('[data-demo]', court).forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.demo === name)); });
      highlight(d.zone || ''); note.hidden = true;
      kicker.textContent = 'Demo'; title.textContent = d.t.replace(/^Demo: /, '');
      d.players.forEach(function (p) {
        var g = el('g', { 'class': 'cx-player', transform: 'translate(' + p[0] + ' ' + p[1] + ')' }, players);
        el('circle', { r: 9 }, g); var t = el('text', {}, g); t.textContent = p[2];
      });
      var pts = [], i = 0, cur = d.steps[0].to.slice(), n = 0;
      function place(x, y) { ball.setAttribute('cx', x); ball.setAttribute('cy', y); }
      function next() {
        if (run.cancelled) return;
        if (i >= d.steps.length) {
          setTimeout(function () { if (!run.cancelled) { $all('[data-demo]', court).forEach(function (b) { b.setAttribute('aria-pressed', 'false'); }); running = null; } }, 400);
          return;
        }
        var s = d.steps[i++], from = cur.slice(), to = s.to;
        text.textContent = s.p;
        var done = function () {
          cur = to.slice(); pts.push(to.join(',')); trail.setAttribute('points', pts.join(' '));
          if (s.bounce || s.volley) {
            n++;
            el('circle', { 'class': 'cx-mark', cx: to[0], cy: to[1], r: s.volley ? 12 : 9 }, marks);
            var lt = el('text', { 'class': 'cx-marknum', x: to[0], y: to[1] - 16 }, marks);
            lt.textContent = s.volley ? 'volley' : 'bounce ' + n;
          }
          if (s.fault) { fault.setAttribute('transform', 'translate(' + (to[0] + 18) + ' ' + (to[1] - 18) + ')'); fault.classList.add('show'); }
          setTimeout(next, reduce ? 1800 : 1500);
        };
        if (i === 1) { place(to[0], to[1]); pts.push(to.join(',')); trail.setAttribute('points', pts.join(' ')); setTimeout(next, reduce ? 1800 : 1300); return; }
        if (reduce) { place(to[0], to[1]); done(); return; }
        var t0 = null, dur = 900;
        (function frame(t) {
          if (run.cancelled) return;
          if (!t0) t0 = t;
          var k = Math.min((t - t0) / dur, 1), e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
          var lift = Math.sin(Math.PI * k) * 26; // a little arc so the ball looks like it travels through the air
          place(from[0] + (to[0] - from[0]) * e, from[1] + (to[1] - from[1]) * e - lift);
          if (k < 1) requestAnimationFrame(frame); else done();
        })(performance.now());
      }
      next();
    }
  })();

  /* ---------- Lightbox ---------- */
  var links = $all('.g-link');
  if (!links.length) return;
  var box = document.createElement('div');
  box.className = 'lightbox';
  box.hidden = true;
  box.setAttribute('role', 'dialog');
  box.setAttribute('aria-modal', 'true');
  box.setAttribute('aria-label', 'Enlarged photo');
  box.innerHTML = '<button type="button" class="lb-close">Close</button><img alt=""><p class="lb-cap"></p>';
  document.body.appendChild(box);
  var img = box.querySelector('img'), cap = box.querySelector('.lb-cap'), close = box.querySelector('.lb-close');
  var current = -1, opener = null;
  function show(i) {
    current = (i + links.length) % links.length;
    var a = links[current];
    img.src = a.getAttribute('href');
    img.alt = a.querySelector('img').alt;
    cap.textContent = a.dataset.caption || '';
  }
  function hide() { box.hidden = true; document.body.style.overflow = ''; if (opener) opener.focus(); }
  links.forEach(function (a, i) {
    a.addEventListener('click', function (e) {
      e.preventDefault(); opener = a; show(i); box.hidden = false; document.body.style.overflow = 'hidden'; close.focus();
    });
  });
  close.addEventListener('click', hide);
  box.addEventListener('click', function (e) { if (e.target === box) hide(); });
  document.addEventListener('keydown', function (e) {
    if (box.hidden) return;
    if (e.key === 'Escape') hide();
    if (e.key === 'ArrowRight') show(current + 1);
    if (e.key === 'ArrowLeft') show(current - 1);
    if (e.key === 'Tab') { e.preventDefault(); close.focus(); }
  });
})();
