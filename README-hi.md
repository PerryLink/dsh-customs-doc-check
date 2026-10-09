# dsh-customs-doc-check — सीमा-शुल्क घोषणा दस्तावेज़ रजिस्टर की संगति की जाँच

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)

`dsh-customs-doc-check` एक घोषणा-संबंधी दस्तावेज़ रजिस्टर (报关单证台账) पढ़ता है — जिसके स्तंभ-नाम चीनी या अंग्रेज़ी में हो सकते हैं — और उसी रजिस्टर की जाँच करता है, उसके पीछे की घोषणा की नहीं: कि हर पंक्ति में माल का नाम या कुल राशि में से कम से कम एक भरा हो, कि माल-कोड दस अंकों का हो और मुद्रा तीन अक्षरों का कोड हो, कि कोई दस्तावेज़-क्रमांक दोहराया न गया हो, कि सकल भार निवल भार से कम न हो, कि दर्ज घोषणा-तिथि पढ़ी जा सके और जाँच-तिथि से बाद की न हो, और कि माल-नाम के स्तंभ में कोई अपरिवर्तित टेम्पलेट प्लेसहोल्डर शेष न रहे।

## आउटपुट कैसा दिखता है

![Terminal demo of dsh-customs-doc-check: real output over its CD-001 fixture](https://raw.githubusercontent.com/PerryLink/dsh-customs-doc-check/main/docs/assets/dsh-customs-doc-check-demo.png)

इस प्लगइन का अपने ही `CD-001` टेस्ट फ़िक्स्चर पर वास्तविक आउटपुट — कोई नकली चित्र नहीं। नियम-पैक उद्धरण नहीं गढ़ता, इसलिए हर निष्कर्ष लागू किए गए खंड का नाम और यह भी बताता है कि उसका मूल पाठ इस बार प्राप्त नहीं हुआ।

## यह किन सवालों का जवाब देता है

| आपका सवाल | इसका जवाब |
|---|---|
| एक पंक्ति में माल का नाम अब भी `待填` लिखा है और राशि का खाना खाली है — क्या कुछ दर्ज होता है? | `CD-001` नहीं: वह केवल यह अपेक्षा करता है कि माल का नाम या कुल राशि — इनमें से कम से कम एक भरा हो, और `待填` खाली नहीं है। उस पंक्ति को `CD-007` दर्ज करता है, जो माल-नाम के स्तंभ में पैक में सूचीबद्ध टेम्पलेट प्लेसहोल्डर (`【`, `{{`, `XXX`, `待填`, `TBD` आदि) खोजता है। `CD-001` यह नहीं आँकता कि घोषित विवरण सच है या नहीं; `CD-007` केवल उसी एक स्तंभ में इन शब्दों को खोजता है, और शब्द-सूची अपने टेम्पलेट के अनुसार बदली जा सकती है। |
| माल-कोड `84713000` लिखा है — केवल आठ अंक। क्या यह दर्ज होता है? | हाँ। `CD-002` उस खाने को दस अंकों से मिलाता है और बाकी सब दर्ज करता है। यह केवल अंकों की संख्या और अक्षरों की वैधता देखता है, यह कभी नहीं कि कोड सही है या नहीं — एक ही माल के विभिन्न वर्गीकरण निर्णयों के अंतर्गत अलग-अलग कोड वैध हो सकते हैं। अंकों की संख्या इस नियम का `pattern` पैरामीटर है, जिसे तत्कालीन टैरिफ के अंक बदलने पर बदला जा सकता है। |
| मुद्रा स्तंभ में एक पंक्ति में `RMB` है और दूसरी में `usd` — कौन-सी पंक्ति दर्ज होती है? | `usd`: `CD-003` केवल तीन बड़े अक्षर स्वीकार करता है। `RMB` इस रूप में बैठता है, इसलिए पास हो जाता है — यह नियम रूप की जाँच है, अनुच्छेद की शब्दावली नहीं; जिस कोड तालिका की ओर अनुच्छेद संकेत करता है वह प्राप्त नहीं हुई, और यह नियम `CNY` तथा `RMB` लेखन में से किसी एक को तय नहीं करता; यदि आपकी संस्था एक ही लेखन तय करती है तो `pattern` को कस दें। यह नहीं आँकता कि चुनी गई मुद्रा भुगतान के लिए सही है या नहीं। |
| एक ही दस्तावेज़-क्रमांक दो पंक्तियों में आया है — जाँच क्या बताती है? | `CD-004` दोहराया गया क्रमांक दर्ज करता है; तुलना करते समय रिक्त स्थान छोड़ दिए जाते हैं। यह नियम केवल अद्वितीयता स्थापित करता है: ऐसा परिणाम सामान्यतः यह दर्शाता है कि वही दस्तावेज़ दो बार दर्ज हुआ है या क्रमांक कहीं और से कॉपी हुआ है, और इनमें कौन गलत है यह मनुष्य को देखना है। यह तय नहीं करता कि कौन-सा पंजीकरण मान्य है। |
| सकल भार `1,180` और निवल भार `1,250` है — क्या यह पकड़ा जाता है? और यदि किसी पंक्ति में निवल भार ही न हो? | पहला दर्ज होता है: `CD-005` दोनों मानों की तुलना करता है और जिस पंक्ति में सकल भार निवल भार से कम है उसे दर्ज करता है। केवल संख्याओं की तुलना होती है और इकाई चलती है (`12.5KGS`), और यह नियम कभी नहीं आँकता कि घोषित भार सच है या नहीं। जिस पंक्ति में इन दोनों में से कोई एक खाना न हो वह तुलना में ही नहीं आती; यदि इससे तुलना के लिए कुछ न बचे तो नियम अंतर के रूप में दर्ज होने के बजाय अपने कारण के साथ `skipped` में चला जाता है। |
| रजिस्टर में घोषणा-तिथि बिल्कुल नहीं है, और एक पंक्ति में `2026-13-40` है — क्या-क्या दर्ज होता है? | असंभव तिथि दर्ज होती है: `CD-006` अपेक्षा करता है कि तिथि पढ़ी जा सके और जाँच-तिथि से बाद की न हो। घोषणा-तिथि का न होना दोष के रूप में दर्ज नहीं होता — घोषणा के समय वह स्तंभ 免予填报 रहता है, उसे घोषणाकर्ता नहीं बल्कि सीमा-शुल्क का कंप्यूटर सिस्टम दर्ज करता है, इसलिए यह नियम केवल तभी जाँचता है जब तिथि लिखी हो। जो तिथि पढ़ी न जा सके वह अलग से दर्ज होती है, चुपचाप छोड़ी नहीं जाती, और यह नियम यह नहीं आँकता कि घोषणा किसी विधिक अवधि के भीतर हुई या नहीं। |

## यह किन मानकों पर आधारित है

| दस्तावेज़ | संख्यांक | इन्हें उद्धृत करने वाले नियम |
|---|---|---|
| 《中华人民共和国海关进出口货物报关单填制规范》 | 海关总署公告 2019 年第 18 号（本次未取得条文） | CD-001, CD-002, CD-005, CD-007 |
| 《表示货币的代码》 | GB/T 12406—2022（表示货币的代码；2022-12-30 发布并实施；全部代替 GB/T 12406—2008（该版名称为「表示货币和资金的代码」）——注意旧版名称含"资金"；修改采用 ISO 4217:2015，非等同采用；条号本次未取得） | CD-003 |
| 《中华人民共和国海关进出口货物申报管理规定》 | 海关总署令（现行令号本次未核实） | CD-004, CD-006 |

**Boundary:** this plugin checks a **报关单证台账** for what a register can be held to mechanically — that
the key columns are filled, that the commodity code and currency follow their formats, that document
numbers are unique, that gross weight is not below net weight, that dates parse, and that no template
placeholder survives. It does **not** decide whether a declaration is truthful, whether it amounts to
misdeclaration, whether it affects duty, or whether goods should be inspected or penalised. **Those calls
belong to Customs**, and the same goods may legitimately carry different codes under different
classification decisions. **This plugin never judges classification.**

> ### ⚠️ What the citations rest on
>
> **《中华人民共和国海关进出口货物报关单填制规范》was obtained in full and read article by article** (49 articles
> plus the closing definitions), and `rules/evidence/clause-verification.md` records what was quoted: article 34
> (the commodity code is **10 digits**), articles 5 and 6 (dates are **8 digits**, year-month-day, and — worth
> knowing — the declaration date is 「**在申报时免予填报**」, so a register lacking it is normal), article 39
> (currency is taken from the 《货币代码表》), articles 24–26 (packages, gross and net weight) and article 38.
> The **issuing facts were confirmed against the official announcement**: 《海关总署公告 2019 年第 18 号》,
> dated 2019-01-22, **in force from 2019-02-01, and it repealed 海关总署 2018 年第 60 号公告**, so citing that one
> is simply wrong. 《进（出）境货物备案清单》 is filled **比照** this specification.
>
> **Two claims were corrected as a result.** `CD-003` said currency "should be three letters" — the article says
> only 「按海关规定的《货币代码表》选择相应的货币名称及代码填报」, and that code table **was not obtained**, so
> three letters is an inference about the table's shape, not the article's wording. And `CD-006` now states the
> exemption above rather than implying a missing declaration date is a defect.
>
> **Every `excerpt` still says "本次未取得" and every rule stays `warn` or `info`** — deliberately. The
> specification governs **how the declaration form's columns are filled in**, while this plugin checks an
> enterprise's **supporting-document register**. A register is not a declaration form, so raising a rule to
> `direct` would dress a register gap up as a customs obligation. **《申报管理规定》and the various code tables
> (关区、运输方式、监管方式、货币、国别、港口 etc.) were all unobtained**, which is exactly why no code table is
> built in. The specification text itself was read from a **local trade-promotion council's reprint**, because the
> official attachment is a `.doc` and this tool cannot decode binary Office files.
>
> Two checks deserve a note of their own. The commodity-code check verifies **ten digits and nothing
> else** — the digit count comes from the current tariff, and the check never says whether a code is the
> *right* code. The currency check verifies **three upper-case letters**, and deliberately takes no
> position on `CNY` versus the `RMB` spelling that Customs practice also uses; narrow the pattern if your
> house style is one of them.

## Compatibility

| सतह | स्थिति |
|---|---|
| Harness | peer रेंज `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — `0.2.0-rc.2` और `0.2.1-alpha.1` दोनों को स्वीकार करने के लिए सत्यापित। **`engines.dsh` जानबूझकर घोषित नहीं**: इसका कोई पाठक नहीं और यह किसी होस्ट को अस्वीकार नहीं कर सकता |
| Node | `^22.19.0 || >=24.0.0` |
| प्लेटफ़ॉर्म | सभी (शुद्ध ESM; कोई नेटिव कोड नहीं, कोई नेटवर्क नहीं, कोई मॉडल कॉल नहीं) |
| टूल मोड | `native`, `ptc` और `both` में काम करता है; पूरे फ़ोल्डर के लिए `ptc` चुनें |

## What it does

नियम-सूची, फ़ील्ड और विस्तृत व्यवहार [README.md](README.md#what-it-does) (अंग्रेज़ी मुख्य संस्करण) में हैं। यह प्लगइन केवल उद्धृत धाराओं के सामने शाब्दिक अंतर सूचीबद्ध करता है और हर न चल पाई जाँच को `skipped` में बताता है।

## Install

```sh
dsh plugin --profile <name> add dsh-customs-doc-check
dsh --profile <name> --dump-config | grep 'dsh-customs-doc-check'
```

## Configuration

सभी समायोज्य पैरामीटर `src/config.ts` की Schemastery स्कीमा में हैं, इसलिए कोड बदले बिना `cordis.yml` से बदले जा सकते हैं; प्रति-नियम सीमाएँ `rules/` के नियम-पैक में हैं।

| कुंजी | प्रकार | डिफ़ॉल्ट | विवरण |
|---|---|---|---|
| `rulesFile` | string | `rules/customs-doc-check.yaml` | नियम-पैक का पथ, पैकेज रूट के सापेक्ष |
| `disabledRules` | string[] | `[]` | बंद करने वाले नियम id; प्रत्येक `skipped` में दिखता है |
| `onlyRules` | string[] | `[]` | केवल ये नियम चलाएँ; खाली होने पर सभी नियम चलते हैं |
| `skipNotes` | string | `""` | हर `skipped` कारण के आगे जोड़ी जाने वाली टिप्पणी |
| `timeoutMs` | number | `120000` | उपकरण का सहकारी समय-सीमा बजट |

## Material format

JSON या YAML स्वीकार्य है। पूरा फ़ील्ड उदाहरण [README.md](README.md#material-format) (अंग्रेज़ी मुख्य संस्करण) में है। पढ़ने की परत में फ़ील्ड वैकल्पिक हैं और जाँच इंजन उन्हें सत्यापित करता है, इसलिए आंशिक निर्यात पर क्रैश के बजाय "अनुपस्थित" श्रेणी के निष्कर्ष मिलते हैं।

## Rule sources

नियम-डेटा कोड से अलग है: प्रत्येक नियम में दस्तावेज़, संख्या, स्रोत की अपनी क्रमांकन-प्रणाली के अनुसार धारा, शब्दशः उद्धरण और स्रोत URL होता है। लोडर लागू करता है कि उद्धरण कम से कम आठ अक्षरों का वास्तविक उद्धरण हो, और जिस जाँच का आधार केवल सामान्य सिद्धांत (`kind: derived-from-principle`, अधिकतम `warn`) या स्थानीय नीति (`kind: institutional-configuration`, अधिकतम `info`) हो, उसे कभी `error` घोषित न किया जाए।

सत्यापित सीमाएँ और जान-बूझकर **न** कहे गए निष्कर्ष [README.md](README.md#rule-sources) (अंग्रेज़ी मुख्य संस्करण) और `rules/evidence/` में हैं।

## Troubleshooting

- **प्लगइन इंस्टॉल हो गया पर टूल दिखता नहीं**: जाँचें कि `main` `lib/index.mjs` पर जाता है और `pnpm run build` ने उसे बनाया है।
- **`dsh plugin add` असंगत बताकर मना करता है**: peer range `0.1.x` और `0.2.x` दोनों को कवर करती है; बाहर होने पर स्पष्ट छूट दें: `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`।
- **कोई नियम नहीं चला**: `skipped` सरणी देखें।
- **`check` में `manifest-peers` विफल दिखता है**: यह `dsh-plugin-dev` की ज्ञात अपस्ट्रीम समस्या है; रनटाइम इंस्टॉल के समय अनुकूलता लागू करता है।
- **समय खिसका हुआ लगता है**: सारी गणना दिए गए स्ट्रिंग पर वॉल-क्लॉक है।

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-customs-doc-check
```

अंतिम कमांड `../_shared` का साझा किट `src/shared/` में कॉपी करता है; हर साझा बदलाव के बाद इसे दोबारा चलाएँ।

## License

[Apache License 2.0](LICENSE) © 2026 dsh-customs-doc-check contributors.
