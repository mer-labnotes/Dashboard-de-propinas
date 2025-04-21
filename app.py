import faicons as fa
import plotly.express as px

# Cargar datos y computar valores estáticos
from shared import app_dir, tips
from shiny import reactive, render
from shiny.express import input, ui
from shinywidgets import render_plotly

# Calcular el rango de valores de facturas para el control deslizante
bill_rng = (min(tips.total_bill), max(tips.total_bill))

# Añadir título de página y opciones
ui.page_opts(title="Restaurant tipping", fillable=True)

# Crear la barra lateral con controles de filtrado
with ui.sidebar(open="desktop"):
    ui.input_slider(
        "total_bill",                # ID del input
        "Bill amount",               # Etiqueta para el usuario
        min=bill_rng[0],             # Valor mínimo
        max=bill_rng[1],             # Valor máximo
        value=bill_rng,              # Valor inicial (rango completo)
        pre="$",                     # Prefijo para los valores
    )
    ui.input_checkbox_group(
        "time",                      # ID del input
        "Food service",              # Etiqueta para el usuario
        ["Lunch", "Dinner"],         # Opciones disponibles
        selected=["Lunch", "Dinner"], # Opciones seleccionadas inicialmente
        inline=True,                 # Mostrar horizontalmente
    )
    ui.input_action_button("reset", "Reset filter") # Botón para reiniciar filtros

# Definir iconos para la interfaz
ICONS = {
    "user": fa.icon_svg("user", "regular"),
    "wallet": fa.icon_svg("wallet"),
    "currency-dollar": fa.icon_svg("dollar-sign"),
    "ellipsis": fa.icon_svg("ellipsis"),
}

# Crear fila de cajas de valores
with ui.layout_columns(fill=False):
    # Primera caja de valor: Total de propinas
    with ui.value_box(showcase=ICONS["user"]):
        "Total tippers"

        @render.express
        def total_tippers():
            tips_data().shape[0]  # Contar filas en los datos filtrados

    # Segunda caja de valor: Propina promedio
    with ui.value_box(showcase=ICONS["wallet"]):
        "Average tip"

        @render.express
        def average_tip():
            d = tips_data()
            if d.shape[0] > 0:
                perc = d.tip / d.total_bill  # Calcular porcentaje de propina
                f"{perc.mean():.1%}"         # Formatear como porcentaje

    # Tercera caja de valor: Factura promedio
    with ui.value_box(showcase=ICONS["currency-dollar"]):
        "Average bill"

        @render.express
        def average_bill():
            d = tips_data()
            if d.shape[0] > 0:
                bill = d.total_bill.mean()  # Calcular factura promedio
                f"${bill:.2f}"              # Formatear como moneda

# Crear diseño principal con tres tarjetas
with ui.layout_columns(col_widths=[6, 6, 12]):
    # Primera tarjeta: Tabla de datos
    with ui.card(full_screen=True):
        ui.card_header("Tips data")

        @render.data_frame
        def table():
            return render.DataGrid(tips_data())
        
# Segunda tarjeta: Gráfico de dispersión
    with ui.card(full_screen=True):
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Total bill vs tip"
            # Menú emergente para opciones de color
            with ui.popover(title="Add a color variable", placement="top"):
                ICONS["ellipsis"]
                ui.input_radio_buttons(
                    "scatter_color",
                    None,
                    ["none", "sex", "smoker", "day", "time"],
                    inline=True,
                )

        # Renderizar el gráfico de dispersión
        @render_plotly
        def scatterplot():
            color = input.scatter_color()
            return px.scatter(
                tips_data(),
                x="total_bill",
                y="tip",
                color=None if color == "none" else color,
                trendline="lowess",  # Añadir línea de tendencia
            )
# Tercera tarjeta: Gráfico de densidad (ridgeplot)
    with ui.card(full_screen=True):
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Tip percentages"
            # Menú emergente para opciones de división
            with ui.popover(title="Add a color variable"):
                ICONS["ellipsis"]
                ui.input_radio_buttons(
                    "tip_perc_y",
                    "Split by:",
                    ["sex", "smoker", "day", "time"],
                    selected="day",  # Valor predeterminado
                    inline=True,
                )

        # Renderizar el gráfico de densidad
        @render_plotly
        def tip_perc():
            from ridgeplot import ridgeplot  # Importamos la función ridgeplot

            # Preparar datos
            dat = tips_data()
            dat["percent"] = dat.tip / dat.total_bill  # Calcular porcentaje de propina
            yvar = input.tip_perc_y()  # Variable para dividir
            uvals = dat[yvar].unique()  # Valores únicos de esa variable

            # Crear muestras para cada valor único
            samples = [[dat.percent[dat[yvar] == val]] for val in uvals]

            # Crear el gráfico ridgeplot
            plt = ridgeplot(
                samples=samples,
                labels=uvals,
                bandwidth=0.01,
                colorscale="viridis",
                colormode="row-index",
            )

            # Ajustar la leyenda
            plt.update_layout(
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5
                )
            )

            return plt

ui.include_css app.dir/

# --------------------------------------------------------
# Cálculos reactivos y efectos
# --------------------------------------------------------

# Función reactiva para filtrar datos según entradas del usuario
@reactive.calc
def tips_data():
    bill = input.total_bill()  # Obtener rango de facturas seleccionado
    idx1 = tips.total_bill.between(bill[0], bill[1])  # Filtrar por factura
    idx2 = tips.time.isin(input.time())  # Filtrar por momento
    return tips[idx1 & idx2]  # Devolver datos filtrados

# Efecto reactivo para restablecer filtros cuando se hace clic en el botón
@reactive.effect
@reactive.event(input.reset)  # Activar cuando se haga clic en "reset"
def _():
    ui.update_slider("total_bill", value=bill_rng)  # Restablecer control deslizante
    ui.update_checkbox_group("time", selected=["Lunch", "Dinner"])  # Restablecer casillas

