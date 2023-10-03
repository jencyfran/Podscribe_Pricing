from flask import Flask, render_template, request
import pandas as pd
import xlrd
import os

app = Flask(__name__)


def cal_pricing(impression_cap):
    try:
        # Load the data
        df = pd.read_csv(r"C:\Users\jency\Downloads\pricing.csv")
        print("Data Loaded:", df.head())  # Debugging line

        # Data cleaning
        # Convert columns to string and replace symbols
        for column in ['Monthly Rate (Min)', 'Monthly Rate (Max)', 'Monthly Attribution Impression Cap']:
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

        return {
            "Tier": tier_row['Tier'],
            "Annual Rate (Low)": annual_rate_low,
            "Annual Rate (High)": annual_rate_high,
            "Monthly Rate (Low)": tier_row['Monthly Rate (Min)'],
            "Monthly Rate (High)": tier_row['Monthly Rate (Max)'],
            "CPM (Low)": cpm_low,
            "CPM (High)": cpm_high,
        }
    except Exception as e:
        # If there's an error anywhere in the function, it will be caught here and returned as a string
        return str(e)


def generate_readable_output(result):
    try:
        # Template for the email/message content
        message_template = (
            f"Hello [Client Name],\n\n"
            f"Thank you for considering our service. Based on a monthly attribution impression cap of [Impression Cap], "
            f"you fall into our Tier {result['Tier']} pricing. Here are the details of this pricing tier:\n\n"
            f"- Annual Rate: ${result['Annual Rate (Low)']} to ${result['Annual Rate (High)']}\n"
            f"- Monthly Rate: ${result['Monthly Rate (Low)']} to ${result['Monthly Rate (High)']}\n"
            f"- Cost Per Mille (CPM): ${result['CPM (Low)']} to ${result['CPM (High)']}\n\n"
            f"Feel free to contact us if you have any questions or need further assistance.\n\n"
            f"Best Regards,\n"
            f"Jency Francis Xavier - Podscribe"
        )

        # Replace placeholders with actual values (if needed)
        message = message_template.replace("[Client Name]", "Valued Client")
        message = message.replace("[Impression Cap]", "500,000")  # Example value
        message = message.replace("[Jency Francis]", "Podscribe")

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
            print("Result:", result)  # Debugging line

            # Generate the message using the results
            if isinstance(result, dict) and 'Tier' in result:
                message = generate_readable_output(result)
            else:
                error = "Unexpected result format."

        except ValueError:
            error = "Invalid impression cap."

        except Exception as e:
            error = str(e)

    return render_template('index.html', result=result, message=message, error=error)


if __name__ == '__main__':
    app.run(debug=True)
