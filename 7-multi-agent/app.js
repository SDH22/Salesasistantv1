const API = 'http://localhost:8000';
const APP = 'manager';
const USER = 'user';
let SESSION_ID = null;
let isThinking = false;
let _welcomeHTML = '';
let pendingLookup = null; // 'invoice' | 'delivery' | null

// ── Session ──────────────────────────────────────────────────────────
async function initSession() {
  try {
    const res = await fetch(`${API}/apps/${APP}/users/${USER}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const data = await res.json();
    SESSION_ID = data.id;
    document.getElementById('statusDot').textContent = 'Agent Online';
  } catch (e) {
    document.getElementById('statusDot').textContent = 'Connecting...';
    showToast('Cannot connect to agent. Is the ADK server running?');
  }
}

function newSession() {
  SESSION_ID = null;
  pendingLookup = null;
  document.getElementById('messages').innerHTML = '';
  document.getElementById('messages').appendChild(buildWelcome());
  const input = document.getElementById('input');
  input.value = '';
  autoResize(input);
  initSession();
}

function buildWelcome() {
  const div = document.createElement('div');
  div.className = 'welcome'; div.id = 'welcome';
  div.innerHTML = _welcomeHTML;
  return div;
}

// ── Send ─────────────────────────────────────────────────────────────
async function sendMessage() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text || isThinking) return;

  // ── Intercept pending Tax Invoice / Delivery Note lookup ──────────────
  if (pendingLookup) {
    const { po, cc } = parsePOandCode(text);
    const welcome = document.getElementById('welcome');
    if (welcome) welcome.remove();
    addMessage('user', text);
    input.value = ''; autoResize(input);

    if (!po || !cc) {
      pendingLookup = null;
      addMessage('agent', '> ⚠️ Couldn\'t read a valid PO Number and Customer Code from that.\n> Click **🧾 Tax Invoice** or **🚚 Delivery Note** again and enter: *PO-2024-001, ALM001*');
      return;
    }

    const typing = addTyping();
    isThinking = true;
    document.getElementById('sendBtn').disabled = true;

    try {
      const reply = await executeLookup(pendingLookup, po, cc);
      typing.remove();
      addMessage('agent', reply);
    } catch (e) {
      typing.remove();
      addMessage('agent', '⚠️ Lookup failed. Please check your connection or contact **sales@steelwood.ae**');
    }

    pendingLookup = null;
    isThinking = false;
    document.getElementById('sendBtn').disabled = false;
    return;
  }
  // ─────────────────────────────────────────────────────────────────────

  const welcome = document.getElementById('welcome');
  if (welcome) welcome.remove();

  addMessage('user', text);
  input.value = ''; autoResize(input);

  const typing = addTyping();
  isThinking = true;
  document.getElementById('sendBtn').disabled = true;

  try {
    const res = await fetch(`${API}/run_sse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        app_name: APP,
        user_id: USER,
        session_id: SESSION_ID,
        new_message: { role: 'user', parts: [{ text }] },
        streaming: false
      })
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let reply = '';
    let msgEl = null;
    let buffer = '';
    const container = document.getElementById('messages');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.content?.parts) {
            for (const part of data.content.parts) {
              if (part.text && data.content.role === 'model') {
                if (!msgEl) {
                  typing.remove();
                  reply = part.text;
                  msgEl = addMessage('agent', reply);
                } else {
                  reply += part.text;
                  msgEl.querySelector('.msg-bubble').innerHTML = parseMarkdown(reply);
                  container.scrollTop = container.scrollHeight;
                }
              }
            }
          }
        } catch(e) {}
      }
    }

    if (!msgEl) {
      typing.remove();
      addMessage('agent', reply || '⚠️ No response received. Please try again.');
    }

  } catch (e) {
    typing.remove();
    addMessage('agent', '⚠️ Connection error. Please check the ADK server.');
  }

  isThinking = false;
  document.getElementById('sendBtn').disabled = false;
}

function sendSuggestion(text) {
  document.getElementById('input').value = text;
  sendMessage();
}

// ── Direct Invoice / Delivery Note lookup (bypasses LLM) ─────────────
function initLookup(type) {
  const welcome = document.getElementById('welcome');
  if (welcome) welcome.remove();
  pendingLookup = type;
  const label = type === 'invoice' ? '🧾 Tax Invoice' : '🚚 Delivery Note';
  addMessage('agent', `## ${label} Lookup\nPlease provide your **PO Number** and **Customer Code**.\n\n*Format: PO-2024-001, ALM001*`);
  if (window.innerWidth <= 900) closeSidebar();
  document.getElementById('input').focus();
}

function parsePOandCode(text) {
  const up = text.toUpperCase().replace(/[^A-Z0-9\-\s,]/g, ' ');
  const poMatch = up.match(/PO[-\s]?\d{4}[-\s]?\d{3,}/);
  const po = poMatch ? poMatch[0].replace(/\s/g, '-').replace(/--+/g, '-') : null;
  const tokens = up.split(/[\s,;:]+/).filter(t => t.length >= 3 && t !== po);
  const cc = tokens.find(t => /^[A-Z]{2,4}\d{2,4}$/.test(t)) || null;
  return { po, cc };
}

async function executeLookup(type, po, cc) {
  const endpoint = type === 'invoice' ? '/lookup/invoice' : '/lookup/delivery';
  const res = await fetch(`${API}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ po_number: po, customer_code: cc })
  });
  const data = await res.json();

  if (data.status === 'not_found') {
    return `> ❌ No record found for PO **${po}**.\n> Please verify the PO number or contact **sales@steelwood.ae**`;
  }
  if (data.status === 'mismatch') {
    return `> ⚠️ **Customer Code mismatch** for PO **${po}**.\n> Please verify your Customer Code or contact **sales@steelwood.ae**`;
  }

  if (type === 'invoice') {
    return `## 🧾 Tax Invoice — ${data.invoice_number}\n| | |\n|--|--|\n| **PO Number** | ${data.po_number} |\n| **Customer Code** | ${data.customer_code} |\n| **Customer** | ${data.customer} |\n| **Date** | ${data.date} |\n| **Items** | ${data.items} |\n| **Amount** | ${data.amount_aed} |\n| **Status** | ${data.status === 'Paid' ? '✅' : '🕐'} ${data.status} |\n\n> 📧 For a PDF copy: **sales@steelwood.ae**`;
  } else {
    return `## 🚚 Delivery Note — ${data.dn_number}\n| | |\n|--|--|\n| **PO Number** | ${data.po_number} |\n| **Customer Code** | ${data.customer_code} |\n| **Customer** | ${data.customer} |\n| **Delivery Date** | ${data.delivery_date} |\n| **Delivered To** | ${data.delivered_to} |\n| **Items** | ${data.items} |\n| **Driver** | ${data.driver} |\n| **Vehicle** | ${data.vehicle} |\n| **Status** | ✅ ${data.status} |\n\n> 📧 For a signed copy: **sales@steelwood.ae**`;
  }
}

function promptInput(prefill) {
  const welcome = document.getElementById('welcome');
  if (welcome) welcome.remove();
  const input = document.getElementById('input');
  input.value = prefill;
  autoResize(input);
  input.focus();
  input.setSelectionRange(input.value.length, input.value.length);
  if (window.innerWidth <= 900) closeSidebar();
}

// ── UI helpers ───────────────────────────────────────────────────────
function addMessage(role, text) {
  const container = document.getElementById('messages');
  const msg = document.createElement('div');
  msg.className = `msg ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'agent' ? '🌲' : '👤';

  const body = document.createElement('div');
  body.className = 'msg-body';

  const name = document.createElement('div');
  name.className = 'msg-name';
  name.textContent = role === 'agent' ? 'Steel Wood AI' : 'You';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = parseMarkdown(text);

  body.appendChild(name);
  body.appendChild(bubble);
  msg.appendChild(avatar);
  msg.appendChild(body);
  container.appendChild(msg);
  container.scrollTop = container.scrollHeight;
  return msg;
}

function addTyping() {
  const container = document.getElementById('messages');
  const msg = document.createElement('div');
  msg.className = 'msg agent';
  msg.innerHTML = `
    <div class="msg-avatar">🌲</div>
    <div class="msg-body">
      <div class="msg-name">Steel Wood AI</div>
      <div class="msg-bubble">
        <div class="typing"><span></span><span></span><span></span></div>
      </div>
    </div>`;
  container.appendChild(msg);
  container.scrollTop = container.scrollHeight;
  return msg;
}

// ── Markdown parser ──────────────────────────────────────────────────
function parseMarkdown(text) {
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3 style="font-size:13px;font-weight:500;color:var(--cyan);margin:8px 0 4px">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/(\|.+\|\n)(\|[-| :]+\|\n)((?:\|.+\|\n?)*)/g, (_, head, sep, body) => {
      const headers = head.trim().split('|').filter(c => c.trim()).map(c => `<th>${c.trim()}</th>`).join('');
      const rows = body.trim().split('\n').filter(Boolean).map(row => {
        const cells = row.trim().split('|').filter(c => c !== '').map(c => `<td>${c.trim()}</td>`).join('');
        return `<tr>${cells}</tr>`;
      }).join('');
      return `<table><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>`;
    })
    .replace(/^---$/gm, '<hr style="border:none;border-top:1px solid rgba(78,205,196,0.12);margin:10px 0">')
    .replace(/^[-•] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
    .replace(/\n\n/g, '</p><p style="margin-top:8px">')
    .replace(/\n/g, '<br>');
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 140) + 'px';
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.style.display = 'block';
  setTimeout(() => { t.style.display = 'none'; }, 4000);
}

// ── Chipboard Accordion ───────────────────────────────────────────────
const CATEGORIES = [
  { id: 'cat-fire',     label: 'Fire Rated',        thicknesses: ['9mm','12mm','18mm','44mm','56mm','62mm'] },
  { id: 'cat-nonfr',    label: 'Non Fire Rated',     thicknesses: ['9mm','12mm','18mm','25mm','33mm','38mm','44mm','56mm','62mm'] },
  { id: 'cat-moist',    label: 'Moisture Rated',     thicknesses: ['9mm','12mm','18mm','44mm'] },
  { id: 'cat-acoustic', label: 'Acoustic Chipboard', thicknesses: ['44mm','56mm','62mm'] },
];

const DOCS = [
  { icon: '📄', label: 'TDS',          prompt: t => `Share the Technical Data Sheet (TDS) for ${t}` },
  { icon: '🧪', label: 'Test Reports', prompt: t => `Show test reports for ${t}` },
];

function buildAccordion() {
  CATEGORIES.forEach(cat => {
    const container = document.getElementById(cat.id);
    if (!container) return;
    cat.thicknesses.forEach(thick => {
      const thickId = `${cat.id}-${thick}`;

      const th = document.createElement('div');
      th.className = 'thick-header';
      th.innerHTML = `<span>${thick}</span><span class="thick-arrow">▶</span>`;
      th.onclick = () => toggleThick(th);

      const dl = document.createElement('div');
      dl.className = 'doc-list';
      dl.id = thickId;

      DOCS.forEach(doc => {
        const fullLabel = `${cat.label} Chipboard ${thick}`;
        const link = document.createElement('div');
        link.className = 'doc-link';
        link.innerHTML = `<span class="doc-dot"></span>${doc.icon} ${doc.label}`;
        link.onclick = () => { sendSuggestion(doc.prompt(fullLabel)); };
        dl.appendChild(link);
      });

      container.appendChild(th);
      container.appendChild(dl);
    });
  });
}

function toggleCat(header) {
  header.classList.toggle('open');
  let el = header.nextElementSibling;
  while (el && !el.classList.contains('cat-body')) el = el.nextElementSibling;
  if (el) el.classList.toggle('open');
}

function toggleThick(header) {
  header.classList.toggle('open');
  const dl = header.nextElementSibling;
  if (dl && dl.classList.contains('doc-list')) dl.classList.toggle('open');
}

function openAllAccordions() {
  document.querySelectorAll('.cat-header').forEach(h => h.classList.add('open'));
  document.querySelectorAll('.cat-body').forEach(b => b.classList.add('open'));
}

// ── Sidebar (mobile) ─────────────────────────────────────────────────
function openSidebar() {
  document.getElementById('sidebar').classList.add('open');
  document.getElementById('sidebarOverlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebarOverlay').classList.remove('active');
  document.body.style.overflow = '';
}

// ── Init ─────────────────────────────────────────────────────────────
buildAccordion();
openAllAccordions();

document.querySelectorAll('.doc-link').forEach(el => {
  el.addEventListener('click', () => { if (window.innerWidth <= 900) closeSidebar(); });
});

document.querySelectorAll('.product-chip, .quick-btn').forEach(el => {
  el.addEventListener('click', () => { if (window.innerWidth <= 900) closeSidebar(); });
});

// Swipe left to close sidebar on mobile
let touchStartX = 0;
document.getElementById('sidebar').addEventListener('touchstart', e => {
  touchStartX = e.touches[0].clientX;
}, { passive: true });
document.getElementById('sidebar').addEventListener('touchend', e => {
  if (touchStartX - e.changedTouches[0].clientX > 60) closeSidebar();
}, { passive: true });

_welcomeHTML = document.getElementById('welcome').innerHTML;
initSession();
