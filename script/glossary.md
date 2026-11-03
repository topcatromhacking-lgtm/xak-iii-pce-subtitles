# Xak III name glossary (subtitles)

Rule: subtitles use **NightWolve's spellings** (XakIII(US) v1.00 text patch and
`XakIII-Jap2EngScript.html`), so the voiced cutscenes match the in-game English
text. The 2006 Ys Utopia listening transcript (SkyeWelse, topic 205) renamed many
characters. Those spellings must **not** appear in `en_subtitle`, and
`tools/lint_script.py` rejects them (see the `avoid:` lines at the bottom).

| Use (NightWolve) | Japanese | 2006 transcript / literal | Notes |
|---|---|---|---|
| Ratok | ラトク | Latok | Full name "Ratok Kurt" (ラトク・カート); transcript "Latok Kart" |
| King Webis | ウェービス王 | King Wavis / King Arband Wavis | |
| Webis (kingdom/castle) | ウェービス | Wavis | |
| Pixie | ピクシー | Pixie | |
| Lou Millie Pixie | ? | Lou Miri Pixie | Spelling is from the earlier notes; not yet found in the NW HTML script. Check the in-game text before using it |
| General Beluga | ベルーガ将軍 | General Beluga | |
| Magician (court mage) | 魔導士 | Magician | Speaker label only |
| Gafuh | ガフー | Gahoe (the Warlock) | NW calls him a "sorcerer" (魔術師/魔導士) |
| Mt. Fuji | ギンガヌール山 | Mt. Ginganul | Literal reading is "Ginganul". NW chose "Mt. Fuji", so we keep it for consistency |
| Fray | フレイ | Fray | |
| Ryun | リューン | Rune | |
| Leo (Admiral) | レオーノフ (提督) | Admiral Leo | Literal "Leonov" |
| Sunaga | スナガ | Sunkan | |
| Mesuron | メスロン | Mesuron | |
| Yunker | ユンカース | Yunker | Literal "Junkers" |
| Isufante | イスファンテ | – | |
| Hoan (Ashtar) | ホーン | Horn Ashtar | NW uses "Hoan" in town text |
| Xak Sword | サーク・ソード | Xak Sword | |
| Duel Knight | デュエル戦士 | Duel Knight | |
| Zekishis | ゼキシス | Zekishis | |
| Demon Knight | 夜叉騎士 | DemonKnight | |
| Necromancer | ネクロマンサー | Necromancer | |
| Aldis | アルディス | – | |
| Lorinza | ロリンザー | – | |
| Saria (Ratok's mother) | サリア | – | |
| Farland | ファーランド | Farland | |
| Fearless (Ratok's home town) | – | Fearless | NW stage header (also typo "Feiless") |
| Gate | ゲート | Gate | Quoted ("Gate") on first mention only |
| War of Sealing | 封印戦争 | War of Sealing | |
| Thunder God | 雷神 | Thunder God | |
| Galoa | ガロア | – | |
| Kalta | カルタ | – | |
| Oceanity | – | Oceanity | Fairy realm (VS5) |

## Lint avoid-list (machine-readable; `avoid: <wrong> -> <right>`)

avoid: Latok -> Ratok
avoid: Kart -> Kurt
avoid: Wavis -> Webis
avoid: Gahoe -> Gafuh
avoid: Ginganul -> Mt. Fuji
avoid: Horn -> Hoan
avoid: Miri -> Millie
avoid: Rune -> Ryun
avoid: Sunkan -> Sunaga
