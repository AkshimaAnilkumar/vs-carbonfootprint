
import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()

from dashboard import (
    show_dashboard,
    show_history,
    show_prediction_history
)


# PAGE CONFIGURATION — must come before other Streamlit commands
st.set_page_config(
    page_title="Carbon Footprint Calculator",
    page_icon="🌱",
    layout="wide"
)

# ECO-FRIENDLY UI STYLING

# ECO-FRIENDLY UI STYLING
st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse at top, #ffffff 0%, transparent 55%),
        linear-gradient(135deg, #eef8e9, #e4f3e5, #f5f9ed);
    color: #244d3e;
    font-family: "Segoe UI", sans-serif;
}

.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

h1, h2, h3 {
    color: #176247 !important;
    font-weight: 700 !important;
}

.eco-heading {
    text-align: center;
    padding: 10px 0 20px;
}

.eco-heading h1 {
    font-size: clamp(28px, 4vw, 42px);
    margin-bottom: 8px;
}

.eco-heading p {
    color: #547767;
    font-size: 17px;
}

[data-testid="stForm"],
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid #dcebdd;
    border-radius: 20px;
    box-shadow: 0 12px 35px rgba(29, 78, 55, 0.09);
}

.stTextInput input,
.stNumberInput input,
.stDateInput input {
    border-radius: 11px;
    min-height: 44px;
    border-color: #cfe2d5;
}

.stSelectbox [data-baseweb="select"] > div {
    border-radius: 11px;
}

.stButton > button,
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #167650, #29a875);
    color: white;
    border: none;
    border-radius: 11px;
    min-height: 46px;
    font-weight: 650;
    transition: all 0.2s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: linear-gradient(135deg, #105d3d, #21865d);
    color: white;
    border: none;
    box-shadow: 0 5px 16px rgba(23, 107, 77, 0.18);
}

[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid #dcebdd;
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 5px 18px rgba(29, 78, 55, 0.05);
}

[data-testid="stSidebar"] {
    background: #e7f2e6;
    border-right: 1px solid #d6e6d7;
}

[data-testid="stAlert"] {
    border-radius: 12px;
}

hr {
    border-color: #d5e5d7;
}

.eco-footer {
    text-align: center;
    color: #547767;
    padding: 28px 0 8px;
    font-size: 14px;
}

@media (max-width: 640px) {
    .block-container {
        padding: 1rem;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def close_database_resources(cursor=None, connection=None):
    """Close database resources safely."""
    if cursor is not None:
        try:
            cursor.close()
        except mysql.connector.Error:
            pass

    if connection is not None:
        try:
            if connection.is_connected():
                connection.close()
        except mysql.connector.Error:
            pass


# =========================================================
# PAGE CONFIGURATION
# =========================================================




# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "user_name" not in st.session_state:
    st.session_state.user_name = ""


# =========================================================
# LOGIN / REGISTER
# =========================================================

if not st.session_state.logged_in:

    st.markdown("""
    <div class="eco-heading">
        <h1>🌱 Carbon Footprint Calculator</h1>
        <p>Calculate and monitor your daily carbon footprint.</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    option = st.radio(
        "Choose an option",
        ["Login", "Register"],
        horizontal=True
    )

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    if option == "Login":

        st.markdown(
            "<h2 style='text-align:left;'>🔐 Login</h2>",
            unsafe_allow_html=True
        )

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button("Login", width="stretch"):

            if not email.strip() or not password:
                st.error("Please enter email and password.")

            else:
                connection = None
                cursor = None

                try:
                    connection = get_connection()
                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        SELECT user_id, name, password
                        FROM users
                        WHERE email = %s
                        """,
                        (email.strip(),)
                    )

                    user = cursor.fetchone()

                    if user is None:
                        st.error("No account found with this email.")

                    else:
                        user_id, user_name, stored_password = user

                        # Supports the existing database where passwords
                        # are stored as plain text.
                        if password == stored_password:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.user_name = user_name
                            st.rerun()

                        else:
                            st.error("Incorrect password.")

                except mysql.connector.Error as error:
                    st.error(f"MySQL Error: {error}")

                finally:
                    close_database_resources(cursor, connection)

    # -----------------------------------------------------
    # REGISTER
    # -----------------------------------------------------

    else:

        st.header("📝 Create Account")

        name = st.text_input(
            "Full Name",
            key="reg_name"
        )

        email = st.text_input(
            "Email",
            key="reg_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="reg_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="confirm_password"
        )

        if st.button("Create Account", width="stretch"):

            if not name.strip() or not email.strip():
                st.error("Please enter your name and email.")

            elif not password:
                st.error("Please enter a password.")

            elif password != confirm_password:
                st.error("Passwords do not match.")

            else:
                connection = None
                cursor = None

                try:
                    connection = get_connection()
                    cursor = connection.cursor()

                    cursor.execute(
                        "SELECT user_id FROM users WHERE email = %s",
                        (email.strip(),)
                    )

                    existing_user = cursor.fetchone()

                    if existing_user:
                        st.error(
                            "An account with this email already exists."
                        )

                    else:
                        cursor.execute(
                            """
                            INSERT INTO users (name, email, password)
                            VALUES (%s, %s, %s)
                            """,
                            (name.strip(), email.strip(), password)
                        )

                        connection.commit()

                        st.success(
                            "Account created successfully! Please login."
                        )

                except mysql.connector.Error as error:
                    if connection is not None and connection.is_connected():
                        connection.rollback()

                    st.error(f"MySQL Error: {error}")

                finally:
                    close_database_resources(cursor, connection)
    # FOOTER — displayed on the Login/Register page
    st.markdown("""
    <div class="eco-footer">
    🌿 Small steps. Lower emissions. Better future.
    </div>
    """, unsafe_allow_html=True)



# =========================================================
# MAIN APPLICATION
# =========================================================

else:
    
    # -----------------------------------------------------
    # SIDEBAR AND LOGOUT
    # -----------------------------------------------------

    st.sidebar.title("🌱 Carbon Calculator")

    st.sidebar.success(
        f"Welcome, {st.session_state.user_name}"
    )

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = ""
        st.rerun()

    # -----------------------------------------------------
    # NAVIGATION
    # -----------------------------------------------------

    page = st.sidebar.radio(
        "Navigation",
        ["Carbon Calculator", "Dashboard", "History",    "Prediction History"]
    )

    user_id = st.session_state.user_id
    user_name = st.session_state.user_name

    if page == "Dashboard":
        show_dashboard(user_id, user_name)
        st.stop()

    
    elif page == "History":
        show_history(user_id)
        st.stop()
    elif page == "Prediction History":
        show_prediction_history(user_id)
        st.stop()
    
    # -----------------------------------------------------
    # CARBON CALCULATOR
    # -----------------------------------------------------

    st.title("🌱 AI-Based Carbon Footprint Calculator")

    st.write(
        "Calculate your daily carbon footprint "
        "from different lifestyle activities."
    )

    st.divider()

    # -----------------------------------------------------
    # TRANSPORTATION
    # -----------------------------------------------------

    st.header("🚗 Transportation")

    distance = st.number_input(
        "How many kilometres do you travel by car per day?",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="transport_distance"
    )

    transport_factor = 0.21
    transport_emission = distance * transport_factor

    # -----------------------------------------------------
    # FUEL
    # -----------------------------------------------------

    st.header("⛽ Fuel Consumption")

    fuel = st.number_input(
        "How many litres of fuel do you use per day?",
        min_value=0.0,
        value=0.0,
        step=0.1,
        key="fuel_litres"
    )

    fuel_type = st.selectbox(
        "Select fuel type",
        ["Petrol", "Diesel"],
        key="fuel_type"
    )

    fuel_factor = 2.31 if fuel_type == "Petrol" else 2.68
    fuel_emission = fuel * fuel_factor

    # -----------------------------------------------------
    # FLIGHT
    # -----------------------------------------------------

    st.header("✈️ Flight")

    flight_distance = st.number_input(
        "Flight distance travelled per day (km)",
        min_value=0.0,
        value=0.0,
        step=10.0,
        key="flight_distance"
    )

    flight_factor = 0.15
    flight_emission = flight_distance * flight_factor

    # -----------------------------------------------------
    # ELECTRICITY
    # -----------------------------------------------------

    st.header("⚡ Electricity")

    electricity = st.number_input(
        "How many kWh of electricity do you use per day?",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="electricity_kwh"
    )

    electricity_factor = 0.82
    electricity_emission = electricity * electricity_factor

    # -----------------------------------------------------
    # FOOD
    # -----------------------------------------------------

    st.header("🍽️ Food")

    food = st.selectbox(
        "What type of diet do you mainly follow?",
        ["Vegetarian", "Non-Vegetarian", "Vegan"],
        key="food_habit"
    )

    if food == "Non-Vegetarian":
        food_emission = 3.0
    elif food == "Vegetarian":
        food_emission = 1.7
    else:
        food_emission = 1.2

    # -----------------------------------------------------
    # WASTE
    # -----------------------------------------------------

    st.header("♻️ Waste")

    waste = st.number_input(
        "How many kg of waste do you generate per day?",
        min_value=0.0,
        value=0.0,
        step=0.1,
        key="waste_kg"
    )

    waste_factor = 0.5
    waste_emission = waste * waste_factor

    # -----------------------------------------------------
    # CALCULATE CARBON FOOTPRINT
    # -----------------------------------------------------

    if st.button(
        "🌱 Calculate Carbon Footprint",
        width="stretch"
    ):

        total = (
            transport_emission
            + fuel_emission
            + flight_emission
            + electricity_emission
            + food_emission
            + waste_emission
        )

        # -------------------------------------------------
        # GENERATE RECOMMENDATION
        # -------------------------------------------------

        if total < 5:
            category = "Low"

            suggestion = (
                "Great! Your estimated footprint is relatively low. "
                "Continue following sustainable habits, save electricity, "
                "reduce waste, and use public transport when possible."
            )

        elif total < 10:
            category = "Moderate"

            suggestion = (
                "Your estimated footprint is moderate. Try using public "
                "transport, reducing electricity consumption and waste, "
                "and choosing more plant-based food."
            )

        else:
            category = "High"

            suggestion = (
                "Your estimated footprint is relatively high. Consider "
                "reducing car travel, flights, fuel consumption, electricity "
                "usage, and high-emission foods."
            )

        # -------------------------------------------------
        # SAVE TO MYSQL
        # -------------------------------------------------

        connection = None
        cursor = None
        save_succeeded = False

        try:
            connection = get_connection()
            cursor = connection.cursor()

            # 1. Save activity details.

            cursor.execute(
                """
                INSERT INTO activities
                (
                    user_id,
                    activity_date,
                    transport_km,
                    transport_mode,
                    electricity_kwh,
                    food_habit,
                    fuel_litres,
                    flight_km,
                    waste_kg
                )
                VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    distance,
                    "Car",
                    electricity,
                    food,
                    fuel,
                    flight_distance,
                    waste
                )
            )

            activity_id = cursor.lastrowid

            # 2. Save carbon emissions.

            cursor.execute(
                """
                INSERT INTO carbon_emissions
                (
                    activity_id,
                    user_id,
                    transport_co2,
                    electricity_co2,
                    food_co2,
                    fuel_co2,
                    flight_co2,
                    waste_co2,
                    total_co2
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    activity_id,
                    user_id,
                    transport_emission,
                    electricity_emission,
                    food_emission,
                    fuel_emission,
                    flight_emission,
                    waste_emission,
                    total
                )
            )

            # 3. Save recommendation.
            # This is the new addition.

            cursor.execute(
                """
                INSERT INTO recommendations
                (
                    user_id,
                    category,
                    suggestion
                )
                VALUES (%s, %s, %s)
                """,
                (
                    user_id,
                    category,
                    suggestion
                )
            )

            # Save all three records together.

            connection.commit()
            save_succeeded = True

        except mysql.connector.Error as error:

            if connection is not None and connection.is_connected():
                connection.rollback()

            st.error(f"MySQL Error: {error}")

        finally:
            close_database_resources(cursor, connection)

        # -------------------------------------------------
        # DISPLAY RESULTS AFTER SUCCESSFUL SAVE
        # -------------------------------------------------

        if save_succeeded:

            st.divider()
            st.header("📊 Your Carbon Footprint")

            st.metric(
                "Estimated Daily CO₂ Emission",
                f"{total:.2f} kg CO₂"
            )

            monthly = total * 30
            yearly = total * 365

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Monthly Estimate",
                    f"{monthly:.2f} kg CO₂"
                )

            with col2:
                st.metric(
                    "Yearly Estimate",
                    f"{yearly:.2f} kg CO₂"
                )

            # ---------------------------------------------
            # EMISSION BREAKDOWN
            # ---------------------------------------------

            st.subheader("📌 Emission Breakdown")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "🚗 Transport",
                    f"{transport_emission:.2f} kg"
                )

            with col2:
                st.metric(
                    "⛽ Fuel",
                    f"{fuel_emission:.2f} kg"
                )

            with col3:
                st.metric(
                    "✈️ Flight",
                    f"{flight_emission:.2f} kg"
                )

            col4, col5, col6 = st.columns(3)

            with col4:
                st.metric(
                    "⚡ Electricity",
                    f"{electricity_emission:.2f} kg"
                )

            with col5:
                st.metric(
                    "🍽️ Food",
                    f"{food_emission:.2f} kg"
                )

            with col6:
                st.metric(
                    "♻️ Waste",
                    f"{waste_emission:.2f} kg"
                )

            # ---------------------------------------------
            # EMISSION CHART
            # ---------------------------------------------

            st.subheader("📈 Emission Comparison")

            chart_data = pd.DataFrame({
                "Category": [
                    "Transport",
                    "Fuel",
                    "Flight",
                    "Electricity",
                    "Food",
                    "Waste"
                ],
                "CO₂ Emission (kg)": [
                    transport_emission,
                    fuel_emission,
                    flight_emission,
                    electricity_emission,
                    food_emission,
                    waste_emission
                ]
            })

            fig = px.bar(
                chart_data,
                x="Category",
                y="CO₂ Emission (kg)",
                title="Carbon Emissions by Category",
                labels={
                    "CO₂ Emission (kg)": "CO₂ Emission (kg)"
                }
            )

            st.plotly_chart(fig, width="stretch")

            # ---------------------------------------------
            # SUSTAINABLE RECOMMENDATION
            # ---------------------------------------------

            st.subheader("💡 Sustainable Recommendation")

            st.write(f"**Emission Category: {category}**")

            if category == "Low":
                st.success(suggestion)

            elif category == "Moderate":
                st.warning(suggestion)

            else:
                st.error(suggestion)

            st.success(
                "✅ Activity, carbon emissions, and recommendation "
                "saved successfully to MySQL!"
            )

