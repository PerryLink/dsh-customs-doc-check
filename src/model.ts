/**
 * dsh-customs-doc-check — table shape and material contract.
 *
 * The plugin is data-only: this file declares which columns the material may use
 * and how they map onto canonical field names; the shared kit supplies the reader
 * and the check engine, and the rule pack declares every check. Adding a check
 * that fits an existing kind is a rule-pack edit, not a code change.
 */

import { canonicaliseRow, parseTable, type TableSpec } from './shared/table.ts'
import { runTableCheck, type TableCheckOptions, type TableInput } from './shared/rows.ts'
import type { Ruleset } from './shared/rules.ts'

/** Tool id exposed to the model, and the row id in `cordis.patch.yml`. */
export const TOOL_NAME = 'customs_doc_check'

/** The register's column aliases, declared once so both the spec and the guard see them. */
const COLUMNS = {
  docKind: ['单证种类', '单证类型', '单据名称', 'docKind', 'document'],
  docNo: ['单证编号', '编号', '发票号', '合同号', 'docNo', 'number'],
  hsCode: ['商品编号', 'HS编码', '税则号列', 'hsCode', 'hs'],
  goodsName: ['商品名称', '品名', '货名', 'goodsName', 'goods'],
  quantity: ['数量', '成交数量', 'quantity', 'qty'],
  unit: ['单位', '计量单位', '成交计量单位', 'unit'],
  unitPrice: ['单价', '成交单价', 'unitPrice', 'price'],
  amount: ['总价', '成交总价', '金额', 'amount', 'total'],
  currency: ['币制', '币种', 'currency'],
  tradeTerms: ['成交方式', '贸易术语', '价格条件', 'tradeTerms', 'terms'],
  origin: ['原产国', '原产国地区', '起运国', 'origin'],
  destination: ['最终目的国', '运抵国', 'destination'],
  grossWeight: ['毛重', 'grossWeight'],
  netWeight: ['净重', 'netWeight'],
  packages: ['件数', '包装件数', 'packages'],
  declaredAt: ['申报日期', '日期', 'declaredAt', 'date'],
  note: ['备注', '说明', 'note', 'remark'],
} as const

/** How the material declares its table. */
export const SPEC: TableSpec = {
  rowKeys: ['rows', 'items', 'documents', '单证'],
  columns: COLUMNS,
  header: {
  declarationNo: ['declarationNo', '报关单号', '提运单号'],
  consignee: ['consignee', '境内收货人', '收发货人', '经营单位'],
  contractNo: ['contractNo', '合同号', '合同协议号'],
  invoiceNo: ['invoiceNo', '发票号'],
  declaredAt: ['declaredAt', '申报日期'],
  },
}

/** Fields the material must carry somewhere for the reader to accept it. */
export const REQUIRE_ANY_OF = [
  '报关单号',
  'declarationNo',
  '单证编号',
  'docNo',
  '商品编号',
  'hsCode',
  '商品名称',
  'goodsName',
]

/**
 * Parse the material and attach its canonical field names.
 * @param source - JSON or YAML text.
 * @param target - description of where the material came from.
 * @returns the normalized table, with each row's aliases resolved to field names.
 */
export function parseMaterial(source: string, target: string): TableInput {
  const table = parseTable(source, target, {
    ...SPEC,
    ...(REQUIRE_ANY_OF === undefined ? {} : { requireAnyOf: REQUIRE_ANY_OF }),
  })
  for (const row of table.rows) canonicaliseRow(row, SPEC)
  return table
}

/**
 * Run the rule pack against the material.
 * @param input - normalized table.
 * @param ruleset - validated rule pack.
 * @param options - plugin identity, clock value, rule selection and overrides.
 * @returns the report.
 */
export function runCheck(input: TableInput, ruleset: Ruleset, options: TableCheckOptions) {
  return runTableCheck(input, ruleset, options)
}

export type { TableCheckOptions, TableInput }
