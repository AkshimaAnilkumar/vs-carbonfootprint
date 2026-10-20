
import pandas as pd
from sklearn.linear_model import LinearRegression


def predict_next_7_days(df):
    """
    Predict the next 7 days of CO2 emissions
    using the user's historical daily emissions.
    """

    if df.empty:
        return None, "No historical data available."

    data = df[["activity_date", "total_co2"]].copy()

    data["activity_date"] = pd.to_datetime(
        data["activity_date"]
    ).dt.normalize()

    data["total_co2"] = pd.to_numeric(
        data["total_co2"], errors="coerce"
    )

    data = data.dropna(
        subset=["activity_date", "total_co2"]
    )

    # Combine multiple calculations from the same day.
    daily = (
        data.groupby("activity_date", as_index=False)
        ["total_co2"]
        .sum()
        .sort_values("activity_date")
    )

    # A small dataset is not sufficient for a useful forecast.
    if len(daily) < 4:
        return None, (
            "At least 4 different days of recorded emissions "
            "are needed to generate a preliminary prediction."
        )

    # Convert dates into numbers for the regression model.
    first_date = daily["activity_date"].min()

    daily["day_number"] = (
        daily["activity_date"] - first_date
    ).dt.days

    X = daily[["day_number"]]
    y = daily["total_co2"]

    model = LinearRegression()
    model.fit(X, y)

    # Predict the 7 calendar days after the latest record.
    last_date = daily["activity_date"].max()

    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        periods=7,
        freq="D"
    )

    future_X = pd.DataFrame({
        "day_number": (
            future_dates - first_date
        ).days
    })

    predictions = model.predict(future_X)

    # Emissions cannot be negative.
    predictions = predictions.clip(min=0)

    forecast = pd.DataFrame({
        "Date": future_dates,
        "Predicted CO2 (kg)": predictions
    })

    return forecast, None
