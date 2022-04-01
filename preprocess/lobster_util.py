# NOTICE: on ubuntu/linux please install :
#  - "apt-get install libarchive-dev"
#  and then  use
#  - "pip3 install libarchive"
import libarchive.public
import re
import pandas as pd

from datetime import datetime, timedelta
import utils as utils
import config as config

COLUMNS_NAMES = {"orderbook": ["sell", "vsell", "buy", "vbuy"],
                 "message": ["time", "event_type", "order_id", "size", "price", "direction", "unk"]}

def message_columns():
    """ return the message columns for the LOBSTER orderbook """
    return COLUMNS_NAMES["message"]

def orderbook_columns(level : int):
    """ return the column names for the LOBSTER orderbook, acording the input level """
    orderbook_columns = []
    for i in range(1, level + 1):
        orderbook_columns += [col + str(i) for col in COLUMNS_NAMES["orderbook"]]
    return  orderbook_columns

def ohlc_df_from_7z(file_7z: str, first_date: str = "1990-01-01",
                         last_date: str = "2100-01-01",
                         plot: bool = False,
                         granularity: config.Granularity = config.Granularity.Hour1) -> pd.DataFrame:
    """ read the input 7z lobster file and return a ohlc df with the selected granularity 

        both first_date and last_date are included in the output!!
    """
    message_dfs = read_7z_sub_routine(file_7z, first_date, last_date, "message", level=1)

    ohlcs = []
    for d in sorted(message_dfs.keys()):
        ohlc_df = lobster_to_ohlc(message_dfs[d], d, granularity=granularity)
        ohlcs.append(ohlc_df)

    ohlc = pd.concat(ohlcs, ignore_index=False)

    if plot:
        utils.plot_candlestick(ohlc)

    return ohlc

def unpack_from_7z(file_7z: str, level : int, first_date: str = "1990-01-01",
                         last_date: str = "2100-01-01") -> tuple:
    """ return a tuple with all the messages and orderbook extracted from the 7z

        Note: the level should be exactly as the level of the input file.
            It cannot be used to filter-out un-wanted levels!
        
        both first_date and last_date are included in the output!!


    """
    message_dfs = read_7z_sub_routine(file_7z, first_date, last_date, "message", level=level)
    orderbook_dfs = read_7z_sub_routine(file_7z, first_date, last_date, "orderbook", level=level)
    
    keys_mess = sorted(orderbook_dfs.keys())
    keys_order = sorted(message_dfs.keys())  
    assert keys_mess == keys_order

    messages = []
    orderbooks = []
    assert list(message_dfs.keys()) == list(orderbook_dfs.keys()), "the messages and orderbooks have different days!!"
    for d in keys_mess:
        # ADD DATE
        ord_df = orderbook_dfs[d]
        msg_df = message_dfs[d]

        # convert the time to seconds and structure the df to the input granularity
        ord_df["seconds"] = msg_df["time"]
        ord_df["date"] = ord_df["seconds"].apply(lambda x: d + timedelta(seconds=x))
        msg_df["date"] = ord_df["date"]

        ord_df.index = ord_df["date"]
        msg_df.index = msg_df["date"]

        orderbooks.append(ord_df)
        messages.append(msg_df)

    orderbook_df = pd.concat(orderbooks, ignore_index=False)
    message_df = pd.concat(messages, ignore_index=False)

    assert len(message_df) == len(orderbook_df)

    return orderbook_df, message_df
    

def read_7z_sub_routine(file_7z: str, first_date: str = "1990-01-01",
                         last_date: str = "2100-01-01",
                         type_file: str = "orderbook",
                        level : int = 1) -> dict:
    """
        :param file_7z: the input file where the csv with data are stored
        :param first_date: the first day to load from the input file
        :param last_date: the last day to load from the input file
        :param type_file: the kind of data to read. type_file in ("orderbook", "message")
        :param level: the LOBSTER level of the orderbook
        :return: a dictionary with {day : dataframe}
    """
    assert type_file in ("orderbook", "message"), "The input type_file: {} is not valid".format(type_file)

    columns = message_columns() if type_file == "message" else orderbook_columns(level)
    # if both none then we automatically detect the dates from the 7z files
    first_date = datetime.strptime(first_date, "%Y-%m-%d")
    last_date = datetime.strptime(last_date, "%Y-%m-%d")

    all_period = {}  # day :  df
    with open(file_7z, 'rb') as f:
        buffer_ = f.read()
        with libarchive.public.memory_reader(buffer_) as e:
            for entry in e:

                # read only the selected type of file
                if type_file not in str(entry):
                    continue

                # read only the data between first_ and last_ input dates
                m = re.search(r".*([0-9]{4}-[0-9]{2}-[0-9]{2}).*", str(entry))
                if m:
                    entry_date = datetime.strptime(m.group(1), "%Y-%m-%d")
                    if entry_date > last_date:
                        break
                    if entry_date < first_date or entry_date > last_date:
                        continue
                else:
                    print("error for file: {}".format(entry))
                    continue
                print("Reading", entry_date, type_file)
                # actually read and create the dataframe
                text = ""
                for b in entry.get_blocks():
                    text += b.decode("utf-8")
                text = text[:-1]
                if type_file == "orderbook":
                    # load only the input level suggest 
                    df = pd.DataFrame([x.split(',')[:len(columns)] for x in text.split('\n')],
                                  columns=columns, dtype="float64")
                else:
                    df = pd.DataFrame([x.split(',') for x in text.split('\n')],
                                  columns=columns, dtype="float64")
                # put types
                all_period[entry_date] = df

    return all_period


def lobster_to_ohlc(message_df,
                    datetime_start: datetime,
                    granularity: config.Granularity = config.Granularity.Sec1,
                    plot=False):
    """ create an ohlc from the messages

        message_df : a csv df with the messages (lobster data format) without initial start lob
        datetime_start : should be a start date in the message file and orderbook file
        granularity : the granularity to use in the mid-prices computation
        plot : whether print or not the mid_prices
        level : the level of the data
    """
    start_date = datetime_start

    # to be sure that columns are okay
    message_df.columns = message_columns()

    # convert the time to seconds and structure the df to the input granularity
    message_df["date"] = [start_date + timedelta(seconds=i) for i in message_df["time"]]
    message_df.index = message_df["date"]

    # use only executed to compute the ohlc
    df_m_executed = message_df[(message_df["event_type"].isin([config.OrderEvent.EXECUTION.value,
                                                               config.OrderEvent.HIDDEN_EXECUTION.value]))]

    # compute the open, high, low, close fields
    ohlc_df = df_m_executed[["price", "size", "order_id"]].resample(granularity.value).agg({"price" : 'ohlc',
                                                                                            "size" : 'sum',
                                                                                            "order_id" : "count"})
    ohlc_df.columns = ["open", "high", "low", "close", "volume", "n-orders"]

    # fill empty data (NaN candle due to empty lob)
    ohlc_df[["volume", "norders"]] = ohlc_df[["volume", "n-orders"]].fillna(0)
    ohlc_df["close"] = ohlc_df["close"].fillna(method="ffill")
    cond = pd.isna(ohlc_df["open"])
    ohlc_df.loc[cond, ["open", "low", "high"]] = ohlc_df.loc[cond, "close"]

    # plot them
    if plot:
        utils.plot_candlestick(ohlc_df, plot=True)

    return ohlc_df

# some code just to test the scripts
if __name__ == "__main__":
    
    # test ohlc
    test_ohlc = True
    if test_ohlc:
        ohlc = ohlc_df_from_7z("data/_exampledata_AAPL_2018-01-02_2019-06-02_10.7z",
                                            first_date="2018-02-05", last_date="2018-02-07")

        print("ohlc")
        print(ohlc)

    # test messages - orderbook    
    test_unpack = True
    if test_unpack:
        orderbook_df, message_df = unpack_from_7z("data/_exampledata_AAPL_2018-01-02_2019-06-02_10.7z",
                                            level=10, first_date="2018-02-05", last_date="2018-02-05")

        print("orderbook:")
        print(orderbook_df)
        print("messages:") 
        print(message_df)
