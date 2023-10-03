from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)


def cal_pricing(impression_cap):
    try:
        # Load the data
        df = pd.read_csv(r"C:\Users\jency\Downloads\pricing.csv")
        print("Data Loaded:", df.head())  # Debugging line

        # Data cleaning
        # Convert columns to string and replace symbols
        for column in df.columns:
            if df[column].dtype == 'O':  # Check if the column is string type
                df[column] = pd.to_numeric(df[column].astype(str).str.replace('[$,]', '', regex=True), errors='coerce')

        # Ensure 'Monthly Attribution Impression Cap' is int type
        df = df.dropna(subset=['Monthly Attribution Impression Cap'])
        df['Monthly Attribution Impression Cap'] = df['Monthly Attribution Impression Cap'].astype(int)

        # Find the correct tier based on impression cap
        tier_row = df[df['Monthly Attribution Impression Cap'] >= impression_cap].iloc[0]
        print("Tier Row:", tier_row)  # Debugging line

        # Calculate CPM (Cost Per Mille) based on min and max monthly rates
        cpm_low = (tier_row['Monthly Rate (Min)'] / impression_cap) * 1000
        cpm_high = (tier_row['Monthly Rate (Max)'] / impression_cap) * 1000

        # Calculate annual rates
        annual_rate_low = tier_row['Monthly Rate (Min)'] * 12
        annual_rate_high = tier_row['Monthly Rate (Max)'] * 12

        # Extract additional charges and replace NaN with 0 and TRUE with Included
        additional_charges = {
            "Planning Included": tier_row['Planning Included?'],
            "G Sheet Sync Included": tier_row['G Sheet Sync Included?'],
            "Brand Safety Add-on Package": tier_row['Brand Safety Add-on Package'],
            "Dedicated Support Slack Channel": tier_row['Dedicated Support Slack Channel'],
            "Publisher Growth Package": tier_row['Publisher Growth Package']
        }
        additional_charges = {key: (0 if pd.isna(value) else 'Included' if value == 'TRUE' else value)
                              for key, value in additional_charges.items()}

        return {
            "Impression Cap": impression_cap,
            "Tier": tier_row['Tier'],
            "Annual Rate (Low)": annual_rate_low,
            "Annual Rate (High)": annual_rate_high,
            "Monthly Rate (Low)": tier_row['Monthly Rate (Min)'],
            "Monthly Rate (High)": tier_row['Monthly Rate (Max)'],
            "CPM (Low)": cpm_low,
            "CPM (High)": cpm_high,
            "Additional Charges": additional_charges
        }

    except Exception as e:
        # If there's an error anywhere in the function, it will be caught here and returned as a string
        return str(e)


def generate_readable_output(result):
    try:
        message_template = (
            f"Hello [Client Name],\n\n"
            f"Thank you for considering our service. Based on a monthly attribution impression cap of [Impression Cap],"
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

        message = message_template.replace("[Client Name]", "Valued Client")
        message = message.replace("[Impression Cap]", f"{result['Impression Cap']:,}")

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
            impression_cap = int(request.form['impression_cap'])
            result = cal_pricing(impression_cap)

            message = generate_readable_output(result)

        except ValueError:
            error = "Invalid impression cap."

        except Exception as e:
            error = str(e)

    return render_template('index.html', result=result, message=message, error=error)


if __name__ == '__main__':
    app.run(debug=True)
