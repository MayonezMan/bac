import streamlit as st
from dataclasses import dataclass
from typing import Literal

Sex = Literal["male", "female"]

@dataclass
class Inputs:
    sex: Sex
    weight_kg: float
    height_cm: float
    age_years: int
    duration_hours: float
    target_bac: float  # in g/dL
    beta: float = 0.015  # elimination rate in g/dL/hour

@dataclass
class Plan:
    tbw_L: float
    tbw_dL: float
    loading_ml: float
    maintenance_ml_per_h: float
    total_ml_for_duration: float
    std_drinks_12g: float
    std_drinks_14g: float

ETHANOL_DENSITY = 0.789  # g/mL

# Common beverages and their alcohol % by volume (ABV)
BEVERAGES = {
    "Beer (5%)": 0.05,
    "Wine (12%)": 0.12,
    "Fortified Wine (18%)": 0.18,
    "Spirits (40%)": 0.40,
}

def watson_tbw_liters(sex: Sex, weight_kg: float, height_cm: float, age_years: int) -> float:
    if sex == "male":
        return 2.447 - 0.09516 * age_years + 0.1074 * height_cm + 0.3362 * weight_kg
    else:
        return -2.097 + 0.1069 * height_cm + 0.2466 * weight_kg


def parse_bac(value: str) -> float:
    s = value.strip().lower().replace(" ", "")
    is_permille = any(x in s for x in ["‰", "permille", "/1000"])
    for suf in ["%", "‰", "permille", "/1000"]:
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    x = float(s)
    if is_permille:
        return x * 0.1
    return x


def make_plan(inp: Inputs) -> Plan:
    tbw_L = watson_tbw_liters(inp.sex, inp.weight_kg, inp.height_cm, inp.age_years)
    tbw_dL = tbw_L * 10.0

    loading_grams = inp.target_bac * tbw_dL
    maintenance_g_per_h = inp.beta * tbw_dL

    total_grams_for_duration = loading_grams + maintenance_g_per_h * inp.duration_hours

    # Convert grams to milliliters using ethanol density
    loading_ml = loading_grams / ETHANOL_DENSITY
    maintenance_ml_per_h = maintenance_g_per_h / ETHANOL_DENSITY
    total_ml_for_duration = total_grams_for_duration / ETHANOL_DENSITY

    std_drinks_12g = total_grams_for_duration / 12.0
    std_drinks_14g = total_grams_for_duration / 14.0

    return Plan(
        tbw_L=tbw_L,
        tbw_dL=tbw_dL,
        loading_ml=loading_ml,
        maintenance_ml_per_h=maintenance_ml_per_h,
        total_ml_for_duration=total_ml_for_duration,
        std_drinks_12g=std_drinks_12g,
        std_drinks_14g=std_drinks_14g,
    )


def ethanol_to_beverage_volume(ethanol_ml: float, abv: float) -> float:
    """Convert pure ethanol mL to beverage volume in mL for given ABV."""
    return ethanol_ml / abv


def main():
    st.title("BAC Planner – Educational Tool")
    st.markdown("Estimate how much alcohol would be required to reach and maintain a certain BAC for a given duration. ⚠️ Educational only – not medical advice.")

    sex = st.selectbox("Sex", ["male", "female"])
    weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, step=0.5)
    height = st.number_input("Height (cm)", min_value=120.0, max_value=220.0, step=0.5)
    age = st.number_input("Age (years)", min_value=15, max_value=100, step=1)
    duration = st.number_input("Duration (hours)", min_value=0.5, max_value=24.0, step=0.5)
    target_bac_input = st.text_input("Target BAC (e.g. 0.05%, 0.5‰)")

    if st.button("Calculate"):
        try:
            target_bac = parse_bac(target_bac_input)
            inp = Inputs(sex, weight, height, age, duration, target_bac)
            plan = make_plan(inp)

            st.subheader("Results (Pure Ethanol)")
            st.write(f"**TBW estimate:** {plan.tbw_L:.2f} L")
            st.write(f"**Loading dose:** {plan.loading_ml:.1f} mL ethanol")
            st.write(f"**Maintenance rate:** {plan.maintenance_ml_per_h:.1f} mL ethanol/hour")
            st.write(f"**Total ethanol for {duration} h:** {plan.total_ml_for_duration:.1f} mL")
            st.write(f"≈ {plan.std_drinks_12g:.1f} × 12g drinks | ≈ {plan.std_drinks_14g:.1f} × 14g drinks")

            st.subheader("Equivalent Beverage Volumes (Total)")
            for name, abv in BEVERAGES.items():
                total_vol = ethanol_to_beverage_volume(plan.total_ml_for_duration, abv)
                st.write(f"**{name}:** {total_vol:.0f} mL total (~{total_vol/1000:.2f} L)")

            st.subheader("Per-Hour Maintenance Suggestion")
            for name, abv in BEVERAGES.items():
                per_hour_vol = ethanol_to_beverage_volume(plan.maintenance_ml_per_h, abv)
                st.write(f"**{name}:** ~{per_hour_vol:.0f} mL per hour")

            st.info("Loading dose is taken at start, maintenance spread evenly per hour. Real metabolism varies – this is only a model.")
        except Exception as e:
            st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
