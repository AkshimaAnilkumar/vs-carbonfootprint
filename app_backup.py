import streamlit as st
import mysql.connectorimport os
from dotenv import load_dotenv

load_dotenv()


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


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Carbon Footprint Calculator",
    page_icon="🌱",
    layout="wide"
)


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

    st.title("🌱 Carbon Footprint Calculator")

    st.write(
        "Calculate and monitor your daily carbon footprint."
    )

    st.divider()

    option = st.radio(
        "Choose an option",
        ["Login", "Register"],
        horizontal=True
    )

    # =====================================================
    # LOGIN
    # =====================================================

    if option == "Login":

        st.header("🔐 Login")

        email = st.text_input("Email")
        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            if email == "" or password == "":
                st.error(
                    "Please enter email and password."
                )

            else:

                try:

                    connection = get_connection()
                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        SELECT user_id, name, password
                        FROM users
                        WHERE email = %s
                        """,
                        (email,)
                    )

                    user = cursor.fetchone()

                    cursor.close()
                    connection.close()

                    if user is None:

                        st.error(
                            "No account found with this email."
                        )

                    else:

                        user_id = user[0]
                        user_name = user[1]
                        stored_password = user[2]

                        if password == stored_password:

                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.user_name = user_name

                            st.rerun()

                        else:

                            st.error(
                                "Incorrect password."
                            )

                except mysql.connector.Error as error:

                    st.error(
                        f"MySQL Error: {error}"
                    )

    # =====================================================
    # REGISTER
    # =====================================================

    else:

        st.header("📝 Create Account")

        name = st.text_input("Full Name")

        email = st.text_input("Email")

        password = st.text_input(
            "Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        if st.button(
            "Create Account",
            use_container_width=True
        ):

            if name == "" or email == "":
                st.error(
                    "Please enter your name and email."
                )

            elif password == "":
                st.error(
                    "Please enter a password."
                )

            elif password != confirm_password:
                st.error(
                    "Passwords do not match."
                )

            else:

                try:

                    connection = get_connection()
                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        SELECT user_id
                        FROM users
                        WHERE email = %s
                        """,
                        (email,)
                    )

                    existing_user = cursor.fetchone()

                    if existing_user:

                        st.error(
                            "An account with this email already exists."
                        )

                    else:

                        cursor.execute(
                            """
                            INSERT INTO users
                            (name, email, password)
                            VALUES (%s, %s, %s)
                            """,
                            (name, email, password)
                        )

                        connection.commit()

                        st.success(
                            "Account created successfully! "
                            "Please login."
                        )

                    cursor.close()
                    connection.close()

                except mysql.connector.Error as error:

                    st.error(
                        f"MySQL Error: {error}"
                    )


# =========================================================
# MAIN APPLICATION
# =========================================================

else:

    # =====================================================
    # SIDEBAR
    # =====================================================

    st.sidebar.title("🌱 Carbon Calculator")

    st.sidebar.success(
        f"Welcome, {st.session_state.user_name}"
    )

    if st.sidebar.button("🚪 Logout"):

        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = ""

        st.rerun()

    # =====================================================
    # TITLE
    # =====================================================

    st.title("🌱 AI-Based Carbon Footprint Calculator")

    st.write(
        "Calculate your daily carbon footprint "
        "from different lifestyle activities."
    )

    st.divider()


    # =====================================================
    # TRANSPORTATION
    # =====================================================

    st.header("🚗 Transportation")

    distance = st.number_input(
        "How many kilometres do you travel by car per day?",
        min_value=0.0,
        value=0.0,
        step=1.0
    )

    transport_factor = 0.21

    transport_emission = (
        distance * transport_factor
    )


    # =====================================================
    # FUEL
    # =====================================================

    st.header("⛽ Fuel Consumption")

    fuel = st.number_input(
        "How many litres of fuel do you use per day?",
        min_value=0.0,
        value=0.0,
        step=0.1
    )

    fuel_type = st.selectbox(
        "Select fuel type",
        [
            "Petrol",
            "Diesel"
        ]
    )

    if fuel_type == "Petrol":

        fuel_factor = 2.31

    else:

        fuel_factor = 2.68

    fuel_emission = (
        fuel * fuel_factor
    )


    # =====================================================
    # FLIGHT
    # =====================================================

    st.header("✈️ Flight")

    flight_distance = st.number_input(
        "Flight distance travelled per day (km)",
        min_value=0.0,
        value=0.0,
        step=10.0
    )

    flight_factor = 0.15

    flight_emission = (
        flight_distance * flight_factor
    )


    # =====================================================
    # ELECTRICITY
    # =====================================================

    st.header("⚡ Electricity")

    electricity = st.number_input(
        "How many kWh of electricity do you use per day?",
        min_value=0.0,
        value=0.0,
        step=1.0
    )

    electricity_factor = 0.82

    electricity_emission = (
        electricity * electricity_factor
    )


    # =====================================================
    # FOOD
    # =====================================================

    st.header("🍽️ Food")

    food = st.selectbox(
        "What type of diet do you mainly follow?",
        [
            "Vegetarian",
            "Non-Vegetarian",
            "Vegan"
        ]
    )

    if food == "Non-Vegetarian":

        food_emission = 3.0

    elif food == "Vegetarian":

        food_emission = 1.7

    else:

        food_emission = 1.2


    # =====================================================
    # WASTE
    # =====================================================

    st.header("♻️ Waste")

    waste = st.number_input(
        "How many kg of waste do you generate per day?",
        min_value=0.0,
        value=0.0,
        step=0.1
    )

    waste_factor = 0.5

    waste_emission = (
        waste * waste_factor
    )


    # =====================================================
    # CALCULATE
    # =====================================================

    if st.button(
        "🌱 Calculate Carbon Footprint",
        use_container_width=True
    ):

        total = (
            transport_emission
            + fuel_emission
            + flight_emission
            + electricity_emission
            + food_emission
            + waste_emission
        )

        try:

            connection = get_connection()
            cursor = connection.cursor()

            user_id = st.session_state.user_id


            # =================================================
            # INSERT ACTIVITY
            # =================================================

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
                VALUES
                (
                    %s,
                    CURDATE(),
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
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


            # =================================================
            # INSERT CARBON EMISSION
            # =================================================

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
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
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

            connection.commit()

            cursor.close()
            connection.close()


            # =================================================
            # RESULT
            # =================================================

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


            # =================================================
            # BREAKDOWN
            # =================================================

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


            # =================================================
            # RECOMMENDATION
            # =================================================

            st.subheader(
                "💡 Sustainable Recommendation"
            )

            if total < 5:

                st.success(
                    "Great! Your estimated footprint is "
                    "relatively low. Continue following "
                    "sustainable habits."
                )

            elif total < 10:

                st.warning(
                    "Your footprint is moderate. Try using "
                    "public transport, reducing electricity "
                    "consumption, reducing waste and "
                    "choosing more plant-based food."
                )

            else:

                st.error(
                    "Your footprint is relatively high. "
                    "Consider reducing car travel, flights, "
                    "fuel consumption, electricity usage "
                    "and high-emission foods."
                )


            st.success(
                "✅ Your carbon footprint has been saved to MySQL!"
            )


        except mysql.connector.Error as error:

            st.error(
                f"MySQL Error: {error}"
            )