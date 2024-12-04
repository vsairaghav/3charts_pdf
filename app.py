import os
import requests
import time
from requests.exceptions import RequestException
from fpdf import FPDF
import streamlit as st


# Function to download charts and create a PDF
def download_charts_to_pdf(symbols, shift=0, scan="default"):
    base_url = "https://www.marketinout.com/chart/servlet.php"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    # Create temporary directory for charts
    output_dir = "charts_download/charts-images"
    os.makedirs(output_dir, exist_ok=True)

    # Initialize PDF
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=5)  # Minimal margins

    with requests.Session() as session:
        for idx, symbol in enumerate(symbols, start=1):
            url = f"{base_url}?s=small&symbol={symbol}&shift={shift}&tp=6&intraday_color=greenred&chart_color=black&ttype=4&tscale=log&tv=0&vs=big&vz=10&show_info=1&show_ohlc=1&hide_val=0&hide_prc=0"
            try:
                response = session.get(url, headers=headers)
                response.raise_for_status()

                # Save the chart as a PNG file
                chart_filename = f"{idx:04d}_{symbol}.png"
                chart_path = os.path.join(output_dir, chart_filename)
                with open(chart_path, "wb") as f:
                    f.write(response.content)

                # Add charts to the PDF (three per page)
                if (idx - 1) % 3 == 0:
                    pdf.add_page()

                # Calculate positions for the charts
                page_width, page_height = 210, 297  # A4 size
                margin = 5
                chart_height = (
                    page_height - 2 * margin - 10
                ) / 3  # Slight space between charts
                chart_width = page_width - 2 * margin

                y_position = margin + ((idx - 1) % 3) * (chart_height + 5)
                pdf.image(
                    chart_path, x=margin, y=y_position, w=chart_width, h=chart_height
                )

                yield f"Added chart for {symbol} to PDF"
            except RequestException as e:
                yield f"Failed to download {symbol}: {e}"
            time.sleep(1)  # Avoid rate limiting

    # Save PDF
    pdf_path = f"charts_download/charts_{scan}.pdf"
    pdf.output(pdf_path)

    # Cleanup temporary directory
    for file in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, file))
    os.rmdir(output_dir)

    yield pdf_path


# Streamlit App UI
st.title("Chart Downloader")

# PIN authentication
PIN = "1234"  # Replace this with your desired PIN
entered_pin = st.text_input(
    "Enter PIN", type="password", placeholder="Enter 4-digit PIN"
)

if entered_pin == PIN:
    st.success("Access granted!")

    # Dropdown to select a scan
    scan = st.selectbox("Select a scan", ["bct4", "ep9"])

    # Input for symbols
    st.write(f"Selected Scan: {scan}")
    symbols_input = st.text_area(
        "Symbols",
        placeholder="Paste one symbol per line, including header if present...",
    )
    shift = st.number_input("Shift (optional)", min_value=0, value=0)

    if st.button("Download Charts"):
        if symbols_input.strip():
            # Split symbols into a list, remove header if present
            symbols = symbols_input.strip().split("\n")
            if symbols[0].lower().startswith("symbols from"):
                symbols = symbols[1:]

            st.write("Starting download...")

            progress_bar = st.progress(0)
            status_text = st.empty()

            # Call the chart download function
            results = []
            pdf_file_path = None
            for idx, result in enumerate(download_charts_to_pdf(symbols, shift, scan)):
                if result.endswith(".pdf"):
                    pdf_file_path = result
                else:
                    results.append(result)
                progress_bar.progress(min((idx + 1) / len(symbols), 1.0))
                status_text.text(result)

            st.success("Download complete!")
            if pdf_file_path:
                with open(pdf_file_path, "rb") as f:
                    # Provide download button for the PDF file
                    st.download_button(
                        label="Download PDF",
                        data=f,
                        file_name=f"charts_{scan}.pdf",
                        mime="application/pdf",
                    )
        else:
            st.error("Please enter at least one symbol.")
else:
    if entered_pin:
        st.error("Incorrect PIN. Please try again.")
