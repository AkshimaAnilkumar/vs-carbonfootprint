
import pandas as pd
from ml_model import predict_next_7_days

# Sample historical emissions for 7 different days
df = pd.DataFrame({
    "activity_date": [
        "2026-10-01",
        "2026-10-02",
        "2026-10-03",
        "2026-10-04",
        "2026-10-05",
        "2026-10-06",
        "2026-10-07"
    ],
    "total_co2": [10, 12, 11, 14, 15, 13, 16]
})

forecast, error = predict_next_7_days(df)

if error:
    print("Prediction message:", error)
else:
    print("\nNext 7 Days CO2 Prediction:")
    print(forecast.to_string(index=False))
