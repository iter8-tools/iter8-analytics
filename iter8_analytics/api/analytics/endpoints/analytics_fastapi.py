from fastapi import FastAPI
from iter8_analytics.api.analytics.response_hil import Response
app = FastAPI()


@app.post("/assessment", response_model=Response)
def post():
    resp = {
    "versions": [
    {
      "id": "string",
      "win_probability": 0,
      "request_count": 0,
      "metrics": [
        {
          "id": "string",
          "statistics": {
            "sample_size": 0,
            "value": 0,
            "improvement": {
              "lower": 0,
              "upper": 0
            },
            "probability_to_beat_baseline": 0,
            "probability_to_be_best_version": 0,
            "confidence_interval": {
              "lower": 0,
              "upper": 0
            }
          },
          "success_criterion_assessment": {
            "conclusion": "string",
            "lower_threshold_breached": True,
            "upper_threshold_breached": True,
            "probability_of_meeting_success_criterion": 0
          }
        }
      ]
    }
  ],
  "traffic_split_recommendation": {
    "recommendation": {
      "pbr": {
        "baseline": 10,
        "candidate1": 60,
        "candidate": 30
      },
      "obr": {
        "baseline": 5,
        "candidate1": 80,
        "candidate2": 15
      }
    }},
    "assessment": {
    "winning_version_found": False,
    "winner": "string",
    "confidence_in_winner": 0,
    "human_consumable_summary": "string"
    },
    "status": 0,
    "last_state": {}
  }
    return resp
