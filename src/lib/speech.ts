// Narrator hygiene for the Priv copilot.
//
// Support replies are markdown full of tables, **bold**, headings, emoji and
// emoticons. Reading that raw makes speech synthesis spell out "asterisk
// asterisk hash hash" and read emoticons character-by-character. These helpers
// reduce any reply to plain spoken prose, pick the most natural voice the
// browser offers, and let the user choose a voice explicitly.

const EMOJI =
  /[\u{1F000}-\u{1FAFF}\u{1F1E6}-\u{1F1FF}\u{FE00}-\u{FE0F}\u{200D}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{2190}-\u{21FF}\u{2300}-\u{23FF}\u{25A0}-\u{25FF}\u{2700}-\u{27BF}\u{E000}-\u{F8FF}]/gu;
// Text emoticons: :) :D :p ;) :( ;-) <3 xD -- only as whole tokens so
// timestamps ("8:30") and "8-)" style numbers inside words stay intact.
const EMOTICON = /(?:^|(?<=\s))[:;=8xX][-']?[)(DPp/\\|]+/g;
const HEART = /<3/g;

export function stripMarkdownForSpeech(md: string): string {
  let t = md || "";
  t = t.replace(/```[\s\S]*?```/g, " ");        // fenced code
  t = t.replace(/`([^`]*)`/g, "$1");             // inline code
  t = t.replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1"); // images -> alt
  t = t.replace(/\[([^\]]*)\]\([^)]*\)/g, "$1"); // links -> text
  t = t.replace(/<[^>]+>/g, " ");                // html tags
  t = t.replace(/^#{1,6}\s*/gm, "");             // headings
  t = t.replace(/^>\s?/gm, "");                  // quotes
  t = t.replace(/^(\s*[-*+]\s+)/gm, " ");        // bullets
  t = t.replace(/^(\s*\d+[.)]\s+)/gm, " ");      // numbered lists
  t = t.replace(/\|/g, " ");                     // table pipes
  t = t.replace(/(\*\*|__)(.*?)\1/g, "$2");      // bold
  t = t.replace(/(\*|_)(.*?)\1/g, "$2");         // italic
  t = t.replace(/~~(.*?)~~/g, "$1");             // strike
  return t;
}

// Turn stripped markdown into text a voice can read naturally: no emoji,
// no emoticons, no symbols the synthesizer would verbalize as words.
export function sanitizeForSpeech(raw: string): string {
  let t = raw || "";

  // Words for direction glyphs before generic emoji removal eats them.
  t = t.replace(/[→⇒➜]/g, " to ");
  t = t.replace(/->/g, " to ");
  t = t.replace(/[←]/g, " to ");
  t = t.replace(/[↑]/g, " up ");
  t = t.replace(/[↓]/g, " down ");

  // Emoticons and emoji out entirely (never spoken).
  t = t.replace(EMOTICON, " ");
  t = t.replace(HEART, " ");
  t = t.replace(EMOJI, " ");
  t = t.replace(/\(\s*\)/g, " "); // empty parens left behind

  // Symbols that TTS engines read out loud ("dash", "pipe", "number"...).
  t = t.replace(/#(\d+)/g, "number $1");
  t = t.replace(/[—–―]/g, ", ");
  t = t.replace(/…/g, ", ");
  t = t.replace(/\|/g, ", ");
  t = t.replace(/&/g, " and ");
  t = t.replace(/%/g, " percent");
  t = t.replace(/[°]/g, " degrees");
  t = t.replace(/[®™©§†‡]/g, " ");
  t = t.replace(/[*#^~`]/g, " ");

  // Slash reads as "slash" between letters ("EUR/USD") but is a fraction
  // bar between digits ("1/2").
  t = t.replace(/(?<=\d)\/(?=\d)/g, " over ");
  t = t.replace(/\//g, " ");

  // Money shorthand -> spoken form ("$65.2M" -> "$65.2 million").
  t = t.replace(/\$\s?(\d+(?:\.\d+)?)\s?M\b/g, "$$$1 million");
  t = t.replace(/\$\s?(\d+(?:\.\d+)?)\s?B\b/g, "$$$1 billion");

  // Trading abbreviations the model leans on.
  t = t.replace(/\bTPs?\s?(\d)\b/g, "take profit $1");
  t = t.replace(/\bTPs\b/g, "take profits");
  t = t.replace(/\bTP\b/g, "take profit");
  t = t.replace(/\bSLs?\b/g, "stop loss");
  t = t.replace(/\bP\s?&\s?L\b/g, "P and L");
  // "USD" only as a standalone currency suffix -- never inside EURUSD/USDT
  // or the USD/CHF pair.
  t = t.replace(/(?<![A-Za-z/])USD(?![/A-Za-z])/g, "dollars");

  // Underscores become spaces ("R_100" -> "R 100"), then leftover markdown
  // markers go.
  t = t.replace(/_/g, " ");
  t = t.replace(/[•]/g, " ");

  t = t.replace(/\s+/g, " ").trim();
  return t;
}

export function forSpeech(md: string): string {
  return sanitizeForSpeech(stripMarkdownForSpeech(md));
}

const NATURAL_VOICE =
  /(natural|neural|enhanced|premium|online|streaming|siri|aria|ava|andrew|jenny|guy|sonia|libby|ryan|amy|joanna|salli|kimberly|kendra|justin|matthew|ronnie|stephen|clara|danielle|emma|aria)/i;
const ROBOT_VOICE = /(compact|loquans|espeak|flite|robot|micro|mono|unison)/i;

export function scoreVoice(v: SpeechSynthesisVoice): number {
  const name = v.name || "";
  let s = 0;
  if (!v.localService) s += 6; // cloud/neural voices are much richer
  if (NATURAL_VOICE.test(name)) s += 8;
  if (/google/i.test(name)) s += 5;
  if (ROBOT_VOICE.test(name)) s -= 50;
  if (v.lang === "en-US" || v.lang === "en_US") s += 3;
  else if ((v.lang || "").toLowerCase().startsWith("en")) s += 2;
  if (v.default) s += 1;
  return s;
}

// English voices ranked most-natural first.
export function rankVoices(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice[] {
  return voices
    .filter((v) => (v.lang || "").toLowerCase().startsWith("en"))
    .slice()
    .sort((a, b) => scoreVoice(b) - scoreVoice(a));
}

// Best overall voice: honor an explicit user choice, otherwise rank.
export function pickBestVoice(
  voices: SpeechSynthesisVoice[],
  preferredURI?: string,
): SpeechSynthesisVoice | null {
  if (preferredURI) {
    const wanted = voices.find((v) => v.voiceURI === preferredURI);
    if (wanted) return wanted;
  }
  const ranked = rankVoices(voices);
  if (ranked.length > 0) return ranked[0];
  return voices.length > 0 ? voices[0] : null;
}
