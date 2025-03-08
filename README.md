# AI-Powered OS Monitor

![Dashboard Screenshot](screenshot.png) ![image](https://github.com/user-attachments/assets/4ff63583-c977-4d1f-8d0b-997f366ac27e)

The **AI-Powered OS Monitor** is a real-time system monitoring dashboard built using Python, Dash, and Plotly. It provides live updates on CPU, network, and disk usage, along with AI-powered forecasting for CPU usage using the ARIMA time-series model.




## Features

1. **Real-Time Monitoring**:
   - **CPU Usage**: Displays live CPU usage as a percentage.
   - **Network Usage**: Tracks network usage in MB/s.
   - **Disk Usage**: Monitors disk usage as a percentage.

2. **AI-Powered Forecasting**:
   - Uses the **ARIMA** time-series model to predict future CPU usage.
   - Forecasts the next 10 time steps based on historical data.

3. **Interactive Dashboard**:
   - Built using **Dash** and **Plotly** for interactive and responsive graphs.
   - Styled with **Bootstrap** and custom CSS for a modern look.

4. **Data Persistence**:
   - Uses `dcc.Store` to persist historical data across app updates.

5. **Error Handling**:
   - Robust error handling to ensure the app doesn’t crash during data collection or forecasting.

---

## Technologies Used

- **Python**: Core programming language.
- **Dash**: Framework for building the web app.
- **Plotly**: Library for creating interactive graphs.
- **Bootstrap**: For responsive and modern UI components.
- **ARIMA**: Time-series forecasting model.
- **psutil**: Library for system monitoring.

---

## Setup Instructions

### Prerequisites

1. **Python 3.7+**: Ensure Python is installed on your system.
2. **pip**: Python package manager.

