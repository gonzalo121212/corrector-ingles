(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var TIPOS = { gramatica: 'Gramática', vocabulario: 'Vocabulario', ortografia: 'Ortografía',
    puntuacion: 'Puntuación', naturalidad: 'Sugerencia' };

  function clase(tipo) { return tipo === 'naturalidad' ? 'sugerencia' : 'error'; }
  function el(tag, cls, texto) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }

  $('texto').addEventListener('input', function () { $('contador').textContent = this.value.length; });
  $('texto').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); $('formulario').requestSubmit(); }
  });

  $('formulario').addEventListener('submit', function (e) {
    e.preventDefault();
    var texto = $('texto').value.trim();
    if (!texto) return;
    $('error').hidden = true;
    $('corregir').disabled = true;
    $('corregir').textContent = 'Corrigiendo…';
    fetch('/api/corregir', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texto: texto })
    }).then(function (r) {
      return r.json().then(function (j) { return { ok: r.ok, j: j }; });
    }).then(function (res) {
      if (!res.ok) throw new Error(res.j.detail || 'No se pudo corregir');
      pintar(res.j);
    }).catch(function (err) {
      $('error').textContent = err.message === 'Failed to fetch' || err.name === 'TypeError'
        ? 'No hay conexión con el corrector. ¿Sigue abierta su ventana?' : err.message;
      $('error').hidden = false;
    }).then(function () {
      $('corregir').disabled = false;
      $('corregir').textContent = 'Corregir';
    });
  });

  function pintar(d) {
    var res = $('resultado');
    res.textContent = '';
    d.trozos.forEach(function (t) {
      if (!t.numero) { res.appendChild(document.createTextNode(t.texto)); return; }
      var m = el('span', 'marca ' + clase(t.tipo));
      m.title = TIPOS[t.tipo] || '';
      m.appendChild(el('del', '', t.texto));
      m.appendChild(document.createTextNode(' '));
      m.appendChild(el('ins', '', t.correccion));
      m.appendChild(el('sup', '', String(t.numero)));
      res.appendChild(m);
    });

    var ver = $('veredicto');
    ver.hidden = !(d.correcto || d.aviso);
    ver.className = 'veredicto ' + (d.aviso ? 'aviso' : 'bien');
    ver.textContent = d.aviso || '¡Correcto! No hay nada que corregir.';
    $('leyenda').hidden = d.fallos.length === 0;

    var ol = $('explicacion');
    ol.textContent = '';
    d.fallos.forEach(function (f) {
      var li = el('li', clase(f.tipo));
      var cab = el('div', 'cambio');
      cab.appendChild(el('span', 'num ' + clase(f.tipo), f.numero + '.'));
      cab.appendChild(el('del', '', f.original));
      cab.appendChild(document.createTextNode(' → '));
      cab.appendChild(el('ins', '', f.correccion));
      cab.appendChild(el('span', 'etiqueta', TIPOS[f.tipo] || f.tipo));
      if (!f.colocado) cab.appendChild(el('span', 'etiqueta', 'sin marcar'));
      li.appendChild(cab);
      li.appendChild(el('p', '', f.explicacion));
      ol.appendChild(li);
    });
    $('caja-explicacion').hidden = d.fallos.length === 0;

    $('corregido').textContent = d.texto_corregido;
    $('caja-corregido').hidden = d.fallos.length === 0;
    $('modelo').textContent = 'Corregido con ' + d.modelo;
    $('salida').hidden = false;
  }

  $('copiar').addEventListener('click', function () {
    var boton = this;
    navigator.clipboard.writeText($('corregido').textContent).then(function () {
      boton.textContent = 'Copiado';
      setTimeout(function () { boton.textContent = 'Copiar'; }, 1500);
    });
  });
})();
