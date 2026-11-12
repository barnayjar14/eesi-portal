#!/usr/bin/env python3
"""
EESI Ops — index.html auto-fix script.
Reads "index (2).html", applies 8 fixes, writes "index.html".
Usage:  python fix.py "index (2).html" index.html
"""

import sys, os, re

SRC = sys.argv[1] if len(sys.argv) > 1 else "index (2).html"
DST = sys.argv[2] if len(sys.argv) > 2 else "index.html"

if not os.path.exists(SRC):
    print(f"ERROR: Source file not found: {SRC}")
    print(f'Usage: python fix.py "index (2).html" index.html')
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

# ---------------- Fix 1: duplicate apple-touch-icon ----------------
fix1_re = re.compile(r'<link rel="apple-touch-icon" href="data:image/svg\+xml,[^"]*">\s*\n')
new_html, n = fix1_re.subn("", html, count=1)
if n == 1:
    html = new_html
    applied.append("Removed duplicate apple-touch-icon (SVG data-URI)")
else:
    skipped.append("Fix 1: apple-touch-icon SVG line not found (already removed?)")

# ---------------- Fix 2: duplicate settings sound buttons ----------------
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
    skipped.append("Fix 2: duplicate settings buttons not found (already removed?)")

# ---------------- Fix 3: insert 9 missing functions + error handlers ----------------
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
    skipped.append("Fix 3: missing functions already present (skipping)")
elif anchor in html:
    html = html.replace(anchor, MISSING_FUNCTIONS + anchor, 1)
    applied.append("Inserted 9 missing functions + 2 global error handlers")
else:
    skipped.append("Fix 3: 'function handleExtraAct' anchor not found")

# ---------------- Fix 4: avatar upload base64 removal ----------------
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

# ---------------- Fix 5: report photo size limit ----------------
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

# ---------------- Fix 6: WebRTC sendTo race ----------------
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

# ---------------- Fix 7: state object cleanup ----------------
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

# ---------------- Fix 8: updateAccess duplicate line ----------------
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

# ---------------- Write + summary ----------------
with open(DST, "w", encoding="utf-8") as f:
    f.write(html)

print()
print("=" * 62)
print("  EESI Ops — auto-fix results")
print("=" * 62)
for line in applied:
    print(f"  [OK]   {line}")
for line in skipped:
    print(f"  [!]    {line}")
print()
print(f"  Source: {SRC}  ({original_len:,} bytes)")
print(f"  Output: {DST}  ({len(html):,} bytes)")
print()
print("  Done. Upload 'index.html' to GitHub.")
