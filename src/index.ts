import { readFile } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { dirname, isAbsolute, resolve } from 'node:path'
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'
import { Config } from './config.ts'
import type { Config as ConfigShape } from './config.ts'
import { runCheck, parseMaterial, SPEC } from './model.ts'
import { needsIngest, readTableDocument, type IngestMeta } from './shared/ingest.ts'
import { MaterialError } from './shared/table.ts'
import { buildView, buildConfirmationView } from './view.ts'
import { loadRulesetFile } from './shared/memo.ts'

export const name = 'dsh-customs-doc-check'
export const inject = ['tools']
export { Config }

/** Tool id exposed to the model, and the row id in `cordis.patch.yml`. */
export const TOOL_NAME = 'customs_doc_check'

/**
 * Locate a package-owned file such as the rule pack.
 *
 * Resolution order: absolute path, then every ancestor of the module directory,
 * then the process working directory. A wrong silent fallback would build a
 * report from the wrong rule pack, so a miss throws with the paths tried.
 *
 * @param relative - configured path, relative to the plugin package root.
 * @returns the resolved absolute path.
 * @throws Error naming every location tried, when the file is absent.
 */
export function resolvePackageFile(relative: string): string {
  if (isAbsolute(relative)) {
    if (existsSync(relative)) return relative
    throw new Error(`规则库文件不存在：${relative}`)
  }
  const tried: string[] = []
  let current = import.meta.dirname ?? process.cwd()
  for (;;) {
    const candidate = resolve(current, relative)
    tried.push(candidate)
    if (existsSync(candidate)) return candidate
    const parent = dirname(current)
    if (parent === current) break
    current = parent
  }
  const fromCwd = resolve(process.cwd(), relative)
  if (!tried.includes(fromCwd)) {
    tried.push(fromCwd)
    if (existsSync(fromCwd)) return fromCwd
  }
  throw new Error(`规则库文件未找到：${relative}；已尝试 ${tried.length} 个位置，最近一处为 ${tried[0] ?? ''}`)
}

/** Read structured material from a file path or use the inline text as-is. */
async function readStructured(file: string | undefined, material: string | undefined, signal: AbortSignal): Promise<{ text: string; target: string }> {
  if (file !== undefined && file.trim() !== '') {
    const path = resolve(file)
    signal.throwIfAborted()
    const text = await readFile(path, { encoding: 'utf8', signal })
    return { text, target: path }
  }
  if (material !== undefined && material.trim() !== '') return { text: material, target: '(内联材料)' }
  throw new MaterialError('必须提供 file 或 material 之一')
}

/**
 * Register the checker tool.
 *
 * Registration is an effect: `ctx.tools.register` returns the disposer that
 * removes the tool when this plugin unloads, which is what keeps the plugin
 * hot-reloadable.
 *
 * @param ctx - plugin context, with `tools` already available.
 * @param config - validated configuration.
 */
export function apply(ctx: Context, config: ConfigShape): () => void {
  return ctx.tools.register(
    defineTool({
      name: TOOL_NAME,
      description:
        '报关单证一致性核对（按公开的报关单填制规范核对单证间字段一致性，仅提示差异，不作出定性结论）本工具只列出材料与所引条款之间的字面差异，供人工复核，不作出任何定性结论。' +
        '材料为 JSON/YAML，或 .docx/.xlsx/.xlsm/.csv/.tsv（后者需要另装 dsh-table-ingest）；无法执行的检查会列在 skipped 中。',
      parameters: {
        file: { type: 'string', description: '材料文件绝对路径（JSON/YAML，或 .docx/.xlsx/.xlsm/.csv/.tsv；文档格式需安装 dsh-table-ingest）。与 material 二选一。' },
        material: { type: 'string', description: '内联材料文本（JSON 或 YAML）。与 file 二选一。' },
        confirm: { type: 'boolean', description: '文档抽取置信度低时，核对预览后传 true 才运行规则。默认 false。' },
        tableIndex: { type: 'integer', description: '文档中的表序号（0 起）。默认自动选表。' },
        headerRow: { type: 'integer', description: '文档表格的表头行号（0 起）。默认自动判断。' },
        rulesFile: { type: 'string', description: '覆盖配置中的规则库路径（相对插件包根或绝对路径）。' },
        only: {
          type: 'array',
          items: { type: 'string' },
          description: '只执行这些规则 id；留空表示执行全部规则。',
        },
      },
      output: {
        schema: {
          type: 'object',
          additionalProperties: false,
          properties: {
            plugin: { type: 'string' },
            target: { type: 'string' },
            checkedAt: { type: 'string' },
            rulesetVersion: { type: 'string' },
            summary: {
              type: 'object',
              additionalProperties: false,
              properties: {
                error: { type: 'integer' },
                warn: { type: 'integer' },
                info: { type: 'integer' },
              },
            },
            issueCount: { type: 'integer' },
            skippedCount: { type: 'integer' },
            needsConfirmation: { type: 'boolean' },
            ingest: {
              type: 'object',
              additionalProperties: false,
              properties: {
                confidence: { type: 'string' },
                preview: { type: 'string' },
                warnings: { type: 'array', items: { type: 'string' } },
                tableIndex: { type: 'integer' },
                headerRows: { type: 'array', items: { type: 'integer' } },
                columns: { type: 'array', items: { type: 'string' } },
              },
            },
            execution: {
              type: 'object',
              additionalProperties: false,
              properties: {
                total: { type: 'integer' },
                executed: { type: 'integer' },
                skipped: { type: 'integer' },
                manual: { type: 'integer' },
                unsupported: { type: 'integer' },
              },
            },
            markdown: { type: 'string' },
            reportJson: { type: 'string' },
          },
        },
        render: (_args, value) => [{ type: 'text', text: (value as { markdown: string }).markdown }],
      },
      timeoutMs: config.timeoutMs,
      isConcurrencySafe: () => true,
      async execute(args, exec) {
        const relative = args.rulesFile !== undefined && args.rulesFile.trim() !== '' ? args.rulesFile : config.rulesFile
        let material: { text: string; target: string; ingest?: IngestMeta } | undefined
        if (args.file !== undefined && args.file.trim() !== '' && needsIngest(args.file)) {
          const doc = await readTableDocument(args.file, SPEC, {
            ...(args.confirm === undefined ? {} : { confirm: args.confirm }),
            ...(args.tableIndex === undefined ? {} : { tableIndex: args.tableIndex }),
            ...(args.headerRow === undefined ? {} : { headerRow: args.headerRow }),
          })
          if (doc.kind === 'confirmation') return buildConfirmationView(doc.target, doc.meta, doc.candidates)
          material = { text: doc.text, target: doc.target, ingest: doc.meta }
        }
        const structured: { text: string; target: string; ingest?: IngestMeta } =
          material ?? (await readStructured(args.file, args.material, exec.signal))
        const ruleset = await loadRulesetFile(resolvePackageFile(relative))
        exec.signal.throwIfAborted()
        const input = parseMaterial(structured.text, structured.target)
        const only = (args.only ?? []).length > 0 ? (args.only as string[]) : config.onlyRules
        const report = runCheck(input, ruleset, {
          plugin: name,
          checkedAt: new Date().toISOString(),
          disabledRules: config.disabledRules,
          onlyRules: only,
          skipNotes: config.skipNotes === '' ? undefined : config.skipNotes,
        })
        return buildView(report, structured.ingest)
      },
    }),
  )
}
