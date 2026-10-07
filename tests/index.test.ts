import { describeTablePlugin } from './table-plugin-suite.ts'
import { Config } from '../src/config.ts'
import { parseMaterial, runCheck, SPEC } from '../src/model.ts'
import { buildView } from '../src/view.ts'
import { inject, name, resolvePackageFile, TOOL_NAME } from '../src/index.ts'

describeTablePlugin({
  name,
  inject,
  TOOL_NAME,
  resolvePackageFile,
  Config,
  rulesFile: 'rules/customs-doc-check.yaml',
  parseMaterial,
  runCheck,
  buildView,
  columnNames: SPEC.columns,
  samples: {
    good: {
      declarationNo: '530120260310000001',
      rows: [
        {
          单证种类: '发票',
          单证编号: 'INV-2026-0001',
          商品编号: '8471300000',
          商品名称: '便携式自动数据处理设备',
          数量: '100',
          总价: '45000.00',
          币制: 'USD',
          毛重: '1250.5',
          净重: '1180.0',
          申报日期: '2026-03-10',
        },
      ],
    },
    unknownColumn: { rows: [{ 备注: '甲' }] },
  },
})
