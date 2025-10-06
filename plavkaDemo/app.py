# app.py
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from model import create_fake_model

server = FastAPI()

model, data = create_fake_model()

dash_app = dash.Dash(__name__)
dash_app.layout = html.Div([
    html.H2("Plavka Jarayonini Prognozlash Demo"),
    dcc.Graph(id='quality-graph'),
    html.Label("Temperature Range:"),
    dcc.RangeSlider(
        id='temp-slider',
        min=int(data['temperature'].min()),
        max=int(data['temperature'].max()),
        step=10,
        value=[int(data['temperature'].min()), int(data['temperature'].max())],
        marks={int(data['temperature'].min()): str(int(data['temperature'].min())),
               int(data['temperature'].max()): str(int(data['temperature'].max()))}
    )
])

@dash_app.callback(
    Output('quality-graph', 'figure'),
    Input('temp-slider', 'value')
)
def update_graph(temp_range):
    filtered = data[(data['temperature'] >= temp_range[0]) & (data['temperature'] <= temp_range[1])]
    filtered = filtered.copy()
    filtered['predicted_quality'] = model.predict(filtered[['temperature','alloy_carbon','alloy_silicon','alloy_manganese']])
    fig = px.scatter(filtered, x='temperature', y='predicted_quality',
                     color='alloy_carbon', hover_data=['alloy_silicon','alloy_manganese'])
    fig.update_layout(title="Plavka Sifat Prognozi")
    return fig

server.mount("/dash", WSGIMiddleware(dash_app.server))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(server, host="0.0.0.0", port=8002)
