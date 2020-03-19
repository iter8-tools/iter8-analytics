from fastapi import FastAPI
from iter8_analytics.api.analytics.response_hil import Response
app = FastAPI()


@app.post("/assessment", response_model=Response)
def post():
    resp = {
    "versions": [
    {
      "id": "baseline",
      "win_probability": 0.1,
      "request_count": 500,
      "metrics": [
        {
          "id": "iter8-latency",
          "statistics": {
            "sample_size": 500,
            "value": 0.005,
            "probability_to_be_best_version": 0.3,
            "confidence_interval": {
              "lower": 0,
              "upper": 0
            }
          },
          "success_criterion_assessment": {
            "conclusion": "Baseline version satisfied all success criteria",
            "lower_threshold_breached": False,
            "upper_threshold_breached": False,
            "probability_of_meeting_success_criterion": 1.0
          }
        }
      ]
    },
    {
      "id": "candidate1",
      "win_probability": 0.6,
      "request_count": 1000,
      "metrics": [
        {
          "id": "iter8-latency",
          "statistics": {
            "sample_size": 1000,
            "value": 0.002,
            "improvement": {
              "lower": 0.24,
              "upper": 0.46
            },
            "probability_to_beat_baseline": 0.0,
            "probability_to_be_best_version": 0.0,
            "confidence_interval": {
              "lower": 0.88,
              "upper": 0.93
            }
          },
          "success_criterion_assessment": {
            "conclusion": "Candidate1 version satisfied all success criteria. Candidate2 is the best version",
            "lower_threshold_breached": False,
            "upper_threshold_breached": False,
            "probability_of_meeting_success_criterion": 1.0
          }
        }
      ]
    },
    {
      "id": "candidate2",
      "win_probability": 0.3,
      "request_count": 1100,
      "metrics": [
        {
          "id": "iter8-latency",
          "statistics": {
            "sample_size": 1100,
            "value": 0.004,
            "improvement": {
              "lower": 0.10,
              "upper": 0.12
            },
            "probability_to_beat_baseline": 0.0,
            "probability_to_be_best_version": 0.0,
            "confidence_interval": {
              "lower": 0.85,
              "upper": 0.97
            }
          },
          "success_criterion_assessment": {
            "conclusion": "Candidate2 version satistied all success criteria.",
            "lower_threshold_breached": False,
            "upper_threshold_breached": False,
            "probability_of_meeting_success_criterion": 1.0
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
