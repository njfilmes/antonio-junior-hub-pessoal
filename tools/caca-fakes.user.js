// ==UserScript==
// @name         Caça-Fakes (ajudante de remoção)
// @namespace    njfilmes
// @version      1.1
// @description  Preenche a busca de Seguidores do Instagram com o próximo perfil suspeito e destaca o botão Remover. Nunca clica sozinho.
// @match        https://www.instagram.com/*
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_setClipboard
// @run-at       document-idle
// @updateURL    https://raw.githubusercontent.com/njfilmes/antonio-junior-hub-pessoal/claude/cloud-connection-test-wqbcb9/tools/caca-fakes.user.js
// @downloadURL  https://raw.githubusercontent.com/njfilmes/antonio-junior-hub-pessoal/claude/cloud-connection-test-wqbcb9/tools/caca-fakes.user.js
// ==/UserScript==

// Como funciona:
// 1. No painel Caça-Fakes, toque em "Copiar lista pro script" e cole no campo deste ajudante.
// 2. No Instagram, abra seu perfil > seguidores (a janelinha com a busca).
// 3. O ajudante escreve o próximo nome na busca e contorna o botão "Remover" em vermelho.
// 4. Você clica em Remover e confirma. O ajudante conta e, depois de uns segundos, escreve o próximo.
// Ele não clica em nada: todo "Remover" é clique seu. Para no limite do dia.
// Travas: pausa de 4 a 8 segundos entre remoções e rodadas de 15, com 2 horas de descanso entre elas.

(function () {
  'use strict';

  const K = { list: 'cf_list', idx: 'cf_idx', done: 'cf_done', limit: 'cf_limit', open: 'cf_open', next: 'cf_next' };
  const get = (k, d) => { try { const v = GM_getValue(k); return v === undefined ? d : v; } catch (e) { return d; } };
  const set = (k, v) => { try { GM_setValue(k, v); } catch (e) {} };
  const today = () => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
  const REMOVE_RE = /^(remover|remove)$/i;
  const PAUSE_MIN = 4000, PAUSE_MAX = 8000;   // pausa entre uma remoção e outra
  const ROUND = 15, BREAK_MS = 2 * 60 * 60 * 1000; // no máximo 15 remoções a cada 2 horas

  let list = get(K.list, []);          // nomes pendentes, em ordem
  let idx = get(K.idx, 0);             // posição do próximo
  let done = get(K.done, []);          // [[usuario, data, horário], ...]
  let nextAt = get(K.next, 0);         // antes disso, não preenche o próximo
  let autoFill = false;
  let limit = get(K.limit, 40);
  let current = null;                  // nome que está na busca agora
  let highlighted = null;
  let waitTimer = null;

  const doneToday = () => done.filter(d => d[1] === today()).length;
  const doneSet = () => new Set(done.map(d => d[0]));
  // Quando a rodada libera: com 15 remoções nas últimas 2 horas, espera a mais antiga completar 2 horas.
  function roundRelease() {
    const now = Date.now();
    const ts = done.map(d => d[2]).filter(t => t && now - t < BREAK_MS).sort((a, b) => a - b);
    return ts.length < ROUND ? 0 : ts[ts.length - ROUND] + BREAK_MS;
  }
  const waitUntil = () => Math.max(nextAt, roundRelease());
  const hhmm = (t) => { const d = new Date(t); return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'); };
  const inRound = () => { const now = Date.now(); return done.filter(d => d[2] && now - d[2] < BREAK_MS).length; };

  /* ---------- interface ---------- */
  const box = document.createElement('div');
  box.id = 'cf-box';
  box.innerHTML = `
    <style>
      #cf-box{position:fixed;right:16px;bottom:16px;z-index:2147483647;width:280px;background:#15201C;color:#E4EDE9;border-radius:14px;
        font:13px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif;box-shadow:0 10px 30px rgba(0,0,0,.35);overflow:hidden}
      #cf-box *{box-sizing:border-box}
      #cf-box header{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:#0D6A5D;font-weight:700;cursor:pointer}
      #cf-box .cf-body{padding:12px;display:flex;flex-direction:column;gap:8px}
      #cf-box .cf-next{font:600 15px ui-monospace,Menlo,monospace;word-break:break-all;color:#fff}
      #cf-box .cf-muted{color:#93A69F;font-size:12px}
      #cf-box .cf-row{display:flex;gap:6px}
      #cf-box button{flex:1;font:600 12px system-ui,sans-serif;border-radius:8px;border:1px solid #2A3833;background:#1B2723;color:#E4EDE9;padding:8px;cursor:pointer}
      #cf-box button.cf-pri{background:#52C4B0;border-color:#52C4B0;color:#04201B}
      #cf-box button:disabled{opacity:.45;cursor:not-allowed}
      #cf-box .cf-wait{background:#1B2723;border:1px solid #52C4B0;border-radius:8px;padding:8px}
      #cf-box textarea{width:100%;height:70px;border-radius:8px;border:1px solid #2A3833;background:#0D1412;color:#E4EDE9;font:12px ui-monospace,monospace;padding:6px}
      #cf-box .cf-meter{height:6px;border-radius:9px;background:#2A3833;overflow:hidden}
      #cf-box .cf-meter span{display:block;height:100%;background:#5FCD8E}
      #cf-box .cf-stop{background:#3A1912;border:1px solid #FF8069;color:#FFB4A6;border-radius:8px;padding:8px}
      #cf-box input{width:56px;border-radius:6px;border:1px solid #2A3833;background:#0D1412;color:#E4EDE9;padding:3px 6px;font:12px ui-monospace,monospace}
      .cf-target{outline:3px solid #FF4D2E !important;outline-offset:2px;border-radius:8px}
    </style>
    <header id="cf-toggle"><span>🧹 Caça-Fakes</span><span id="cf-mini"></span></header>
    <div class="cf-body" id="cf-body"></div>`;

  function render() {
    const body = box.querySelector('#cf-body');
    const open = get(K.open, true);
    body.style.display = open ? 'flex' : 'none';
    const n = doneToday();
    box.querySelector('#cf-mini').textContent = n + '/' + limit + ' hoje';
    const pending = list.length - idx;
    let h = '';
    h += `<div class="cf-meter"><span style="width:${Math.min(100, n / limit * 100)}%"></span></div>`;
    h += `<div class="cf-muted">Hoje: <b>${n}</b> de ${limit} · Limite <input id="cf-limit" type="number" min="5" max="200" value="${limit}"> · Faltam ${Math.max(0, pending)}</div>`;
    if (!list.length || pending <= 0) {
      h += `<div class="cf-muted">${list.length ? 'Lista terminada. 🎉 Cole uma nova, se quiser.' : 'Cole aqui a lista copiada no painel Caça-Fakes (um nome por linha).'}</div>`;
      h += `<textarea id="cf-paste" placeholder="usuario1&#10;usuario2&#10;..."></textarea>`;
      h += `<div class="cf-row"><button class="cf-pri" id="cf-load">Carregar lista</button></div>`;
    } else if (n >= limit) {
      h += `<div class="cf-stop"><b>Limite de hoje atingido.</b> Pare e continue amanhã, para o Instagram não bloquear suas ações.</div>`;
    } else if (roundRelease() > Date.now()) {
      h += `<div class="cf-wait"><b>Rodada de ${ROUND} concluída.</b> Descanse um pouco. A próxima rodada libera às <b>${hhmm(roundRelease())}</b>.</div>`;
    } else {
      const wait = waitUntil() - Date.now();
      h += `<div class="cf-muted">Próximo: <span id="cf-count">${wait > 0 ? 'em ' + Math.ceil(wait / 1000) + 's' : ''}</span></div><div class="cf-next">@${list[idx]}</div>`;
      h += `<div class="cf-muted" id="cf-hint">${hint()}</div>`;
      h += `<div class="cf-row"><button class="cf-pri" id="cf-fill"${wait > 0 ? ' disabled' : ''}>Preencher busca</button><button id="cf-skip">Pular</button></div>`;
      h += `<div class="cf-muted">Rodada: ${inRound()} de ${ROUND} · pausa de 4 a 8 s entre remoções</div>`;
    }
    h += `<div class="cf-row"><button id="cf-copy">Copiar removidos (${done.length})</button><button id="cf-new">Nova lista</button></div>`;
    body.innerHTML = h;
  }

  function hint() {
    if (!dialogInput()) return 'Abra seu perfil › <b>seguidores</b> (a janelinha com a busca).';
    if (current && highlighted) return 'Clique no <b>Remover</b> contornado em vermelho e confirme.';
    if (current) return 'Procurando @' + current + ' na lista…';
    return 'Toque em <b>Preencher busca</b>.';
  }
  function setHint(t) { const el = box.querySelector('#cf-hint'); if (el) el.innerHTML = t; }

  box.addEventListener('click', (e) => {
    const t = e.target;
    if (t.closest('#cf-toggle')) { set(K.open, !get(K.open, true)); render(); return; }
    if (t.id === 'cf-load') {
      const names = (box.querySelector('#cf-paste').value || '').split(/[\s,;]+/).map(s => s.trim().replace(/^@/, '').toLowerCase()).filter(s => /^[a-z0-9._]{1,30}$/.test(s));
      const ds = doneSet();
      list = Array.from(new Set(names)).filter(u => !ds.has(u)); idx = 0;
      set(K.list, list); set(K.idx, idx); current = null; render();
      return;
    }
    if (t.id === 'cf-fill') { fill(); return; }
    if (t.id === 'cf-skip') { advance(); return; }
    if (t.id === 'cf-copy') {
      const txt = done.map(d => d[0] + ';' + d[1]).join('\n');
      try { GM_setClipboard(txt); t.textContent = 'Copiado ✓'; } catch (err) { t.textContent = 'Não deu para copiar'; }
      setTimeout(render, 1500); return;
    }
    if (t.id === 'cf-new') { list = []; idx = 0; set(K.list, list); set(K.idx, 0); current = null; render(); return; }
  });
  box.addEventListener('change', (e) => {
    if (e.target.id === 'cf-limit') { let v = Math.round(+e.target.value) || 40; v = Math.max(5, Math.min(200, v)); limit = v; set(K.limit, v); render(); }
  });

  /* ---------- Instagram ---------- */
  function dialogInput() {
    const dialogs = document.querySelectorAll('div[role="dialog"]');
    for (const d of dialogs) { const i = d.querySelector('input[type="text"], input[placeholder]'); if (i) return i; }
    return null;
  }

  function typeInto(input, value) {
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    input.focus();
    setter.call(input, value);
    input.dispatchEvent(new Event('input', { bubbles: true }));
  }

  function clearHighlight() { clearInterval(waitTimer); if (highlighted) highlighted.classList.remove('cf-target'); highlighted = null; }

  function fill() {
    if (doneToday() >= limit || Date.now() < waitUntil()) { render(); return; }
    const input = dialogInput();
    if (!input) { setHint('Abra seu perfil › <b>seguidores</b> primeiro.'); return; }
    clearHighlight();
    current = list[idx];
    if (!current) { render(); return; }
    typeInto(input, current);
    setHint('Procurando @' + current + '…');
    findRemove(input.closest('div[role="dialog"]'), current, Date.now());
  }

  function locate(user) {
    const dialog = dialogInput() && dialogInput().closest('div[role="dialog"]');
    if (!dialog) return null;
    const btns = Array.from(dialog.querySelectorAll('button, div[role="button"]')).filter(b => REMOVE_RE.test((b.textContent || '').trim()));
    for (const b of btns) {
      // sobe até a linha que contém o nome
      let row = b.parentElement;
      for (let i = 0; i < 8 && row; i++, row = row.parentElement) {
        const names = Array.from(row.querySelectorAll('a, span')).map(x => (x.textContent || '').trim().toLowerCase());
        if (names.includes(user)) return b;
      }
    }
    return null;
  }

  // O Instagram redesenha a lista depois da busca, então o destaque é reaplicado sempre que some.
  function findRemove(dialog, user, started) {
    clearInterval(waitTimer);
    waitTimer = setInterval(() => {
      if (current !== user) { clearInterval(waitTimer); return; }
      if (highlighted && highlighted.isConnected) return;
      const b = locate(user);
      if (b) {
        const first = !highlighted;
        highlighted = b; b.classList.add('cf-target');
        if (first) { b.scrollIntoView({ block: 'center' }); setHint('Clique no <b>Remover</b> contornado em vermelho e confirme.'); }
      } else if (!highlighted && Date.now() - started > 6000) {
        setHint('@' + user + ' não aparece nos seus seguidores (talvez já saiu). Toque em <b>Pular</b>.');
      }
    }, 300);
  }

  function advance() {
    clearHighlight(); current = null;
    idx = Math.min(idx + 1, list.length); set(K.idx, idx); render();
  }

  // Detecta quando VOCÊ confirma a remoção (o segundo "Remover", na caixinha de confirmação).
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('button, div[role="button"]');
    if (!b || box.contains(b) || !current) return;
    if (!REMOVE_RE.test((b.textContent || '').trim())) return;
    const dlg = b.closest('div[role="dialog"]');
    if (!dlg || dlg.querySelector('input[type="text"], input[placeholder]')) return; // clique na lista, não na confirmação
    done.push([current, today(), Date.now()]); set(K.done, done);
    nextAt = Date.now() + PAUSE_MIN + Math.random() * (PAUSE_MAX - PAUSE_MIN); set(K.next, nextAt);
    autoFill = true;
    advance();
  }, true);

  // Relógio: mostra a contagem regressiva e preenche o próximo quando a pausa acaba.
  let wasWaiting = false;
  setInterval(() => {
    const wait = waitUntil() - Date.now();
    const el = box.querySelector('#cf-count');
    if (wait > 0) {
      wasWaiting = true;
      if (el) el.textContent = 'em ' + Math.ceil(wait / 1000) + 's';
      return;
    }
    if (wasWaiting) { wasWaiting = false; render(); }
    if (autoFill && !current && idx < list.length && doneToday() < limit && dialogInput()) { autoFill = false; fill(); }
  }, 500);

  // mantém a dica atualizada quando a janelinha de seguidores abre ou fecha
  let lastHas = null;
  setInterval(() => { const has = !!dialogInput(); if (has !== lastHas) { lastHas = has; render(); } }, 1000);

  document.body.appendChild(box);
  render();
})();
