from datetime import datetime

import dash
from dash import html, dcc, no_update, ctx, Input, Output
import pandas as pd
from io import BytesIO
app = dash.Dash(__name__)

# External state hooks (kept from your design)
_get_state = lambda: {}
_clear_data = lambda: {}


def set_dashboard_state_provider(state_provider, clear_callback):
    global _get_state
    _get_state = state_provider

    global _clear_data
    _clear_data = clear_callback


app.layout = html.Div(
    [
        html.H2(
            "📡 TID Monitor 📡",
            style={
                "marginBottom": "20px",
                "color": "#2c3e50",
                "fontWeight": "600",
            },
        ),

        html.Div(
            [
                html.Button(
                    "🧹 Clear Data",
                    id="clear-btn",
                    n_clicks=0,
                    style={
                        "marginBottom": "15px",
                        "padding": "10px 16px",
                        "border": "none",
                        "borderRadius": "6px",
                        "backgroundColor": "#78e0f0",
                        "color": "white",
                        "fontWeight": "600",
                        "cursor": "pointer",
                        "marginRight": "10px",
                    },
                ),

                html.Button(
                    "📥 Export Excel",
                    id="export-btn",
                    n_clicks=0,
                    style={
                        "marginBottom": "15px",
                        "padding": "10px 16px",
                        "border": "none",
                        "borderRadius": "6px",
                        "backgroundColor": "#2ecc71",
                        "color": "white",
                        "fontWeight": "600",
                        "cursor": "pointer",
                    },
                ),
            ]
        ),

        dcc.Download(id="download-excel"),

        dcc.Interval(
            id="interval",
            interval=500,
            n_intervals=0,
        ),

        html.Div(id="table"),
    ],
    style={
        "padding": "30px",
        "backgroundColor": "#f4f6f9",
        "minHeight": "100vh",
        "fontFamily": "Segoe UI, Arial, sans-serif",
        "textAlign": "center",
    },
)


# -----------------------------
# MAIN UPDATE CALLBACK
# -----------------------------
@app.callback(
    Output("table", "children"),
    Input("interval", "n_intervals"),
    Input("clear-btn", "n_clicks"),
)
def update(n_intervals, n_clicks):
    # Handle clear button click
    if ctx.triggered_id == "clear-btn":
        _clear_data()

    epc_map = _get_state()

    if not epc_map:
        return html.Div(
            "No RFID tags received",
            style={
                "padding": "40px",
                "textAlign": "center",
                "color": "#666",
                "fontSize": "18px",
                "background": "white",
                "borderRadius": "10px",
                "boxShadow": "0 2px 8px rgba(0,0,0,.08)",
            },
        )

    header_style = {
        "backgroundColor": "#34495e",
        "color": "white",
        "padding": "14px",
        "textAlign": "left",
        "position": "sticky",
        "top": 0,
        "zIndex": 1,
        "fontWeight": "600",
    }

    cell_style = {
        "padding": "12px 14px",
        "borderBottom": "1px solid #e5e7eb",
        "verticalAlign": "top",
        "textAlign": "left",
    }

    rows = []
    for i, (epc, tag_data) in enumerate(epc_map.items(), start=1):
        tids = sorted(tag_data.tids)
        barcode = tag_data.barcode
        first_seen = datetime.fromtimestamp(
            tag_data.first_seen_at
        ).strftime("%H:%M:%S")

        last_seen = datetime.fromtimestamp(
            tag_data.last_seen_at
        ).strftime("%H:%M:%S")

        reading_time = f"{tag_data.reading_time * 1000:.0f} ms"
        tid_count = str(tag_data.tid_count)
        status = tag_data.status

        rows.append(
            html.Tr(
                [
                    html.Td(i, style={**cell_style, "textAlign": "center", "width": "60px", "fontWeight": "bold"}),
                    html.Td(epc, style={**cell_style, "fontFamily": "Consolas, monospace", "wordBreak": "break-all"}),
                    html.Td(
                        [
                            html.Div(tid, style={"fontFamily": "Consolas, monospace", "fontSize": "13px"})
                            for tid in tids
                        ] if tids else "-",
                        style=cell_style,
                    ),
                    html.Td(barcode, style=cell_style),
                    html.Td(first_seen, style=cell_style),
                    html.Td(last_seen, style=cell_style),
                    html.Td(reading_time, style=cell_style),
                    html.Td(tid_count, style=cell_style),
                    html.Td(
                        status,
                        style={
                            **cell_style,
                            "fontWeight": "bold",
                            "color": "green" if status == "PASSED" else "red",
                        },
                    ),
                ],
                style={"backgroundColor": "#ffffff" if i % 2 else "#f9fafb"},
            )
        )

    return html.Div(
        [
            html.Div(
                f"Total EPCs: {len(epc_map)}",
                style={
                    "padding": "15px 20px",
                    "fontWeight": "600",
                    "fontSize": "16px",
                    "borderBottom": "1px solid #e5e7eb",
                    "backgroundColor": "#fafafa",
                },
            ),

            html.Div(
                html.Table(
                    [
                        html.Thead(
                            html.Tr(
                                [
                                    html.Th("#", style=header_style),
                                    html.Th("EPC", style=header_style),
                                    html.Th("TIDs", style=header_style),
                                    html.Th("Barcode", style=header_style),
                                    html.Th("First Seen", style=header_style),
                                    html.Th("Last Seen", style=header_style),
                                    html.Th("Read Time", style=header_style),
                                    html.Th("Tid Count", style=header_style),
                                    html.Th("Status", style=header_style),
                                ]
                            )
                        ),
                        html.Tbody(rows),
                    ],
                    style={"width": "100%", "borderCollapse": "collapse"},
                ),
                style={"maxHeight": "75vh", "overflowY": "auto"},
            ),
        ],
        style={
            "background": "white",
            "borderRadius": "12px",
            "boxShadow": "0 4px 16px rgba(0,0,0,.08)",
            "overflow": "hidden",
        },
    )


# -----------------------------
# EXCEL EXPORT CALLBACK
# -----------------------------
@app.callback(
    Output("download-excel", "data"),
    Input("export-btn", "n_clicks"),
    prevent_initial_call=True,
)
def export_excel(_):
    epc_map = _get_state()

    rows = []
    for epc, tag_data in epc_map.items():
        rows.append({
            "EPC": epc,
            "TIDs": ", ".join(tag_data.tids),
            "Barcode": tag_data.barcode,
            "First Seen": datetime.fromtimestamp(tag_data.first_seen_at),
            "Last Seen": datetime.fromtimestamp(tag_data.last_seen_at),
            "Read Time (ms)": round(tag_data.reading_time * 1000, 2),
            "TID Count": tag_data.tid_count,
            "Status": tag_data.status,
        })

    df = pd.DataFrame(rows)

    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="RFID_Data")

    buffer.seek(0)

    return dcc.send_bytes(buffer.read(), "rfid_export.xlsx")


def run_dash():
    app.run(
        debug=False,
        use_reloader=False,
        dev_tools_silence_routes_logging=True,
    )