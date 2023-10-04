from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)


def cal_pricing(cap_value, cap_type):
    try:
        # Load the data
        df = pd.read_csv("/home/ec2-user/Podscribe_Pricing/data/pricing.csv")
        # df = pd.read_csv("C:\\Users\\jency\\Downloads\\pricing.csv")

        print("Data Loaded:", df.head())  # Debugging line

        # Define column names mapping
        cap_column_mapping = {
            'impression': 'Monthly Attribution Impression Cap',
            'aircheck': 'Airchecks/mo'
        }

        # Data cleaning
        # Convert columns to string and replace symbols
        for column in df.columns:
            if df[column].dtype == 'O':  # Check if the column is string type
                df[column] = pd.to_numeric(df[column].astype(str).str.replace('[$,]', '', regex=True), errors='coerce')

        # Ensure 'Monthly Attribution Impression Cap' is int type
        df = df.dropna(subset=[cap_column_mapping[cap_type]])
        df[cap_column_mapping[cap_type]] = df[cap_column_mapping[cap_type]].astype(int)
        # Find the correct tier based on impression cap
        tier_row = df[df[cap_column_mapping[cap_type]] >= cap_value].iloc[0]
        print("Tier Row:", tier_row)  # Debugging line

        # Calculate CPM (Cost Per Mille) based on min and max monthly rates
        cpm_low = (tier_row['Monthly Rate (Min)'] / cap_value) * 1000
        cpm_high = (tier_row['Monthly Rate (Max)'] / cap_value) * 1000

        # Calculate annual rates
        annual_rate_low = tier_row['Monthly Rate (Min)'] * 12
        annual_rate_high = tier_row['Monthly Rate (Max)'] * 12

        # Extract additional charges and replace NaN with 0 and TRUE with Included
        included_features = {}
        additional_charges = {}

        # Populate the dictionaries based on conditions
        for key, value in {
            "Unlimited Impression Verification": tier_row['Unlimited Impression Verification'],
            "Planning Included": tier_row['Planning Included?'],
            "G Sheet Sync Included": tier_row['G Sheet Sync Included?'],
            "Brand Safety Add-on Package": tier_row['Brand Safety Add-on Package'],
            "Dedicated Support Slack Channel": tier_row['Dedicated Support Slack Channel'],
            "Publisher Growth Package": tier_row['Publisher Growth Package']
        }.items():
            if pd.isna(value) or value in ['TRUE', True]:
                included_features[key] = 'Included'
            else:
                if isinstance(value, str):
                    additional_charges[key] = float(value.strip('$').replace(',', ''))
                else:
                    additional_charges[key] = float(value)

        return {
            "Cap Value": cap_value,
            "Cap Type": cap_type,
            "Tier": tier_row['Tier'],
            "Annual Rate (Low)": annual_rate_low,
            "Annual Rate (High)": annual_rate_high,
            "Monthly Rate (Low)": tier_row['Monthly Rate (Min)'],
            "Monthly Rate (High)": tier_row['Monthly Rate (Max)'],
            "CPM (Low)": cpm_low,
            "CPM (High)": cpm_high,
            "Included Features": included_features,
            "Additional Charges": additional_charges
        }

    except Exception as e:
        return str(e)


def generate_readable_output(result):
    cap_type_placeholder = "[Cap Type]"
    cap_value_placeholder = "[Cap Value]"
    try:
        message_template = (
            f"Hello [Client Name],\n\n"
            f"Thank you for considering our service. Based on a {cap_type_placeholder} of {cap_value_placeholder},"
            f" you fall into our Tier {result['Tier']} pricing. Below are the detailed pricing and features "
            f"available:\n\n"
            f"- Annual Rate: ${result['Annual Rate (Low)']} to ${result['Annual Rate (High)']}\n"
            f"- Monthly Rate: ${result['Monthly Rate (Low)']} to ${result['Monthly Rate (High)']}\n"
            f"- Cost Per Mile (CPM): ${result['CPM (Low)']} to ${result['CPM (High)']}\n\n"
            f"Additional Features and Charges:\n"
        )

        for charge, value in result['Additional Charges'].items():
            # Handling None and 'TRUE' values
            if pd.isna(value) or value == "TRUE":
                message_template += f"  - {charge}: Included\n"
            else:
                message_template += f"  - {charge}: ${value}\n"

        message_template += (
            f"\nFeel free to contact us if you have any questions or need further assistance.\n\n"
            f"Best Regards,\n"
            f"Jency Francis - Podscribe"
        )

        message = message_template.replace(cap_type_placeholder, result['Cap Type'])
        message = message.replace(cap_value_placeholder, f"{result['Cap Value']:,}")
        message = message.replace("[Client Name]", "Valued Client")

        return message
    except Exception as e:
        return str(e)


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    message = None

    if request.method == 'POST':
        try:
            impression_cap = request.form.get('impression_cap')
            aircheck_cap = request.form.get('aircheck_cap')

            if not impression_cap and not aircheck_cap:
                raise ValueError("Please provide either an Impression Cap or an Aircheck Cap")
            if impression_cap and aircheck_cap:
                raise ValueError("Please provide only one of Impression Cap or Aircheck Cap")
            cap_type, cap_value = (
                ('impression', int(impression_cap))
                if impression_cap else ('aircheck', int(aircheck_cap))
            )
            result = cal_pricing(cap_value, cap_type)

            # Check if result is an error message (string) or actual result (dict)
            if isinstance(result, str):
                error = result
                result = None
            else:
                message = generate_readable_output(result)

        except ValueError as ve:
            error = str(ve)
        except Exception as e:
            error = str(e)

    return render_template('index.html', result=result, message=message, error=error)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
