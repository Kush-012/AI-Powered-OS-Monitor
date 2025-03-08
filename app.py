import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import psutil
import plotly.graph_objs as go
import pandas as pd
import time
from statsmodels.tsa.arima.model import ARIMA

# Initialize the Dash app with a Bootstrap theme and custom CSS
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, 'styles.css'])

# Use dcc.Store to persist data for CPU, Network, and Disk usage
app.layout = html.Div([
    dcc.Store(id='data-store', data={'cpu': [], 'network': [], 'disk': []}),  # Store data as a dictionary
    html.H1("AI-Powered OS Monitor", className="custom-heading"),  # Add a custom class for styling
    dbc.Row([
        dbc.Col([
            html.Div(dcc.Graph(id='live-cpu-graph'), className="graph-card")
        ], width=4),
        dbc.Col([
            html.Div(dcc.Graph(id='live-network-graph'), className="graph-card")
        ], width=4),
        dbc.Col([
            html.Div(dcc.Graph(id='live-disk-graph'), className="graph-card")
        ], width=4),
    ], className="graph-row"),  # Add a custom class for styling
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("CPU Usage Forecast", className="forecast-section"),
                dcc.Graph(id='cpu-forecast-graph')
            ], className="forecast-section")
        ], width=12),
    ]),
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0)  # Update every 2 seconds
], className="dashboard-container")  # Add a custom class for styling

# Callback to update all graphs, store data, and generate forecasts
@app.callback(
    Output('live-cpu-graph', 'figure'),
    Output('live-network-graph', 'figure'),
    Output('live-disk-graph', 'figure'),
    Output('cpu-forecast-graph', 'figure'),
    Output('data-store', 'data'),  # Update the stored data
    Input('interval-component', 'n_intervals'),
    State('data-store', 'data')  # Retrieve the current stored data
)
def update_graphs(n, stored_data):
    try:
        # Debugging: Print stored data
        print("Stored Data:", stored_data)

        # Initialize DataFrames for each metric
        cpu_data = pd.DataFrame(stored_data.get('cpu', [])) if stored_data.get('cpu') else pd.DataFrame(columns=['Time', 'CPU Usage'])
        network_data = pd.DataFrame(stored_data.get('network', [])) if stored_data.get('network') else pd.DataFrame(columns=['Time', 'Network Usage'])
        disk_data = pd.DataFrame(stored_data.get('disk', [])) if stored_data.get('disk') else pd.DataFrame(columns=['Time', 'Disk Usage'])

        # Debugging: Print initial data
        print("CPU Data:", cpu_data)
        print("Network Data:", network_data)
        print("Disk Data:", disk_data)

        # Get current time
        time_stamp = time.strftime("%H:%M:%S")

        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)
        new_cpu_data = pd.DataFrame({'Time': [time_stamp], 'CPU Usage': [cpu_percent]})
        updated_cpu_data = pd.concat([cpu_data, new_cpu_data], ignore_index=True)
        if len(updated_cpu_data) > 100:
            updated_cpu_data = updated_cpu_data.tail(100)

        # Network Usage (bytes sent + received, converted to MB/s)
        network_io = psutil.net_io_counters()
        bytes_total = (network_io.bytes_sent + network_io.bytes_recv) / (1024 * 1024)  # Convert to MB
        if not network_data.empty:
            last_bytes = (network_data['Network Usage'].iloc[-1] * 1024 * 1024)  # Convert back to bytes
            network_rate = (bytes_total * 1024 * 1024 - last_bytes) / (2 * 1024 * 1024)  # MB/s over 2 seconds
        else:
            network_rate = 0  # First measurement, no rate yet
        new_network_data = pd.DataFrame({'Time': [time_stamp], 'Network Usage': [bytes_total]})
        updated_network_data = pd.concat([network_data, new_network_data], ignore_index=True)
        if len(updated_network_data) > 100:
            updated_network_data = updated_network_data.tail(100)

        # Disk Usage
        disk_percent = psutil.disk_usage('/').percent  # Root directory
        new_disk_data = pd.DataFrame({'Time': [time_stamp], 'Disk Usage': [disk_percent]})
        updated_disk_data = pd.concat([disk_data, new_disk_data], ignore_index=True)
        if len(updated_disk_data) > 100:
            updated_disk_data = updated_disk_data.tail(100)

        # Debugging: Print updated data
        print("Updated CPU Data:", updated_cpu_data)
        print("Updated Network Data:", updated_network_data)
        print("Updated Disk Data:", updated_disk_data)

        # Create CPU graph
        cpu_fig = go.Figure(data=[go.Scatter(x=updated_cpu_data['Time'], y=updated_cpu_data['CPU Usage'], mode='lines+markers', line=dict(color='#3498db'))])
        cpu_fig.update_layout(
            title="CPU Usage Over Time",
            xaxis_title="Time",
            yaxis_title="CPU Usage (%)",
            template="plotly_white",
            margin=dict(l=40, r=40, t=40, b=40),
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='#f8f9fa'
        )

        # Create Network graph (showing total MB for simplicity)
        network_fig = go.Figure(data=[go.Scatter(x=updated_network_data['Time'], y=updated_network_data['Network Usage'], mode='lines+markers', line=dict(color='#2ecc71'))])
        network_fig.update_layout(
            title="Network Usage Over Time",
            xaxis_title="Time",
            yaxis_title="Network Usage (MB)",
            template="plotly_white",
            margin=dict(l=40, r=40, t=40, b=40),
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='#f8f9fa'
        )

        # Create Disk graph
        disk_fig = go.Figure(data=[go.Scatter(x=updated_disk_data['Time'], y=updated_disk_data['Disk Usage'], mode='lines+markers', line=dict(color='#e67e22'))])
        disk_fig.update_layout(
            title="Disk Usage Over Time",
            xaxis_title="Time",
            yaxis_title="Disk Usage (%)",
            template="plotly_white",
            margin=dict(l=40, r=40, t=40, b=40),
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='#f8f9fa'
        )

        # Update stored data
        updated_store = {
            'cpu': updated_cpu_data.to_dict('records'),
            'network': updated_network_data.to_dict('records'),
            'disk': updated_disk_data.to_dict('records')
        }

        # Forecasting CPU Usage with ARIMA
        if len(updated_cpu_data) >= 50:  # Ensure enough data points for training
            try:
                # Prepare data for ARIMA
                cpu_series = updated_cpu_data['CPU Usage']
                model = ARIMA(cpu_series, order=(5, 1, 0))  # ARIMA(p, d, q)
                model_fit = model.fit()

                # Forecast the next 10 steps
                forecast_steps = 10
                forecast = model_fit.forecast(steps=forecast_steps)

                # Create forecast graph
                forecast_fig = go.Figure(data=[
                    go.Scatter(x=updated_cpu_data['Time'], y=updated_cpu_data['CPU Usage'], mode='lines+markers', line=dict(color='#3498db'), name='Historical Data'),
                    go.Scatter(x=pd.date_range(start=updated_cpu_data['Time'].iloc[-1], periods=forecast_steps + 1, freq='2S')[1:], y=forecast, mode='lines+markers', line=dict(color='red'), name='Forecast')
                ])
                forecast_fig.update_layout(
                    title="CPU Usage Forecast",
                    xaxis_title="Time",
                    yaxis_title="CPU Usage (%)",
                    template="plotly_white",
                    margin=dict(l=40, r=40, t=40, b=40),
                    plot_bgcolor='#f8f9fa',
                    paper_bgcolor='#f8f9fa'
                )
            except Exception as e:
                print(f"Error in ARIMA forecasting: {e}")
                forecast_fig = go.Figure()  # Return an empty figure if forecasting fails
        else:
            forecast_fig = go.Figure()  # Return an empty figure if not enough data

        return cpu_fig, network_fig, disk_fig, forecast_fig, updated_store

    except Exception as e:
        print(f"Error in callback: {e}")
        # Return last known figures and data if an error occurs
        cpu_data = pd.DataFrame(stored_data.get('cpu', [])) if stored_data.get('cpu') else pd.DataFrame(columns=['Time', 'CPU Usage'])
        network_data = pd.DataFrame(stored_data.get('network', [])) if stored_data.get('network') else pd.DataFrame(columns=['Time', 'Network Usage'])
        disk_data = pd.DataFrame(stored_data.get('disk', [])) if stored_data.get('disk') else pd.DataFrame(columns=['Time', 'Disk Usage'])

        cpu_fig = go.Figure(data=[go.Scatter(x=cpu_data['Time'], y=cpu_data['CPU Usage'], mode='lines+markers', line=dict(color='#3498db'))]) if not cpu_data.empty else go.Figure()
        cpu_fig.update_layout(title="CPU Usage Over Time", xaxis_title="Time", yaxis_title="CPU Usage (%)", template="plotly_white")

        network_fig = go.Figure(data=[go.Scatter(x=network_data['Time'], y=network_data['Network Usage'], mode='lines+markers', line=dict(color='#2ecc71'))]) if not network_data.empty else go.Figure()
        network_fig.update_layout(title="Network Usage Over Time", xaxis_title="Time", yaxis_title="Network Usage (MB)", template="plotly_white")

        disk_fig = go.Figure(data=[go.Scatter(x=disk_data['Time'], y=disk_data['Disk Usage'], mode='lines+markers', line=dict(color='#e67e22'))]) if not disk_data.empty else go.Figure()
        disk_fig.update_layout(title="Disk Usage Over Time", xaxis_title="Time", yaxis_title="Disk Usage (%)", template="plotly_white")

        forecast_fig = go.Figure()  # Return an empty figure if an error occurs

        return cpu_fig, network_fig, disk_fig, forecast_fig, stored_data

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True) 