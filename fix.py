#!/usr/bin/env python3
"""
EESI Ops — index.html combined auto-fix script.
Applies ALL fixes: duplicate cleanup, missing functions,
PWA head, mobile CSS, mobile JS, service worker, and more.

Usage:
    python fix.py                          # fixes index.html in place
    python fix.py input.html               # fixes input.html in place
    python fix.py "index (2).html" out.html # reads input, writes out
"""

import sys, os, re

SRC = sys.argv[1] if len(sys.argv) > 1 else "index.html"
DST = sys.argv[2] if len(sys.argv) > 2 else SRC

if not os.path.exists(SRC):
    print(f"ERROR: Source file not found: {SRC}")
    print(f'Usage: python fix.py [input.html] [output.html]')
    sys.exit(1)

try:
    with open(SRC, "r", encoding="utf-8") as f:
        html = f.read()
except UnicodeDecodeError:
    with open(SRC, "r", encoding="latin-1") as f:
        html = f.read()
    print("WARNING: file wasn't UTF-8, read as latin-1")

original_len = len(html)
applied, skipped = [], []

# ============================================================
# FIX 1: Remove duplicate SVG apple-touch-icon
# ============================================================
fix1_re = re.compile(r'<link rel="apple-touch-icon" href="data:image/svg\+xml,[^"]*">\s*\n')
new_html, n = fix1_re.subn("", html, count=1)
if n == 1:
    html = new_html
    applied.append("Removed duplicate apple-touch-icon (SVG data-URI)")
else:
    skipped.append("Fix 1: apple-touch-icon SVG line not found")

# ============================================================
# FIX A: Add PWA head block (manifest + apple meta tags + PNG icon)
# ============================================================
PWA_BLOCK = (
    '<link rel="manifest" href="./manifest.webmanifest">\n'
    '<link rel="apple-touch-icon" href="./icons/icon-192.png">\n'
    '<meta name="apple-mobile-web-app-capable" content="yes">\n'
    '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\n'
    '<meta name="apple-mobile-web-app-title" content="EESI Ops">\n'
)

if 'rel="manifest"' in html:
    skipped.append("Fix A: PWA manifest already present")
else:
    fav_pat = re.compile(r'(<link rel="icon" type="image/svg\+xml"[^>]*>)\s*\n')
    new_html, n2 = fav_pat.subn(r'\1\n' + PWA_BLOCK, html, count=1)
    if n2 > 0:
        html = new_html
        applied.append("Added PWA head block (manifest + apple meta + PNG icon)")
    else:
        # Fallback: insert PWA block right before </head>
        if '</head>' in html:
            html = html.replace('</head>', PWA_BLOCK + '</head>', 1)
            applied.append("Added PWA head block (before </head>)")
        else:
            skipped.append("Fix A: no anchor point for PWA block")

# ============================================================
# FIX A2: Service worker registration
# ============================================================
SW_BLOCK = (
    '<script>\n'
    '  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {\n'
    '    window.addEventListener("load", () => {\n'
    '      navigator.serviceWorker.register("./sw.js").catch(err => {\n'
    '        console.warn("Service worker registration failed:", err);\n'
    '      });\n'
    '    });\n'
    '  }\n'
    '</script>\n'
)

if 'serviceWorker.register' in html:
    skipped.append("Fix A2: service worker already registered")
elif '</body>' in html:
    html = html.replace('</body>', SW_BLOCK + '</body>', 1)
    applied.append("Added service worker registration")
else:
    skipped.append("Fix A2: no </body> found")

# ============================================================
# FIX B: Remove #activeChat CSS height override
# ============================================================
FIX_B_OLD = '''#activeChat {
  height: calc(100dvh - 152px - env(safe-area-inset-bottom));
  max-height: calc(100dvh - 152px - env(safe-area-inset-bottom));
}
'''
if FIX_B_OLD in html:
    html = html.replace(FIX_B_OLD, '', 1)
    applied.append("Removed #activeChat CSS height override")
else:
    skipped.append("Fix B: #activeChat CSS block not found (already removed?)")

# ============================================================
# FIX 2: Remove duplicate settings sound buttons
# ============================================================
fix2_old = '''  <label><input id="settingVibration" type="checkbox"> Vibration</label>
  <div style="display:flex;gap:8px;margin:8px 0">
  <button id="builtInSoundChoice" class="btn" type="button">Built-in sounds</button>
  <button id="customSoundChoice" class="gray" type="button">Custom ringtone</button>
</div>
'''
fix2_new = '''  <label><input id="settingVibration" type="checkbox"> Vibration</label>
'''
if fix2_old in html:
    html = html.replace(fix2_old, fix2_new, 1)
    applied.append("Removed duplicate settings sound buttons")
else:
    # Try more flexible pattern
    flex_pat = re.compile(
        r'(<label><input id="settingVibration" type="checkbox">\s*Vibration</label>\s*)\n'
        r'<div style="display:flex;gap:8px;margin:8px 0">\s*\n'
        r'\s*<button id="builtInSoundChoice"[^>]*>Built-in sounds</button>\s*\n'
        r'\s*<button id="customSoundChoice"[^>]*>Custom ringtone</button>\s*\n'
        r'</div>\s*\n'
    )
    new_html, n = flex_pat.subn(r'\1\n', html, count=1)
    if n == 1:
        html = new_html
        applied.append("Removed duplicate settings sound buttons (flexible)")
    else:
        skipped.append("Fix 2: duplicate settings buttons not found")

# ============================================================
# FIX 3: Insert 9 missing functions + error handlers
# ============================================================
MISSING_FUNCTIONS = r'''  /* ============================================================
     MISSING FUNCTIONS — added to fix silent ReferenceErrors
     ============================================================ */

  async function changePassword() {
    const { data: { user } } = await client.auth.getUser();
    if (!user) return toast("Sign in first.");
    const newPassword = prompt("Enter your new password (min 8 characters):");
    if (!newPassword || newPassword.length < 8) {
      return toast("Password must be at least 8 characters.");
    }
    const { error } = await client.auth.updateUser({ password: newPassword });
    if (error) return toast("Could not update password: " + error.message);
    toast("Password updated successfully.");
  }
  window.changePassword = changePassword;

  function openNotifySheet(threadId) {
    const pref = getPref(threadId);
    const current = pref.mute || "off";
    openSheet(
      '<h2>Notifications &amp; sounds</h2>' +
      '<p class="muted">Choose what happens when new messages arrive in this chat.</p>' +
      [
        ["off",      "🔔 On (default)"],
        ["3600000",  "🔕 Mute for 1 hour"],
        ["28800000", "🔕 Mute for 8 hours"],
        ["forever",  "🔕 Mute forever"]
      ].map(([value, label]) =>
        '<button class="sheet-btn' + (current === value ? ' primary' : '') + '" ' +
        'type="button" data-act="chat-set-mute" data-id="' + esc(threadId) +
        '" data-value="' + value + '">' + esc(label) + '</button>'
      ).join("") +
      sheetClose()
    );
  }
  window.openNotifySheet = openNotifySheet;

  function setMuteChoice(threadId, choice) {
    const muteValue = choice === "off"
      ? null
      : (choice === "forever" ? "forever" : Date.now() + Number(choice));
    setPref(threadId, { mute: muteValue });
    refreshChatViews();
    closeSheet();
    toast(choice === "off" ? "Notifications turned on." : "Chat muted.");
  }
  window.setMuteChoice = setMuteChoice;

  async function openGroupWith(otherUserId) {
    closeSheet();
    const other = profileOf(otherUserId);
    const name = prompt(
      "Group name:",
      "Group with " + (other?.full_name?.split(" ")[0] || "member")
    );
    if (!name) return;
    $("groupName").value = name;
    openCompose();
    showGroupForm();
    const checkbox = [...$("groupChoices").querySelectorAll("input")]
      .find(cb => cb.value === otherUserId);
    if (checkbox) checkbox.checked = true;
  }
  window.openGroupWith = openGroupWith;

  function shareContact(userId) {
    const p = profileOf(userId);
    if (!p) return toast("Profile not found.");
    const vcard = [
      "BEGIN:VCARD", "VERSION:3.0",
      "FN:" + (p.full_name || ""),
      "TEL:" + (p.phone || ""),
      "EMAIL:" + (p.email || ""),
      "ORG:EESI Elevators", "END:VCARD"
    ].join("\n");
    const blob = new Blob([vcard], { type: "text/vcard" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = (p.full_name || "contact").replace(/\s+/g, "_") + ".vcf";
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 3000);
    toast("Contact card shared.");
  }
  window.shareContact = shareContact;

  function openMembersSheet(threadId) {
    const t = state.threads.find(x => x.id === threadId);
    if (!t) return;
    const members = threadMembers(t);
    openSheet(
      '<h2>Group members (' + members.length + ')</h2>' +
      members.map(m => {
        const p = profileOf(m.user_id);
        return '<div class="media-item">' + face(p) +
          '<span class="media-name"><b>' +
          esc(p?.full_name || "Member") + '</b>' +
          (m.user_id === state.userId ? ' <span class="muted">(you)</span>' : '') +
          '</span></div>';
      }).join("") + sheetClose()
    );
  }
  window.openMembersSheet = openMembersSheet;

  function openAddSheet(threadId) {
    const t = state.threads.find(x => x.id === threadId);
    if (!t) return;
    const existing = new Set(threadMembers(t).map(m => m.user_id));
    const candidates = state.profiles.filter(p => !existing.has(p.user_id));
    openSheet(
      '<h2>Add people</h2>' +
      '<div id="addMemberChoices">' +
      (candidates.map(p =>
        '<label style="display:flex;gap:8px;align-items:center;margin:6px 0">' +
        '<input type="checkbox" value="' + esc(p.user_id) +
        '" style="width:auto"> ' + esc(p.full_name || p.email) + '</label>'
      ).join("") || '<p class="muted">Everyone is already in this group.</p>') +
      '</div>' +
      '<div class="sheet-actions">' +
      '<button class="gray" type="button" data-act="close-sheet">Cancel</button>' +
      '<button class="btn" type="button" data-act="chat-add-save" data-id="' +
      esc(threadId) + '">Add selected</button></div>'
    );
  }
  window.openAddSheet = openAddSheet;

  async function addMembers(threadId) {
    const ids = [...document.querySelectorAll("#addMemberChoices input:checked")]
      .map(cb => cb.value);
    if (!ids.length) return toast("Select at least one person.");
    const { error } = await client.from("thread_members").insert(
      ids.map(user_id => ({ thread_id: threadId, user_id }))
    );
    if (error) return toast("Could not add members: " + error.message);
    closeSheet();
    await loadThreads();
    toast(ids.length + " member(s) added.");
  }
  window.addMembers = addMembers;

  async function leaveGroup(threadId) {
    if (!confirm("Leave this group? Another member will need to add you back.")) return;
    const { error } = await client.from("thread_members")
      .delete()
      .eq("thread_id", threadId)
      .eq("user_id", state.userId);
    if (error) return toast("Could not leave group: " + error.message);
    closeSheet();
    closeChat();
    await loadThreads();
    toast("You left the group.");
  }
  window.leaveGroup = leaveGroup;

  window.addEventListener("unhandledrejection", event => {
    console.error("[Unhandled promise rejection]", event.reason);
    const msg = event.reason?.message || String(event.reason || "Unknown error");
    if (!/NetworkError|Failed to fetch/i.test(msg)) {
      toast("Something went wrong. Check console for details.");
    }
  });
  window.addEventListener("error", event => {
    console.error("[Uncaught error]", event.error || event.message);
  });

'''

anchor = "  function handleExtraAct(act, id, el) {"
if "MISSING FUNCTIONS — added to fix silent ReferenceErrors" in html:
    skipped.append("Fix 3: missing functions already present")
elif anchor in html:
    html = html.replace(anchor, MISSING_FUNCTIONS + anchor, 1)
    applied.append("Inserted 9 missing functions + 2 global error handlers")
else:
    skipped.append("Fix 3: 'function handleExtraAct' anchor not found")

# ============================================================
# FIX 4: Avatar upload — no base64 fallback
# ============================================================
fix4_old = '''      if (!error) {
        const { data: pub } = client.storage.from("avatars").getPublicUrl(path);
        finalUrl = pub.publicUrl;
      } else {
        finalUrl = await compressImage(file, column === "cover_url" ? 1100 : 400);
      }'''
fix4_new = '''      if (error) {
        return toast("Could not upload picture: " + error.message);
      }
      const { data: pub } = client.storage.from("avatars").getPublicUrl(path);
      finalUrl = pub.publicUrl;'''
if fix4_old in html:
    html = html.replace(fix4_old, fix4_new, 1)
    applied.append("Avatar upload now fails loudly instead of storing base64")
else:
    skipped.append("Fix 4: avatar upload pattern not found")

# ============================================================
# FIX 5: Report photo size limit
# ============================================================
fix5_old = '''    for (const file of files) {
      if (!file.type.startsWith("image/")) {
        throw new Error("Please select image files only.");
      }

      const safeName = file.name.replace(/[^a-zA-Z0-9._-]/g, "_");'''
fix5_new = '''    const MAX_PHOTO_MB = 5;
    for (const file of files) {
      if (!file.type.startsWith("image/")) {
        throw new Error("Please select image files only.");
      }
      if (file.size > MAX_PHOTO_MB * 1024 * 1024) {
        throw new Error("Photo too large — max " + MAX_PHOTO_MB + " MB each.");
      }

      const safeName = file.name.replace(/[^a-zA-Z0-9._-]/g, "_");'''
if "const MAX_PHOTO_MB = 5;" in html:
    skipped.append("Fix 5: photo limit already applied")
elif fix5_old in html:
    html = html.replace(fix5_old, fix5_new, 1)
    applied.append("Report photos limited to 5 MB each")
else:
    skipped.append("Fix 5: report photo loop pattern not found")

# ============================================================
# FIX 6: WebRTC sendTo race condition
# ============================================================
fix6_old = '''  function sendTo(peerId, payload) {
    if (!peerChannels[peerId]) {
      peerChannels[peerId] = client.channel(callTopic(peerId), { config: { broadcast: { self: false } } });
      peerChannels[peerId].subscribe();
    }
    return peerChannels[peerId].send({
      type: "broadcast", event: "call",
      payload: { ...payload, from: state.userId, to: peerId }
    });
  }'''
fix6_new = '''  function sendTo(peerId, payload) {
    if (!peerChannels[peerId]) {
      peerChannels[peerId] = client.channel(callTopic(peerId), { config: { broadcast: { self: false } } });
    }
    const ch = peerChannels[peerId];
    const doSend = () => ch.send({
      type: "broadcast", event: "call",
      payload: { ...payload, from: state.userId, to: peerId }
    });
    if (ch.state === "joined") return doSend();
    return new Promise(resolve => {
      ch.subscribe(status => {
        if (status === "SUBSCRIBED" && ch.state === "joined") resolve(doSend());
      });
    });
  }'''
if 'if (ch.state === "joined") return doSend();' in html:
    skipped.append("Fix 6: signaling fix already applied")
elif fix6_old in html:
    html = html.replace(fix6_old, fix6_new, 1)
    applied.append("WebRTC signaling now waits for channel to be joined")
else:
    skipped.append("Fix 6: sendTo function not found")

# ============================================================
# FIX 7: state object cleanup (remove duplicate keys)
# ============================================================
fix7_old = '''  const state = {
    userId: null, email: null, role: null, profile: null,
    profiles: [], roles: {}, presence: {},
    announcements: [], pending: [], appNotifications: [], approvalNotifications: [],
    leaveRequests: [],
    threads: [], unread: {}, previews: {}, chatFilter: "all", activeThread: null, messages: [],
    sites: [], schedules: [], dtrs: [], notes: [], recs: [],
    reports: [], reportType: "service",
    announcements: [], pending: [],
    threads: [], unread: {}, previews: {}, chatFilter: "all", activeThread: null, messages: [],
    regionFilter: "all", setupIssue: "", booted: false
  };'''
fix7_new = '''  const state = {
    userId: null, email: null, role: null, profile: null,
    profiles: [], roles: {}, presence: {},
    announcements: [], pending: [], appNotifications: [], approvalNotifications: [],
    leaveRequests: [],
    threads: [], unread: {}, previews: {}, chatFilter: "all", activeThread: null, messages: [],
    sites: [], schedules: [], dtrs: [], notes: [], recs: [],
    reports: [], reportType: "service",
    regionFilter: "all", setupIssue: "", booted: false
  };'''
if fix7_old in html:
    html = html.replace(fix7_old, fix7_new, 1)
    applied.append("Removed duplicate keys from state object")
else:
    skipped.append("Fix 7: state object pattern not found")

# ============================================================
# FIX 8: updateAccess duplicate line
# ============================================================
fix8_old = '''    document.querySelectorAll(".manager-only").forEach(el => el.classList.toggle("hidden", !isManager()));
    document.querySelectorAll(".admin-only").forEach(el => el.classList.toggle("hidden", !isAdmin()));
  }'''
fix8_new = '''    document.querySelectorAll(".manager-only").forEach(el => el.classList.toggle("hidden", !isManager()));
  }'''
if fix8_old in html:
    html = html.replace(fix8_old, fix8_new, 1)
    applied.append("Removed duplicate .admin-only line in updateAccess()")
else:
    skipped.append("Fix 8: updateAccess duplicate pattern not found")

# ============================================================
# FIX M1: Mobile CSS enhancements
# ============================================================
MOBILE_CSS = r'''/* ============================================================
   MOBILE NATIVE ENHANCEMENTS
   Makes the app feel like a real phone app
   ============================================================ */

html, body {
  height: 100%;
  overflow-x: hidden;
  overscroll-behavior: none;
  -webkit-overflow-scrolling: touch;
  -webkit-tap-highlight-color: transparent;
  -webkit-touch-callout: none;
}

body {
  padding-top: env(safe-area-inset-top);
  padding-bottom: calc(64px + env(safe-area-inset-bottom));
  min-height: 100dvh;
  text-size-adjust: 100%;
  -webkit-text-size-adjust: 100%;
}

@media (display-mode: standalone) {
  header {
    padding-top: calc(10px + env(safe-area-inset-top));
  }
  body {
    padding-top: 0;
  }
}

.page {
  animation: pageFade 0.18s ease-out;
}

@keyframes pageFade {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}

.page.hidden {
  animation: none;
}

button, .btn, .chip, .tab, .filter, .stat, .tile, .sheet-btn, .msgr-icon, .hbtn {
  min-height: 44px;
  min-width: 44px;
  touch-action: manipulation;
}

.small-btn {
  min-height: 32px;
  min-width: auto;
  padding: 6px 10px;
}

button:not(:disabled),
.clickable,
.person,
.thread-row,
.tile {
  position: relative;
  overflow: hidden;
}

button:not(:disabled)::after,
.thread-row::after {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at center, currentColor 0%, transparent 70%);
  opacity: 0;
  transform: scale(0);
  transition: opacity 0.25s, transform 0.25s;
  pointer-events: none;
}

button:not(:disabled):active::after,
.thread-row:active::after {
  opacity: 0.08;
  transform: scale(2.5);
  transition: 0s;
}

.msgr-list,
.msgr-msgs,
.messages,
#messages,
#chatList,
.sheet,
.person-picker {
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}

::-webkit-scrollbar {
  width: 0;
  height: 0;
  background: transparent;
}

* {
  scrollbar-width: none;
}

nav.bottom {
  height: calc(56px + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

nav.bottom button {
  min-height: 56px;
  font-size: 11px;
  transition: transform 0.15s, color 0.15s;
}

nav.bottom button:active {
  transform: scale(0.92);
}

header {
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.sheet-back {
  animation: sheetBackdrop 0.2s ease-out;
}

.sheet {
  animation: sheetSlide 0.28s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes sheetBackdrop {
  from { background: transparent; }
  to   { background: #0008; }
}

@keyframes sheetSlide {
  from { transform: translateY(100%); }
  to   { transform: translateY(0); }
}

.dialog .card {
  animation: dialogPop 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes dialogPop {
  from { transform: scale(0.9); opacity: 0; }
  to   { transform: scale(1); opacity: 1; }
}

.msgr-row {
  animation: msgIn 0.22s ease-out;
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

header, nav, .msgr-head, .chat-head, .page > h1.title,
.tile, .stat, .chip, .tab, .filter {
  user-select: none;
  -webkit-user-select: none;
}

.msgr-bub, .item, .card p, textarea, input, .bubble {
  user-select: text;
  -webkit-user-select: text;
}

input, select, textarea {
  font-size: 16px !important;
  touch-action: manipulation;
}

#ptr-indicator {
  position: fixed;
  top: env(safe-area-inset-top);
  left: 50%;
  transform: translateX(-50%) translateY(-60px);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--blue);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 18px;
  z-index: 100;
  transition: transform 0.25s, opacity 0.25s;
  opacity: 0;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

#ptr-indicator.active {
  transform: translateX(-50%) translateY(20px);
  opacity: 1;
}

#ptr-indicator.spinning {
  animation: ptrSpin 0.8s linear infinite;
}

@keyframes ptrSpin {
  to { transform: translateX(-50%) translateY(20px) rotate(360deg); }
}

.toast {
  animation: toastIn 0.28s cubic-bezier(0.16, 1, 0.3, 1);
  border-radius: 12px;
  font-weight: 600;
  box-shadow: 0 8px 24px rgba(0,0,0,0.35);
}

@keyframes toastIn {
  from { transform: translateX(-50%) translateY(20px); opacity: 0; }
  to   { transform: translateX(-50%) translateY(0); opacity: 1; }
}

.msgr-bub {
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
  transition: transform 0.1s;
}

.msgr-bub:active {
  transform: scale(0.98);
}

body.modal-open {
  overflow: hidden;
  position: fixed;
  width: 100%;
}

button:disabled {
  opacity: 0.4;
  filter: grayscale(0.3);
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

'''

if 'MOBILE NATIVE ENHANCEMENTS' in html:
    skipped.append("Fix M1: mobile CSS already present")
elif '</style>' in html:
    html = html.replace('</style>', MOBILE_CSS + '</style>', 1)
    applied.append("Added mobile CSS enhancements")
else:
    skipped.append("Fix M1: no </style> found")

# ============================================================
# FIX M2: Mobile gestures JS
# ============================================================
MOBILE_JS = r'''  /* ============================================================
     MOBILE NATIVE GESTURES & FEEL
     ============================================================ */

  let lastTouchEnd = 0;
  document.addEventListener("touchend", (e) => {
    const now = Date.now();
    if (now - lastTouchEnd <= 300) e.preventDefault();
    lastTouchEnd = now;
  }, { passive: false });

  function haptic(ms = 10) {
    if ("vibrate" in navigator && localStorage.getItem("eesi-vibration") === "on") {
      try { navigator.vibrate(ms); } catch (e) {}
    }
  }

  document.addEventListener("click", (e) => {
    const t = e.target.closest("button, .thread-row, .person, .tile, .stat");
    if (t && !t.disabled) haptic(8);
  }, { passive: true });

  let ptrStartY = 0;
  let ptrPulling = false;
  let ptrIndicator = null;

  function ensurePtrIndicator() {
    if (!ptrIndicator) {
      ptrIndicator = document.createElement("div");
      ptrIndicator.id = "ptr-indicator";
      ptrIndicator.innerHTML = "↓";
      document.body.appendChild(ptrIndicator);
    }
    return ptrIndicator;
  }

  document.addEventListener("touchstart", (e) => {
    if (window.scrollY === 0) {
      ptrStartY = e.touches[0].clientY;
      ptrPulling = true;
    }
  }, { passive: true });

  document.addEventListener("touchmove", (e) => {
    if (!ptrPulling || window.scrollY > 0) return;
    const dy = e.touches[0].clientY - ptrStartY;
    if (dy > 60) {
      const ind = ensurePtrIndicator();
      ind.classList.add("active");
      ind.innerHTML = dy > 120 ? "↻" : "↓";
    }
  }, { passive: true });

  document.addEventListener("touchend", async (e) => {
    if (!ptrPulling) return;
    const dy = (e.changedTouches[0]?.clientY || 0) - ptrStartY;
    ptrPulling = false;
    if (dy > 120) {
      const ind = ensurePtrIndicator();
      ind.classList.add("active", "spinning");
      haptic(20);
      try {
        if (typeof reloadEverything === "function") await reloadEverything();
      } catch (err) {}
      setTimeout(() => {
        ind.classList.remove("active", "spinning");
      }, 400);
    } else if (ptrIndicator) {
      ptrIndicator.classList.remove("active");
    }
  }, { passive: true });

  let swStartX = 0;
  let swStartY = 0;
  let swTracking = false;

  document.addEventListener("touchstart", (e) => {
    swStartX = e.touches[0].clientX;
    swStartY = e.touches[0].clientY;
    swTracking = swStartX < 40;
  }, { passive: true });

  document.addEventListener("touchend", (e) => {
    if (!swTracking) return;
    const dx = (e.changedTouches[0]?.clientX || 0) - swStartX;
    const dy = Math.abs((e.changedTouches[0]?.clientY || 0) - swStartY);
    if (dx > 80 && dy < 50) {
      haptic(10);
      if (typeof closeChat === "function" && !document.getElementById("activeChat").classList.contains("hidden")) {
        closeChat();
      } else if (typeof closeSheet === "function" && !document.getElementById("sheet").classList.contains("hidden")) {
        closeSheet();
      } else if (typeof closeCompose === "function" && !document.getElementById("chatCompose").classList.contains("hidden")) {
        closeCompose();
      } else if (typeof closeChatInfo === "function" && !document.getElementById("chatInfo").classList.contains("hidden")) {
        closeChatInfo();
      } else if (typeof goBack === "function") {
        goBack();
      }
    }
    swTracking = false;
  }, { passive: true });

  document.addEventListener("focusin", (e) => {
    const t = e.target;
    if (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT") {
      setTimeout(() => {
        t.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 250);
    }
  });

  function setAppVh() {
    document.documentElement.style.setProperty("--app-vh", window.innerHeight * 0.01 + "px");
  }
  setAppVh();
  window.addEventListener("resize", setAppVh);
  window.addEventListener("orientationchange", () => setTimeout(setAppVh, 100));

'''

if 'MOBILE NATIVE GESTURES' in html:
    skipped.append("Fix M2: mobile gestures JS already present")
elif '  applyDisplaySettings();\n  start();' in html:
    html = html.replace(
        '  applyDisplaySettings();\n  start();',
        '  applyDisplaySettings();\n' + MOBILE_JS + '  start();',
        1
    )
    applied.append("Added mobile gestures JS")
else:
    skipped.append("Fix M2: anchor (applyDisplaySettings + start) not found")

# ============================================================
# Write output + summary
# ============================================================
with open(DST, "w", encoding="utf-8") as f:
    f.write(html)

print()
print("=" * 62)
print("  EESI Ops — combined auto-fix results")
print("=" * 62)
for line in applied:
    print(f"  [OK]   {line}")
for line in skipped:
    print(f"  [--]   {line}")
print()
print(f"  Source: {SRC}  ({original_len:,} bytes)")
print(f"  Output: {DST}  ({len(html):,} bytes)")
print()
print("  Upload the output to GitHub. Netlify will auto-deploy.")