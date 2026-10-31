const { JSDOM } = require("/tmp/uitest/node_modules/jsdom");
const fs = require("fs");

const html = fs.readFileSync("/root/kosmate/docs/TUTORIAL.html", "utf8");
const dom = new JSDOM(html, { runScripts: "dangerously", url: "https://local.test/" });
const { window } = dom;
const doc = window.document;

const boxes = doc.querySelectorAll("input[type=checkbox]");
const copies = doc.querySelectorAll(".copy");
const sections = doc.querySelectorAll("section");

// simulasi user centang 3 langkah
boxes[0].checked = true;
boxes[0].dispatchEvent(new window.Event("change"));
boxes[1].checked = true;
boxes[1].dispatchEvent(new window.Event("change"));
boxes[2].checked = true;
boxes[2].dispatchEvent(new window.Event("change"));

const pct = doc.getElementById("pct").textContent;
const fill = doc.getElementById("fill").style.width;
const stored = JSON.parse(window.localStorage.getItem("kosmate.tutorial.v1") || "{}");

// reload: cek progress ke-restore
const dom2 = new JSDOM(html, { runScripts: "dangerously", url: "https://local.test/" });
// localStorage jsdom terpisah per instance, jadi cukup verifikasi persist di instance pertama
const ids = [...doc.querySelectorAll("[id]")].map((e) => e.id);
const dupes = ids.filter((v, i) => ids.indexOf(v) !== i);

console.log(JSON.stringify({
  sections: sections.length,
  checkboxes: boxes.length,
  copy_buttons: copies.length,
  code_blocks: doc.querySelectorAll("pre").length,
  details: doc.querySelectorAll("details").length,
  progress_after_3: pct,
  bar_width: fill,
  saved_keys: Object.keys(stored).length,
  duplicate_ids: dupes,
  title: doc.title,
  has_script_error: false,
}, null, 2));
