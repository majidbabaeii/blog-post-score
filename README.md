# Blog Post Task

## Installation

To run this project, you'll need to have Docker Compose installed on your system. Follow these steps:

1. Clone this repository to your local machine.
2. Navigate to the project directory.
3. Run the following command:

```bash
docker-compose build
docker-compose up
```

## Configuration for Testing

For testing purposes, I have made the following adjustments:

1. **Reduced Cache Timeout**: The cache timeout has been reduced to a smaller value to facilitate testing.


2. **Reduced Celerybeat Run Period**: The period at which Celerybeat runs has been reduced to a smaller amount for faster
   testing.


3. To facilitate testing, I added 10 normal users and an admin user to the system. Here are the details for the admin
   user:
    ```
   Username: admin
   Password: 1234
   ```


## Handling Sudden Changes in Post Score
To mitigate sudden changes in post scores, the following strategies have been implemented:

1. **Daily Pre-computation of Score**: Scores are pre-computed daily and stored in separate rows for each day. This reduces the amount of computation required to calculate the blog score, as it avoids re-computing scores for each request.


2. **Slope Calculation**: The slope of score change from today to the previous day is calculated. If the slope exceeds the threshold defined in the settings.py file (currently set to 1), the calculation of today's score is delayed until tomorrow. Only scores before today are displayed in such cases.

These strategies help stabilize the scoring system and prevent sudden fluctuations in post scores




## How the System Works
The system operates according to the following workflow:

1. **Adding a Score**: When a user adds or updates a score for a post, the actual post score is not immediately changed. Instead, a Celery task is triggered to calculate and store the score in another table as a chunk of time series data. Currently, the scores are stored daily, but this period can be adjusted dynamically.


2. **Score Calculation**: The Celery task calculates the score and stores it in the time series table. Each chunk of time series data represents a period of time (e.g., a day) and contains the scores for that period.


3. **Updating Scores**: When a user updates their score, the system marks the chunk related to the score object of the user as needing an update. The system then only updates the chunk related to that day, reducing unnecessary calculations for other days.


4. **Displaying Post Score**: The system displays the actual post score based on the sum of all scores in the time series chunk. This ensures that the post score reflects the cumulative scores over the specified period.