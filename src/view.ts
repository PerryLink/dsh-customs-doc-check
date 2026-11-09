/**
 * Model-facing projection of a {@link Report}.
 *
 * `buildView` is pure and covers the whole canonical output shape, so both the
 * tool's `output.render` and the test suite exercise exactly what the model
 * reads. `output.schema` in `index.ts` mirrors these keys.
 */

import { canonicalJson } from './shared/report.ts'
import { DISCLAIMER } from './shared/wording.ts'
import type { Issue, Report, Severity } from './shared/report.ts'
import type { IngestMeta } from './shared/ingest.ts'

const SEVERITY_ORDER: readonly Severity[] = ['error', 'warn', 'info']

/** Markdown rendering of the canonical report, kept column-free for models. */
export interface ReportView {
  plugin: string
  target: string
  checkedAt: string
  rulesetVersion: string
  summary: { error: number; warn: number; info: number }
  issueCount: number
  skippedCount: number
  execution?: Report['execution']
  /** True when the extraction needs a human confirmation before rules run. */
  needsConfirmation?: boolean
  /** Extraction metadata, when the material came from a document. */
  ingest?: IngestMeta
  markdown: string
  reportJson: string
}

function issueLines(issues: readonly Issue[]): string[] {
  const lines: string[] = []
  for (const severity of SEVERITY_ORDER) {
    const group = issues.filter((issue) => issue.severity === severity)
    if (group.length === 0) continue
    lines.push(`### ${severity}（${group.length} 条）`)
    lines.push('')
    for (const issue of group) {
      const where: string[] = []
      if (issue.locator.file !== undefined) where.push(issue.locator.file)
      if (issue.locator.row !== undefined) where.push(`第${issue.locator.row}行`)
      if (issue.locator.page !== undefined) where.push(`第${issue.locator.page}页`)
      if (issue.locator.cell !== undefined) where.push(issue.locator.cell)
      if (issue.locator.column !== undefined) where.push(`字段 ${issue.locator.column}`)
      lines.push(`- \`${issue.ruleId}\` ${where.length === 0 ? '' : `[${where.join(' · ')}] `}${issue.found}`)
      lines.push(`  - 依据：${issue.expected}`)
      lines.push(`  - 条款：${issue.basis}`)
      if (issue.fix !== undefined) lines.push(`  - 建议核对：${issue.fix}`)
    }
    lines.push('')
  }
  return lines
}

/**
 * Build the model-facing view of a report.
 * @param report - canonical report value.
 * @returns the structured view consumed by `output.render` and by tests.
 */
export function buildView(report: Report, ingest?: IngestMeta): ReportView {
  const lines: string[] = []
  lines.push(`# ${report.plugin} 检查结果`)
  lines.push('')
  lines.push(`- 检查对象：${report.target}`)
  lines.push(`- 检查时间：${report.checkedAt}`)
  lines.push(`- 规则集版本：${report.rulesetVersion}`)
  lines.push(`- 统计：错误 ${report.summary.error} · 提示 ${report.summary.warn} · 参考 ${report.summary.info}`)
  if (report.execution !== undefined) {
    lines.push(
      `- 规则执行：${report.execution.executed}/${report.execution.total}` +
        ` · 跳过 ${report.execution.skipped}` +
        ` · manual ${report.execution.manual}` +
        ` · 未实现 ${report.execution.unsupported}`,
    )
  }
  if (ingest !== undefined) {
    lines.push(`- 文档抽取：表 ${ingest.tableIndex + 1} · 表头行 ${ingest.headerRows.join('+')} · 置信度 ${ingest.confidence}`)
  }
  lines.push('')
  if (ingest !== undefined) {
    lines.push('## 抽取结果')
    lines.push('')
    lines.push('以下为插件从文档中识别出的表；若表头或行列不对，请指定 tableIndex/headerRow 后重试。')
    lines.push('')
    lines.push(ingest.preview)
    lines.push('')
    if (ingest.warnings.length > 0) {
      lines.push(`抽取警告：${ingest.warnings.join('；')}`)
      lines.push('')
    }
  }
  lines.push('## 差异明细')
  lines.push('')
  if (report.issues.length === 0) {
    lines.push('本次执行的检查项未产生差异条目。')
    lines.push('')
  } else {
    lines.push(...issueLines(report.issues))
  }
  lines.push('## 未执行的检查')
  lines.push('')
  if (report.skipped.length === 0) {
    lines.push('规则集声明的全部检查项均已执行。')
  } else {
    lines.push(`以下 ${report.skipped.length} 项检查未执行，其结论不包含在本报告中：`)
    lines.push('')
    for (const entry of report.skipped) lines.push(`- \`${entry.rule}\`：${entry.reason}`)
  }
  lines.push('')
  lines.push('---')
  lines.push('')
  lines.push(DISCLAIMER)

  return {
    plugin: report.plugin,
    target: report.target,
    checkedAt: report.checkedAt,
    rulesetVersion: report.rulesetVersion,
    summary: report.summary,
    issueCount: report.issues.length,
    skippedCount: report.skipped.length,
    ...(report.execution === undefined ? {} : { execution: report.execution }),
    ...(ingest === undefined ? {} : { ingest }),
    markdown: lines.join('\n'),
    reportJson: canonicalJson(report),
  }
}


/**
 * Build a confirmation result for a low-confidence document extraction.
 * No rule runs until the user confirms the table/header.
 * @param target - document path.
 * @param meta - extraction metadata and preview.
 * @param candidates - candidate table ids when the extractor was ambiguous.
 * @returns a view with `needsConfirmation: true`.
 */
export function buildConfirmationView(target: string, meta: IngestMeta, candidates: string[]): ReportView {
  const lines: string[] = []
  lines.push('# 需要确认文档抽取')
  lines.push('')
  lines.push(`- 检查对象：${target}`)
  lines.push(`- 文档抽取：表 ${meta.tableIndex + 1} · 表头行 ${meta.headerRows.join('+')} · 置信度 ${meta.confidence}`)
  if (candidates.length > 0) lines.push(`- 候选表：${candidates.join('、')}`)
  lines.push('')
  lines.push('抽取置信度较低，规则尚未运行。请先核对下表；确认无误后带 `confirm: true` 重试，或用 `tableIndex`/`headerRow` 指定正确的表和表头。')
  lines.push('')
  lines.push(meta.preview)
  if (meta.warnings.length > 0) {
    lines.push('')
    lines.push(`抽取警告：${meta.warnings.join('；')}`)
  }
  return {
    plugin: 'dsh-customs-doc-check',
    target,
    checkedAt: new Date().toISOString(),
    rulesetVersion: '',
    summary: { error: 0, warn: 0, info: 0 },
    issueCount: 0,
    skippedCount: 0,
    needsConfirmation: true,
    ingest: meta,
    markdown: lines.join('\n'),
    reportJson: '{}',
  }
}
