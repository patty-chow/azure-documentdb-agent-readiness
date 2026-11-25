import os
from src.db import get_db
from src.agents import ScenarioAgent, ReportingAgent
from datetime import datetime


def compute_impact_pipeline(scenario):
    # scenario: {rate_shift_bps, fx_shift_pct}
    rate_shift = scenario.get('rate_shift_bps', 0) / 10000.0  # bps to decimal
    fx_shift = scenario.get('fx_shift_pct', 0.0)
    # Build aggregation that computes impact per position using stored sensitivities
    pipeline = [
        {
            '$project': {
                '_id': 1,
                'account_id': 1,
                'instrument': 1,
                'quantity': 1,
                'market_value': 1,
                'currency': 1,
                'risk_factors': 1,
                'impact_rate': {
                    '$multiply': [ '$quantity', '$market_value', rate_shift, '$risk_factors.rateSensitivity' ]
                },
                'impact_fx': {
                    '$multiply': [ '$quantity', '$market_value', fx_shift, '$risk_factors.fxSensitivity' ]
                }
            }
        },
        {
            '$addFields': {
                'impact_total': { '$add': [ '$impact_rate', '$impact_fx' ] }
            }
        },
        {
            '$group': {
                '_id': None,
                'total_impact': { '$sum': '$impact_total' },
                'by_instrument': { '$push': { 'instrument': '$instrument', 'impact': '$impact_total' } }
            }
        }
    ]
    return pipeline


def run_once():
    db = get_db()
    scenario_agent = ScenarioAgent()
    reporting_agent = ReportingAgent()

    scenario = scenario_agent.generate()
    pipeline = compute_impact_pipeline(scenario)
    print('Running aggregation pipeline with scenario:', scenario)
    res = list(db['positions'].aggregate(pipeline))
    if res:
        summary_doc = res[0]
    else:
        summary_doc = {'total_impact': 0, 'by_instrument': []}

    # Adjusted to match ReportingAgent.synthesize signature
    report = reporting_agent.synthesize(scenario, {'total_pl': summary_doc.get('total_impact')})

    # Persist run
    run_doc = {
        'scenario': scenario,
        'impact_summary': {'total_impact': summary_doc.get('total_impact')},
        'per_instrument': summary_doc.get('by_instrument'),
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'schemaVersion': 1
    }
    db['stress_runs'].insert_one(run_doc)
    print('Report saved.')
    print(report)

if __name__ == '__main__':
    run_once()
