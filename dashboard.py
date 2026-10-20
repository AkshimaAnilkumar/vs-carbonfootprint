
import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
from ml_model import predict_next_7_days
import os
from dotenv import load_dotenv

load_dotenv()

# =============================================
# DATABASE CONNECTION
# =============================================

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


# =============================================
# LOAD USER'S CARBON HISTORY
# =============================================

def load_history(user_id):
    connection = get_connection()

    query = """
        SELECT
            a.activity_id,
            a.activity_date,
            a.transport_km,
            a.electricity_kwh,
            a.fuel_litres,
            a.flight_km,
            a.food_habit,
            a.waste_kg,
            c.transport_co2,
            c.electricity_co2,
            c.fuel_co2,
            c.food_co2,
            c.waste_co2,
            c.flight_co2,
            c.total_co2
        FROM activities a
        JOIN carbon_emissions c
          ON a.activity_id = c.activity_id
        WHERE a.user_id = %s
        ORDER BY a.activity_date DESC, a.activity_id DESC
    """

    try:
        df = pd.read_sql(
            query,
            connection,
            params=(user_id,)
        )
        return df
    finally:
        connection.close()


# =============================================
# SAVE 7-DAY AI PREDICTIONS
# =============================================

def save_predictions(user_id, forecast, historical_df):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Calculate average daily historical emissions
        history = historical_df.copy()

        history["activity_date"] = pd.to_datetime(
            history["activity_date"]
        ).dt.normalize()

        history["total_co2"] = pd.to_numeric(
            history["total_co2"],
            errors="coerce"
        )

        daily_history = (
            history.dropna(
                subset=["activity_date", "total_co2"]
            )
            .groupby("activity_date")["total_co2"]
            .sum()
        )

        if daily_history.empty:
            raise ValueError(
                "No valid historical emissions are available."
            )

        average_daily = float(daily_history.mean())

        for _, row in forecast.iterrows():
            prediction_date = pd.to_datetime(
                row["Date"]
            ).strftime("%Y-%m-%d")

            predicted_co2 = float(
                row["Predicted CO2 (kg)"]
            )

            # Relative emission classification
            if predicted_co2 <= average_daily:
                level = "Low"
            elif predicted_co2 <= average_daily * 1.25:
                level = "Moderate"
            else:
                level = "High"

            # Check whether this user already has this date
            cursor.execute(
                """
                SELECT prediction_id
                FROM predictions
                WHERE user_id = %s
                  AND predicted_month = %s
                ORDER BY prediction_id
                LIMIT 1
                """,
                (user_id, prediction_date)
            )

            existing = cursor.fetchone()

            if existing:
                # Update the existing prediction
                cursor.execute(
                    """
                    UPDATE predictions
                    SET predicted_co2 = %s,
                        emission_level = %s
                    WHERE prediction_id = %s
                    """,
                    (
                        predicted_co2,
                        level,
                        existing[0]
                    )
                )
            else:
                # Insert a new prediction
                cursor.execute(
                    """
                    INSERT INTO predictions (
                        user_id,
                        predicted_month,
                        predicted_co2,
                        emission_level
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        prediction_date,
                        predicted_co2,
                        level
                    )
                )

        connection.commit()

        return True, (
            f"{len(forecast)} predictions saved successfully!"
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# =============================================
# DASHBOARD
# =============================================

def show_dashboard(user_id, user_name):

    st.title(f"🌱 Welcome, {user_name}!")
    st.write("Your personal carbon footprint dashboard")

    # Load historical records
    try:
        df = load_history(user_id)

    except mysql.connector.Error as error:
        st.error(f"Database error: {error}")
        return

    if df.empty:
        st.info(
            "No carbon calculations yet. "
            "Visit the Calculator page to create your first record."
        )
        return

    df["activity_date"] = pd.to_datetime(
        df["activity_date"]
    )

    # =============================================
    # SUMMARY METRICS
    # =============================================

    today = pd.Timestamp.today().normalize()
    month_start = today.replace(day=1)

    today_df = df[
        df["activity_date"].dt.normalize() == today
    ]

    month_df = df[
        (df["activity_date"].dt.normalize() >= month_start)
        & (df["activity_date"].dt.normalize() <= today)
    ]

    today_total = today_df["total_co2"].sum()
    month_total = month_df["total_co2"].sum()
    all_time_total = df["total_co2"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Today's CO₂",
        f"{today_total:.2f} kg"
    )

    col2.metric(
        "This Month",
        f"{month_total:.2f} kg"
    )

    col3.metric(
        "All-Time CO₂",
        f"{all_time_total:.2f} kg"
    )

    col4.metric(
        "Calculations",
        len(df)
    )

    # =============================================
    # DAILY EMISSION TREND
    # =============================================

    st.divider()
    st.subheader("📈 Daily Emission Trend")

    daily = (
        df.assign(
            activity_date=df["activity_date"].dt.normalize()
        )
        .groupby("activity_date", as_index=False)["total_co2"]
        .sum()
        .sort_values("activity_date")
    )

    fig = px.line(
        daily,
        x="activity_date",
        y="total_co2",
        markers=True,
        title="Recorded CO₂ Emissions by Date",
        labels={
            "activity_date": "Date",
            "total_co2": "CO₂ (kg)"
        }
    )

    st.plotly_chart(
        fig,
        use_container_width="stretch"
    )

    # =============================================
    # EMISSION BREAKDOWN
    # =============================================

    st.divider()
    st.subheader("📊 Emission Breakdown")

    emission_columns = {
        "Transportation": "transport_co2",
        "Electricity": "electricity_co2",
        "Fuel": "fuel_co2",
        "Food": "food_co2",
        "Waste": "waste_co2",
        "Flight": "flight_co2"
    }

    breakdown = pd.DataFrame({
        "Category": list(emission_columns.keys()),
        "CO₂ (kg)": [
            df[column].fillna(0).sum()
            for column in emission_columns.values()
        ]
    })

    fig = px.bar(
        breakdown,
        x="Category",
        y="CO₂ (kg)",
        title="Total Recorded Emissions by Category"
    )

    st.plotly_chart(
        fig,
        use_container_width="stretch"
    )

    # =============================================
    # AI-BASED 7-DAY PREDICTION
    # =============================================

    st.divider()
    st.subheader("🤖 AI-Based CO₂ Emission Prediction")

    try:
        forecast, message = predict_next_7_days(df)

        if message:
            st.info(message)

        elif forecast is not None and not forecast.empty:

            st.write(
                "Predicted daily emissions for the next "
                "7 days based on your historical records."
            )

            predicted_total = forecast[
                "Predicted CO2 (kg)"
            ].sum()

            st.metric(
                "Predicted CO₂ for Next 7 Days",
                f"{predicted_total:.2f} kg"
            )

            # Prediction chart
            prediction_fig = px.line(
                forecast,
                x="Date",
                y="Predicted CO2 (kg)",
                markers=True,
                title="Predicted Daily Carbon Emissions"
            )

            prediction_fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Predicted CO₂ (kg)"
            )

            st.plotly_chart(
                prediction_fig,
                use_container_width="stretch"
            )

            # Prediction table
            st.dataframe(
                forecast.round(2),
                use_container_width="stretch",
                hide_index=True
            )

            # =============================================
            # SAVE PREDICTIONS BUTTON
            # =============================================

            if st.button(
                "💾 Save 7-Day Predictions",
                key="save_7_day_predictions"
            ):
                try:
                    success, save_message = save_predictions(
                        user_id,
                        forecast,
                        df
                    )

                    if success:
                        st.success(save_message)

                except (
                    mysql.connector.Error,
                    ValueError,
                    KeyError,
                    TypeError
                ) as error:
                    st.error(
                        f"Could not save predictions: {error}"
                    )

        else:
            st.warning(
                "No predictions could be generated."
            )

    except (
        ValueError,
        KeyError,
        TypeError
    ) as error:
        st.error(
            f"Could not generate predictions: {error}"
        )


# =============================================
# CARBON FOOTPRINT HISTORY
# =============================================

def show_history(user_id):

    st.title("📜 Carbon Footprint History")

    try:
        df = load_history(user_id)

    except mysql.connector.Error as error:
        st.error(f"Database error: {error}")
        return

    if df.empty:
        st.info("No previous calculations found.")
        return

    df["activity_date"] = pd.to_datetime(
        df["activity_date"]
    ).dt.strftime("%Y-%m-%d")

    st.dataframe(
        df,
        use_container_width="stretch",
        hide_index=True
    )

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download History as CSV",
        data=csv,
        file_name="carbon_footprint_history.csv",
        mime="text/csv"
    )
    
# =============================================
# AI PREDICTION HISTORY
# =============================================

def show_prediction_history(user_id):

    st.title("📈 AI Prediction History")
    st.write("View your previously saved AI-based CO₂ predictions.")

    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                prediction_id,
                predicted_month,
                predicted_co2,
                emission_level,
                created_at
            FROM predictions
            WHERE user_id = %s
            ORDER BY predicted_month DESC, prediction_id DESC
        """, (user_id,))

        records = cursor.fetchall()
        cursor.close()

        if not records:
            st.info(
                "No predictions found. "
                "Go to Dashboard and save your 7-day predictions first."
            )
            return

        df = pd.DataFrame(
            records,
            columns=[
                "Prediction ID",
                "Prediction Date",
                "Predicted CO₂ (kg)",
                "Emission Level",
                "Saved At"
            ]
        )

        df["Predicted CO₂ (kg)"] = pd.to_numeric(
            df["Predicted CO₂ (kg)"], errors="coerce"
        )

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        col1.metric("Total Predictions", len(df))

        col2.metric(
            "Average Predicted CO₂",
            f"{df['Predicted CO₂ (kg)'].mean():.2f} kg"
        )

        col3.metric(
            "Highest Predicted CO₂",
            f"{df['Predicted CO₂ (kg)'].max():.2f} kg"
        )

        st.divider()

        # Display saved predictions
        st.subheader("📋 Saved Prediction Records")

        st.dataframe(
            df,
            use_container_width="stretch",
            hide_index=True
        )

        # Prediction chart
        st.subheader("📊 Predicted CO₂ Trend")

        chart_df = df.dropna(
            subset=["Predicted CO₂ (kg)"]
        ).copy()

        chart_df["Prediction Date"] = pd.to_datetime(
            chart_df["Prediction Date"], errors="coerce"
        )

        chart_df = chart_df.dropna(
            subset=["Prediction Date"]
        ).sort_values("Prediction Date")

        if not chart_df.empty:
            fig = px.line(
                chart_df,
                x="Prediction Date",
                y="Predicted CO₂ (kg)",
                markers=True,
                title="Saved AI Prediction History"
            )

            st.plotly_chart(
                fig,
                use_container_width="stretch"
            )

        # Download history
        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download Prediction History (CSV)",
            data=csv_data,
            file_name="prediction_history.csv",
            mime="text/csv",
            key="download_prediction_history"
        )

    except mysql.connector.Error as error:
        st.error(f"Database error: {error}")

    finally:
        if connection is not None and connection.is_connected():
            connection.close()

