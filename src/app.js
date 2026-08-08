(function () {
  'use strict';

  /* ---------- theme detection ---------- */
  var mq = window.matchMedia('(prefers-color-scheme: dark)');

  function isDark() {
    var t = document.documentElement.getAttribute('data-theme');
    if (t === 'dark') return true;
    if (t === 'light') return false;
    return mq.matches;
  }

  /* ---------- plantogram ---------- */
  var RAMP_LIGHT = ['#E6EDE9', '#CFE0D9', '#AECDC2', '#EAC96B', '#E59A41', '#D96436', '#C13A2B'];
  var RAMP_DARK = ['#1C2F2E', '#26443F', '#33625A', '#B08A2E', '#C06A2C', '#C24E26', '#C63A2A'];
  var BANDS = [0.10, 0.22, 0.36, 0.52, 0.68, 0.84];

  // pressure zones for the left foot (toes up, medial side toward canvas centre)
  var LEFT_FOOT = [
    [258, 118, 28, 0.90], // hallux
    [224, 96, 13, 0.50], [194, 92, 12, 0.42], [168, 98, 11, 0.36], [146, 110, 10, 0.30],
    [266, 186, 26, 0.85], [232, 174, 25, 0.80], [200, 172, 23, 0.62], [172, 180, 21, 0.50], [148, 196, 20, 0.42],
    [150, 268, 30, 0.45], [158, 328, 32, 0.50], // lateral column
    [200, 428, 48, 1.00], [202, 456, 38, 0.80]  // heel
  ];

  function hexRgb(hex) {
    return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
  }

  function drawPlantogram() {
    var canvas = document.getElementById('plantogram');
    if (!canvas || !canvas.getContext) return;
    var w = canvas.width, h = canvas.height;

    // accumulate a smooth intensity field: t += weight * (1 - d²/R²)²
    var field = new Float32Array(w * h);

    function blob(cx, cy, r, wgt) {
      var R = r * 1.9, R2 = R * R;
      var x0 = Math.max(0, Math.floor(cx - R)), x1 = Math.min(w - 1, Math.ceil(cx + R));
      var y0 = Math.max(0, Math.floor(cy - R)), y1 = Math.min(h - 1, Math.ceil(cy + R));
      for (var y = y0; y <= y1; y++) {
        var dy = y - cy;
        for (var x = x0; x <= x1; x++) {
          var dx = x - cx;
          var q = 1 - (dx * dx + dy * dy) / R2;
          if (q > 0) field[y * w + x] += wgt * q * q;
        }
      }
    }

    LEFT_FOOT.forEach(function (z) {
      blob(z[0], z[1], z[2], z[3]);          // left foot
      blob(w - z[0], z[1], z[2], z[3]);      // right foot, mirrored
    });

    // posterize intensity into contour bands
    var ramp = (isDark() ? RAMP_DARK : RAMP_LIGHT).map(hexRgb);
    var ctx = canvas.getContext('2d');
    var out = ctx.createImageData(w, h);
    var d = out.data;

    for (var i = 0; i < field.length; i++) {
      var t = field[i];
      if (t < BANDS[0]) continue; // transparent
      var band = 0;
      while (band < BANDS.length - 1 && t >= BANDS[band + 1]) band++;
      var c = ramp[Math.min(band + 1, ramp.length - 1)];
      var p = i * 4;
      d[p] = c[0]; d[p + 1] = c[1]; d[p + 2] = c[2]; d[p + 3] = 255;
    }
    ctx.clearRect(0, 0, w, h);
    ctx.putImageData(out, 0, 0);
  }

  function drawLegend() {
    var el = document.getElementById('scan-legend');
    if (!el) return;
    var ramp = isDark() ? RAMP_DARK : RAMP_LIGHT;
    el.innerHTML = 'Нагрузка ';
    [2, 3, 4, 5, 6].forEach(function (i) {
      var chip = document.createElement('i');
      chip.style.background = ramp[i];
      el.appendChild(chip);
    });
  }

  function render() { drawPlantogram(); drawLegend(); }

  render();
  if (mq.addEventListener) mq.addEventListener('change', render);
  new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  /* ---------- reveal on scroll ---------- */
  var revealed = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('is-in');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.15 });
    revealed.forEach(function (el) { io.observe(el); });
  } else {
    revealed.forEach(function (el) { el.classList.add('is-in'); });
  }
})();
