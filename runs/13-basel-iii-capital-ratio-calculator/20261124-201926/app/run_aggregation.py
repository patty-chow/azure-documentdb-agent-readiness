from tools.aggregation_tool import DocumentDBAggregationTool
import json

tool = DocumentDBAggregationTool()
res = tool.aggregate_totals()
print('AGGREGATION RESULT:')
print(json.dumps(res, indent=2))
