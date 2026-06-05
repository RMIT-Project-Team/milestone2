# VicRoadInsightsNew

Programming Studio project. It lets you
explore Victorian road crash data from 2013 to 2025 you can filter and
summarise crashes by road/weather/light conditions, and by the people involved
(age, sex, road user type, injuries, etc.). All the numbers come straight from
the database, nothing is typed in by hand.

## How to open the website

You need **Python** installed on your computer first. Once you have that:

1. Unzip this folder somewhere easy, like the Desktop.
2. Open the folder so you can see the file app.py
3. Open a command window inside the folder: click the address bar at the top of
   the folder window, type cmd, and press Enter.
4. Install the one thing it needs. Type:

   pip install -r requirements.txt
5. Start the website. Type:
   python app.py
  

6. When you see a line that says Running on http://127.0.0.1:5000, open your
   web browser and go to:

   ```
   localhost:5000
   ```

7. Leave the black command window open while you use the site — it only runs
   while that window is open. To stop it, click the window and press
   **Ctrl + C**.

## What the website is built with

- **Python (Flask)**  the main code that runs the website and gets the data.
- **SQLite**  the database (`Road_Accidents.db`) where all the crash data lives.
- **SQL** the queries that pull, filter, sort, group and join the data.
- **HTML**  the structure of each page (the headings, tables, layout).
- **CSS**  the styling, i.e. how the site looks (colours, spacing, fonts).
- **JavaScript**  makes the pages update instantly when you change a filter,
  without reloading the page.
- **Chart.js**  the small library that draws the donut chart.

## The pages

- **Home** landing page with 4 key facts pulled from the database.
- **About**  the mission, the two users the site is for, and the team
  (all stored in and read from the database).
- **Conditions**  summarises crashes by road, weather and light conditions.
- **People & Injuries**  summarises the people in crashes by age, sex, road
  user type, injuries and ejection, with a donut chart and CSV export.
- **Deep-Dive**  finds the demographic groups with above-average injury risk
  using a nested query one query's result feeds into the next.
>>>>>>> 8022a90 (Update README.md)
