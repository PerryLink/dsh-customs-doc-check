/**
 * Optional document entry point.
 *
 * The checker's canonical input is a table the user already has as JSON, YAML
 * or CSV. Word/Excel users can hand the same table over directly when the
 * separate `dsh-table-ingest` plugin is installed; this module is the only
 * place that knows about that package, and it fails with an install hint
 * rather than a YAML syntax error when the package is absent.
 *
 * Deliberately a dynamic import: a user who only has JSON pays no install
 * cost, and the checker keeps its zero-dependency package contract.
 *
 * @module dsh-aqua-input-check/ingest
 */

import { readFile } from 'node:fs/promises'
import { extname, resolve } from 'node:path'
import { MaterialError } from './table.ts'
import type { TableSpec } from './table.ts'

/** Extensions that go through the optional ingest layer. */
const DOCUMENT_EXTENSIONS = new Set(['.docx', '.xlsx', '.xlsm', '.csv', '.tsv'])

/** Metadata returned to the report so the extraction is auditable. */
export interface IngestMeta {
  /** How sure the table/header detector is. */
  confidence: 'high' | 'medium' | 'low'
  /** Markdown preview of the extracted table. */
  preview: string
  /** Non-fatal extraction warnings. */
  warnings: string[]
  /** 0-based table index chosen inside the document. */
  tableIndex: number
  /** Header rows used (1 or 2 entries). */
  headerRows: number[]
  /** Column names the extractor recognised. */
  columns: string[]
}

/** Result of reading a document, either a table or a confirmation request. */
export type DocumentRead =
  | { kind: 'table'; text: string; target: string; meta: IngestMeta }
  | { kind: 'confirmation'; target: string; meta: IngestMeta; candidates: string[] }

/** True when the path should go through the optional ingest layer. */
export function needsIngest(file: string): boolean {
  return DOCUMENT_EXTENSIONS.has(extname(file).toLowerCase())
}

/** The subset of `dsh-table-ingest/api` this module uses. */
interface IngestApi {
  ingestToTable: (
    source: Buffer,
    filename: string,
    hint: Record<string, unknown>,
  ) => IngestApiResult
}

interface IngestApiResult {
  ok: boolean
  table?: {
    header: Record<string, string>
    rows: Record<string, string>[]
    columns: string[]
    tableIndex: number
    headerRows: number[]
  }
  confidence: 'high' | 'medium' | 'low'
  preview: string
  warnings: string[]
  error?: string
  candidates: { tableId: string }[]
}

/** Load the optional package, with an actionable error when it is missing. */
async function loadIngest(): Promise<IngestApi> {
  try {
    // A variable specifier keeps this optional package out of the static type
    // graph: the checker still type-checks and builds with no dependency on it.
    const specifier = 'dsh-table-ingest/api'
    return (await import(specifier)) as IngestApi
  } catch {
    throw new MaterialError(
      '要直接读 Word/Excel/CSV，请先安装 dsh-table-ingest（dsh plugin --profile <name> add dsh-table-ingest），' +
        '或先把材料转成 JSON/YAML。当前插件本身不携带文档解析器。',
    )
  }
}

/**
 * Read a real document through `dsh-table-ingest`.
 *
 * @param file - path to a .docx/.xlsx/.xlsm/.csv/.tsv file.
 * @param spec - the plugin's table spec; its column aliases drive table selection.
 * @param options - confirmation/table-selection overrides.
 * @returns the table as JSON text, or a confirmation request for a low-confidence extraction.
 */
export async function readTableDocument(
  file: string,
  spec: TableSpec,
  options: { confirm?: boolean; tableIndex?: number; headerRow?: number } = {},
): Promise<DocumentRead> {
  const path = resolve(file)
  const api = await loadIngest()
  const buffer = await readFile(path)
  const expectedColumns = Object.values(spec.columns).flat()
  const result = api.ingestToTable(buffer, path, {
    expectedColumns,
    tableIndex: options.tableIndex ?? 'auto',
    headerRow: options.headerRow ?? 'auto',
    previewRows: 5,
    ambiguous: 'fail',
  })

  if (!result.ok || result.table === undefined) {
    throw new MaterialError(
      `无法从 ${path} 识别表格：${result.error ?? '未知原因'}` +
        (result.candidates.length > 0 ? `（候选 ${result.candidates.length} 张，请指定 tableIndex）` : ''),
    )
  }

  const table = result.table
  const meta: IngestMeta = {
    confidence: result.confidence,
    preview: result.preview,
    warnings: result.warnings,
    tableIndex: table.tableIndex,
    headerRows: table.headerRows,
    columns: table.columns,
  }

  if (result.confidence === 'low' && options.confirm !== true) {
    return {
      kind: 'confirmation',
      target: path,
      meta,
      candidates: result.candidates.map((candidate) => candidate.tableId),
    }
  }

  return {
    kind: 'table',
    target: path,
    meta,
    text: JSON.stringify({ header: table.header, rows: table.rows }),
  }
}
