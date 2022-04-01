import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import colors
from matplotlib.legend_handler import *
from datetime import datetime, timedelta
import lobster_util as lu
import config as config
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def load_column_from_ohcl(symbols, format_file, column="close", pickled_data=False) -> pd.DataFrame:
    """
    Read a column for a bunch of sumbols

    :param symbols: the symbols to read into a unique df
    :param format_file: the format of the files (e.g., data/ohcl_data/sec/{}.bz2)
    :param column: the column to read for each symbol (the column will be renamed by name symbol)
    :return: the dataframe
    """
    out_df = None
    for sym in symbols:
        if pickled_data:
            df = pd.read_pickle(format_file.format(sym))
        else:
            df = pd.read_pickle(format_file.format(sym))
        if out_df is None:
            out_df = df
            out_df[sym] = out_df[column]
            out_df = out_df[[sym]]
        else:
            out_df[sym] = df[column]
    return out_df

def save_df_to_bz(df: pd.DataFrame, filename: str) -> None:
    """ save a dataframe with an efficient compression into filename file (please use .bz2 extension)

    :param df: the dataframe to save
    :param filename: the path where save the dataframe (use .bz2 extension)
    :return: nothing
    """
    assert ".bz2" in filename
    df.to_pickle(filename)

def load_df_from_bz(filename: str) -> pd.DataFrame:
    return pd.read_pickle(filename)


def plot_symbols(list_df: list, plot: bool = True, filename: str = None) -> None:
    """
    Plot or Save the "close" of each period for the symbols

    :param list_df: the list of symbols to plot/save. The list is: [(df1, synname1), (df2, symname2), ...]
    :param plot: whether plot or not the symbols
    :param filename: wheter save or not (and where) the plot
    :return:  None
    """
    # Create traces
    fig = go.Figure()
    for df, syn_name in list_df:
        fig.add_trace(go.Scatter(x=df.index, y=df["close"] / float(df[1:2]["close"]),
                                 mode='lines+markers',
                                 name=syn_name))
    if filename is not None:
        fig.write_html(filename)
    if plot:
        fig.show()


def plot_candlestick(df: pd.DataFrame, filename: str = None, plot: bool = True) -> None:
    """
    use plotly to plot candle stick

    :param df: the input data, the df should contains: date, open, high, low, close
    :param filename: where (if not None) save the output html file
    :param plot: it display or not the data
    :return: None
    """
    trace1 = go.Candlestick(x=df.index,
                            open=df['open'],
                            high=df['high'],
                            low=df['low'],
                            close=df['close'], name="Candlestick")

    # add volume
    trace2 = go.Bar(x=df.index, y=df["volume"], name='Volume')

    # add orders
    trace3 = go.Bar(x=df.index, y=df["norders"], name='Number of orders')

    go.Bar()
    fig = make_subplots(rows=5, cols=1,
                        specs=[
                            [{'rowspan': 2}],
                            [None],
                            [{}],
                            [{}],
                            [{}],
                        ])
    fig.update_layout(xaxis_rangeslider_thickness=0.04)
    # Add range slider
    fig.add_trace(trace1)
    fig.add_trace(trace2, row=4, col=1)
    fig.add_trace(trace3, row=5, col=1)
    fig['layout'].update(title="Candlestick Chart", xaxis=dict(tickangle=-90
                                                               ))

    if plot:
        fig.show()
    # if filename is not None:
    fig.write_html("prova.html")


def candlestick_from_7z(sym_7z: str, startdate: str, lastdate: str, granularity: config.Granularity) -> None:
    """ use plotly to plot candle stick

        the input df should contains: date, open, high, low, close
    """
    lu.from_7z_to_unique_df(sym_7z, startdate, lastdate, granularity=granularity, plot=True, level=1)


def gradient_color(lenght: int, cmap: str = "brg") -> list:
    """
    :param lenght: the len of colors to create
    :return: a list of different matplotlib colors
    """
    t_colors = []
    paired = plt.get_cmap(cmap)
    for i in range(lenght):
        c = paired(i / float(lenght))
        t_colors += [colors.to_hex(c)]
    return t_colors
