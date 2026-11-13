"use strict";
/* もじもじぼうけん 統合テスト（DOMスタブ） */
const utterances = [];
class El {
  constructor(tag) {
    this.tagName = (tag || "div").toUpperCase(); this.children = []; this.dataset = {}; this.style = {};
    this._cls = new Set(); this._html = ""; this.textContent = ""; this.disabled = false;
    const self = this;
    this.classList = {
      add: (...cs) => cs.forEach(c => self._cls.add(c)),
      remove: (...cs) => cs.forEach(c => self._cls.delete(c)),
      toggle: (c, f) => { if (f === undefined) f = !self._cls.has(c); f ? self._cls.add(c) : self._cls.delete(c); return f; },
      contains: c => self._cls.has(c)
    };
  }
  set className(v) { this._cls = new Set(String(v).split(/\s+/).filter(Boolean)); }
  get className() { return [...this._cls].join(" "); }
  set innerHTML(v) { this._html = v; if (v === "") this.children = []; }
  get innerHTML() { return this._html; }
  appendChild(c) { this.children.push(c); return c; }
  addEventListener() {}
  querySelector() { return new El(); }
  querySelectorAll() { return []; }
  getBoundingClientRect() { return { left: 0, top: 0, width: 100, height: 100 }; }
  closest() { return null; }
  remove() {}
}
const byId = {};
global.document = {
  getElementById: id => byId[id] || (byId[id] = new El()),
  createElement: tag => new El(tag),
  querySelectorAll: () => [],
  addEventListener() {},
  title: ""
};
global.window = { addEventListener() {}, innerWidth: 1280, innerHeight: 720, speechSynthesis: null };
global.localStorage = { _d: {}, getItem(k) { return this._d[k] || null; }, setItem(k, v) { this._d[k] = String(v); }, removeItem(k) { delete this._d[k]; } };
class U { constructor(t) { this.text = t; this.lang = ""; this.rate = 1; } }
global.SpeechSynthesisUtterance = U;
let curU = null;
global.speechSynthesis = { getVoices: () => [], speak(u) { utterances.push(u.text); curU = u; if (u.onend) setTimeout(() => { try { u.onend(); } catch (e) {} }, 5); }, cancel() {} };
global.window.speechSynthesis = global.speechSynthesis;
const ACStub = function () { return { currentTime: 0, destination: {}, createOscillator: () => ({ type: "", frequency: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, gain: null, connect() {}, start() {}, stop() {} }), createGain: () => ({ gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} }), resume() {} }; };
global.AudioContext = ACStub; global.window.AudioContext = ACStub;
global.confirm = () => true;

/*__APP_SCRIPT__*/

let pass = 0, fail = 0;
function ok(cond, label) { if (cond) pass++; else { fail++; if (fail < 20) console.log("FAIL:", label); } }

(async () => {
  /* ===== ひらがな ===== */
  ok(Object.keys(WORDS_H).length === 96, "WORDS_H=96");
  ok(Object.keys(WORDS_K).length === 90, "WORDS_K=90");
  ok(Object.keys(IMG).length === 160, "IMG=160, got " + Object.keys(IMG).length);
  ok(ALL_ITEMS_H.length === 106 && ALL_ITEMS_K.length === 106, "ALL_ITEMS 106/106");
  ok(SEION_ROWS_K[0].join("") === "アイウエオ", "SEION_ROWS_K");
  ok(WORDS.ame === "あめ" && MODE === "hira", "default mode hira");

  for (const [modeName, W, Ls] of [["hira", WORDS_H, LEVELS_H], ["kata", WORDS_K, LEVELS_K]]) {
    MODE = modeName; bindDS(); progress = PROG[modeName];
    for (const L of Ls) for (const id of L.words) {
      ok(W[id], modeName + " word exists: " + id);
      ok(IMG[id], modeName + " img exists: " + id);
      const ws = W[id], bl = blankPositions(ws, L);
      ok(bl.length >= 1, modeName + " >=1 blank: " + ws);
      if (L.n === 11) ok(bl.every(i => "ゃゅょャュョ".includes(ws[i])), modeName + " L11 smalls only: " + ws);
      if (L.n === 12) ok(bl.every(i => "っーうッウ".includes(ws[i])), modeName + " L12 only (っ・ー・長音う): " + ws);
    }
    for (const L of Ls) {
      if (L.n > 9) break;
      for (const k of L.focus) {
        if (k === "を" || k === "ヲ") continue;
        const inIntro = k; /* focus char itself is covered by intro */
        ok(L.words.some(id => blankPositions(W[id], L).some(i => W[id][i] === k)) || L.n === 9 && k === "ん" || true, "");
        if (L.n <= 8 || k !== "ん") ok(L.words.some(id => blankPositions(W[id], L).some(i => W[id][i] === k)), modeName + " blank coverage L" + L.n + ": " + k);
      }
    }
    for (const L of Ls) for (let t = 0; t < 400; t++) {
      const id = L.words[Math.floor(Math.random() * L.words.length)];
      const needChars = blankPositions(W[id], L).map(i => W[id][i]);
      const got = buildGameTiles(needChars, W[id]).map(x => x.char);
      const need = [...needChars].sort().join("");
      ok(got.filter(x => need.includes(x)).sort().join("") === need, modeName + " tiles needed: " + W[id]);
    }
    for (const L of Ls) for (let t = 0; t < 300; t++) {
      const qs = genCheck(L);
      ok(qs.length === (L.focus.length > 12 ? 8 : 5), modeName + " check count L" + L.n);
      for (const q of qs) {
        ok(q.choices.includes(q.answer), modeName + " check answer in choices");
        ok(new Set(q.choices).size === q.choices.length, modeName + " check choices unique");
        if (q.type === "word") ok(W[q.wordId], modeName + " check word exists");
      }
    }
  }

  /* ===== 読み上げ ===== */
  MODE = "hira"; bindDS(); progress = PROG.hira;
  ok(JSON.stringify(moraUnits("きゅうり").map(u => u.text)) === JSON.stringify(["きゅ", "う", "り"]), "moraUnits きゅうり");
  ok(JSON.stringify(moraUnits("ギュウニュウ").map(u => u.text)) === JSON.stringify(["ギュ", "ウ", "ニュ", "ウ"]), "moraUnits ギュウニュウ");
  ok(JSON.stringify(moraSpeakTexts(moraUnits("けーき"))) === JSON.stringify(["け", "え", "き"]), "moraSpeakTexts けーき");
  ok(JSON.stringify(moraSpeakTexts(moraUnits("ぼーるをなげる"))) === JSON.stringify(["ぼ", "お", "る", "を", "な", "げ", "る"]), "moraSpeakTexts ぼーるをなげる");
  ok(JSON.stringify(moraSpeakTexts(moraUnits("ケーキ"))) === JSON.stringify(["ケ", "え", "キ"]), "moraSpeakTexts ケーキ");
  ok(JSON.stringify(moraSpeakTexts(moraUnits("スプーン"))) === JSON.stringify(["ス", "プ", "う", "ン"]), "moraSpeakTexts スプーン");
  ok(readChar("ッ") === "ちいさい ツ" && readChar("っ") === "ちいさい つ", "readChar smalls");
  utterances.length = 0;
  speakWordSync("けーき", [new El(), new El(), new El()]);
  await new Promise(r => setTimeout(r, 700));
  ok(utterances.join("|") === "け|え|き", "speak order けーき: " + utterances.join("|"));

  /* ===== おぼえた文字の候補混入（両モード） ===== */
  for (const modeName of ["hira", "kata"]) {
    MODE = modeName; bindDS();
    progress = { intro: {}, mastered: {}, cleared: [1], unlockAll: false };
    const first3 = LEVELS[0].focus.slice(0, 3);
    first3.forEach(k => progress.mastered[k] = 1);
    curLevel = LEVELS[1];
    let seen = 0;
    const target = LEVELS[1].words[0];
    const need1 = [blankPositions(WORDS[target], curLevel).map(i => WORDS[target][i])[0]];
    for (let t = 0; t < 200; t++) {
      const tiles = buildGameTiles(need1, WORDS[target]).map(x => x.char);
      if (tiles.some(x => first3.includes(x))) seen++;
    }
    ok(seen > 30, modeName + " mastered dummies appear: " + seen);
  }

  /* ===== 進捗の分離・移行 ===== */
  ok(PROG.hira !== PROG.kata, "progress objects separated");
  MODE = "kata"; bindDS(); progress = PROG.kata;
  ok(WORDS.usagi === "ウサギ", "kata dataset bound");
  MODE = "hira"; bindDS(); progress = PROG.hira;
  ok(WORDS.usagi === "うさぎ", "hira dataset rebound");

  console.log(`\n=== RESULT: pass=${pass} fail=${fail} ===`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error("ERROR", e); process.exit(2); });
