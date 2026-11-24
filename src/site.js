// Menu toggle, back-to-top button, photo lightbox. No dependencies.
(function () {
  var btn = document.querySelector('.menu-btn');
  var menu = document.getElementById('menu');
  function setMenu(open) {
    btn.setAttribute('aria-expanded', String(open));
    menu.hidden = !open;
  }
  if (btn && menu) {
    btn.addEventListener('click', function () { setMenu(menu.hidden); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !menu.hidden) { setMenu(false); btn.focus(); }
    });
    window.matchMedia('(min-width: 1024px)').addEventListener('change', function (mq) { if (mq.matches) setMenu(false); });
  }

  var top = document.querySelector('.totop');
  if (top) {
    var onScroll = function () { top.hidden = window.scrollY < 600; };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  var links = Array.prototype.slice.call(document.querySelectorAll('.g-link'));
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
