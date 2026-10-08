# dsh-customs-doc-check — Verificação da coerência do registo de documentos de declaração aduaneira

`dsh-customs-doc-check` lê um registo de documentos de declaração (报关单证台账) —cujos nomes de coluna podem estar em chinês ou em inglês— e verifica esse registo em si mesmo, não a declaração por trás dele: que cada linha traga pelo menos um dos dois, o nome da mercadoria ou o montante total; que o código da mercadoria tenha dez dígitos e a moeda seja um código de três letras; que não se repita nenhum número de documento; que o peso bruto não seja inferior ao peso líquido; que a data de declaração, quando registada, seja analisável e não seja posterior à data de verificação; e que não reste nenhum marcador de modelo por substituir na coluna do nome da mercadoria.

## O que ele responde

| Você pergunta | O que ele responde |
|---|---|
| Numa linha o nome da mercadoria ainda diz `待填` e a célula do montante está vazia — isso é reportado? | `CD-001` não: exige apenas que pelo menos um dos dois, o nome da mercadoria ou o montante total, esteja preenchido, e `待填` não está em branco. Quem reporta essa linha é `CD-007`, que procura na coluna do nome da mercadoria os marcadores de modelo que o pacote lista (`【`, `{{`, `XXX`, `待填`, `TBD` e afins). `CD-001` não julga se o conteúdo declarado é verdadeiro; `CD-007` procura apenas esses termos nessa coluna, e a sua lista de termos pode ser ajustada ao modelo da sua instituição. |
| O código da mercadoria está escrito `84713000`, com oito dígitos — isso é reportado? | Sim. `CD-002` compara a célula com dez dígitos e reporta qualquer outro caso. Verifica apenas o número de dígitos e a legalidade dos caracteres, nunca se o código é o correto: a mesma mercadoria pode legitimamente ter códigos diferentes sob decisões de classificação diferentes. O número de dígitos é o parâmetro `pattern` da regra, alterável quando a pauta aduaneira mudar o seu número de dígitos. |
| A coluna da moeda diz `RMB` numa linha e `usd` noutra — qual das linhas é reportada? | `usd`: `CD-003` aceita apenas três letras maiúsculas. `RMB` encaixa nessa forma e passa, porque a regra é uma verificação de forma e não a redação do artigo — a tabela de códigos para a qual o artigo remete não foi obtida, e a regra não toma posição entre as grafias `CNY` e `RMB` que a prática aduaneira também usa; restrinja o `pattern` se a sua instituição fixar uma só. Não julga se a moeda escolhida é a correta para a liquidação. |
| O mesmo número de documento aparece em duas linhas — o que diz a verificação? | `CD-004` reporta o número repetido; na comparação os espaços são ignorados. A unicidade é tudo o que a regra estabelece: um resultado costuma significar que o mesmo documento foi registado duas vezes ou que um número foi copiado de outro documento, e qual dos dois está errado cabe a uma pessoa confirmar. Não decide qual registo é o válido. |
| O peso bruto está `1,180` e o líquido `1,250` — isso é detetado? E se uma linha não tiver peso líquido? | O primeiro é reportado: `CD-005` compara os dois valores e reporta a linha em que o peso bruto é inferior ao líquido. Só os números são comparados e aceitam-se unidades (`12.5KGS`), e a regra nunca julga se o peso declarado é verdadeiro. Uma linha à qual falte um dos dois campos não é comparada de todo; se isso não deixar nada a comparar, a regra entra em `skipped` com o seu motivo em vez de ser reportada como diferença. |
| O registo não traz data de declaração nenhuma e uma linha tem `2026-13-40` — o que é reportado? | A data impossível é reportada: `CD-006` exige que a data seja analisável e não posterior à data de verificação. A falta da data de declaração não é reportada como defeito — no momento da declaração essa coluna é 免予填报, sendo registada pelo sistema informático aduaneiro e não pelo declarante, pelo que a regra só verifica a data quando ela consta. Uma data que não se consegue analisar é reportada à parte e nunca é omitida em silêncio, e a regra não julga se a declaração foi feita dentro de um prazo legal. |

## Normas que segue

| Documento | Número | Regras que o citam |
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

| Superfície | Estado |
|---|---|
| Harness | Faixa de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificada para aceitar tanto `0.2.0-rc.2` quanto `0.2.1-alpha.1`. **`engines.dsh` não é declarado**: não tem leitor e não pode recusar nenhum host |
| Node | `^22.19.0 || >=24.0.0` |
| Plataformas | Todas (ESM puro; sem código nativo, sem rede, sem chamada ao modelo) |
| Modo de ferramenta | Funciona em `native`, `ptc` e `both`; para um diretório inteiro use `ptc` |

## What it does

A tabela de regras, os campos e o comportamento detalhado estão em [README.md](README.md#what-it-does) (versão principal em inglês). O plugin apenas lista divergências literais frente às cláusulas citadas e indica em `skipped` cada verificação que não pôde ser executada.

## Install

```sh
dsh plugin --profile <name> add dsh-customs-doc-check
dsh --profile <name> --dump-config | grep 'dsh-customs-doc-check'
```

## Configuration

Todos os parâmetros ajustáveis ficam no esquema Schemastery de `src/config.ts`, portanto mudam pelo `cordis.yml` sem editar código; os limites por regra ficam no pacote de regras sob `rules/`.

| Chave | Tipo | Padrão | Descrição |
|---|---|---|---|
| `rulesFile` | string | `rules/customs-doc-check.yaml` | Caminho do pacote de regras, relativo à raiz do pacote |
| `disabledRules` | string[] | `[]` | Ids de regras a desativar; cada uma aparece em `skipped` |
| `onlyRules` | string[] | `[]` | Executar apenas estas regras; vazio executa todas |
| `skipNotes` | string | `""` | Nota acrescentada a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Orçamento de tempo limite cooperativo da ferramenta |

## Material format

Aceita JSON ou YAML. O exemplo completo de campos está em [README.md](README.md#material-format) (versão principal em inglês). Os campos são opcionais na camada de leitura e validados pelo motor, de modo que uma exportação parcial gera achados sobre o que falta em vez de falhar.

## Rule sources

Os dados das regras ficam separados do código: cada regra traz documento, número, cláusula na numeração própria da fonte, trecho literal e URL de origem. O carregador impõe que o trecho seja citação real de pelo menos oito caracteres e que uma verificação baseada apenas em princípio geral (`kind: derived-from-principle`, teto `warn`) ou em política local (`kind: institutional-configuration`, teto `info`) nunca seja declarada `error`.

Os limites verificados e as conclusões deliberadamente **não** afirmadas estão em [README.md](README.md#rule-sources) (versão principal em inglês) e em `rules/evidence/`.

## Troubleshooting

- **O plugin instala mas a ferramenta não aparece**: confirme que `main` resolve para `lib/index.mjs` e que `pnpm run build` o gerou.
- **`dsh plugin add` recusa o pacote**: a faixa de peers cobre `0.1.x` e `0.2.x`; fora dela, conceda isenção explícita com `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Uma regra não executou**: leia o arranjo `skipped`.
- **`check` informa `manifest-peers` como falha**: problema conhecido do `dsh-plugin-dev`; o runtime aplica a compatibilidade na instalação.
- **Os horários parecem deslocados**: toda a aritmética é de hora local sobre as cadeias fornecidas.

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-customs-doc-check
```

O último comando copia o kit compartilhado de `../_shared` para `src/shared/`; execute-o novamente após cada alteração compartilhada.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-customs-doc-check contributors.
