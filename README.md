# bart-weather
## **Introduction**
**bart-weather** is a data science project. It gathers data on departing BART trains across the Bay Area and pairs this with weather information at the departure location.
<br>
<p align = 'center'>
<img src=https://i.imgur.com/5dcTP1s.png alt="LCD with I2C backpack - RPi"
     width="400"><br>
</p><br>

This project can run on any platfrom that supports **Python 3.5** and above.<br>

The approach is simple: BART has a transparent API that transmits a myriad of information. We monitor live updates of when trains are leaving from every BART station in the Bay Area. When the train departs a station, we capture various information about the train and the current weather at its station. The most important factors are the train's delay (in seconds) and the current weather at the station (using geological coordinates).<br>

The information is conitnually written to a CSV file (```BART_weather.csv```) upon detection of a departing train. Please take a look at ```BART_weather.csv``` to view the captured parameters.

## **Python Setup**<br>
This script requires Python 3.5 and above. Please look at requirements.txt for required Python libraries. Clone this repository onto your computer and use pip to install the necessary libraries, like this:<br><br>
```pip install -r requirements.txt``` <br><br>
To run the scipt, open your terminal, navigate to the *bart-weather* directory, and type this:<br><br>
```python LiveBartDataAcquisition.py```<br><br>
This script will run indefinitely until interrupted. To interrupt the script, press *CTRL + C* in your running terminal.<br><br>

## **Project Notes**
The CSV file will continually acquire information until the script is interrupted. It should be noted that there are many trains departing from stations at a given time - the file is expected to grow significantly over time.<br><br>
A couple of interesting ideas for this data are:
- Discovering the station with the most traffic.
- Discovering a relationship between # of train cars with time of day / day of week.
- Discovering a relationship between delays with time of day / day of week.
- Predicting if weather has an influence on train delays.
<br><br>

## **Further Implementation**
Preferably, the ```BART_weather.csv``` file will be divided into various days, for example ```20200108_BART_weather.csv``` to indicate all data collected on January 08, 2020.<br>
This will be implemented in the near future.

