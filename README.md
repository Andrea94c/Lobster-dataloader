# Lobster-data Reader v1 

## Project scope
Lobster data for multiple days are provided within a big 7z file, which we have to unpack in order to access single days.
In case of 1year of data at level 10, A 7z can required around 5GB of disk space, while its unpacked version even 50-100GB. This library allows to access single days inside the 7z without the need to unpack it. 

## Execution
There are two examples in the lobster_util.py file. 

### OHLC Data
You can run: 
```
import lobster_util 
import config 
ohlc = lobster_util.ohlc_df_from_7z("data/_exampledata_AAPL_2018-01-02_2019-06-02_10.7z",
                                            first_date="2018-02-05", last_date="2018-02-07", 
                                            granularity=config.Granularity.Hour1)
```
to retrieve the data in the classic OHLC format from Febraury 5, 2018 up to Febraury 07, 2018 (both included) with 1-hour candlesticks.
The results is a pandas dataframe


### Messages and Orderbook Data
You can run: 
```
import lobster_util 
orderbook_df, message_df = lobster_util.unpack_from_7z("data/_exampledata_AAPL_2018-01-02_2019-06-02_10.7z",
                                            level=10, first_date="2018-02-05", last_date="2018-02-05")
```
to retrieve all messages and corresponding orderbook data from the first_date to last_date (both included).


### Plot utils
Some plotting utils are provided as well but they are not a stable implementation.

### Requirments 
Please be sure, among other standard libraries, to install **libarchive**.

On ubuntu/linux you can install it by:
```
apt-get install libarchive-dev
pip install libarchive
```

The code was tested on python 3.8.5.

##### March - 2022

## Contacts
For further information contact Andrea Coletta at **coletta[AT]di.uniroma1.it**.

