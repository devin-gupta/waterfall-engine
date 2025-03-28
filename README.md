# waterfall-engine

This is a project aimed at calculating LP and GP allocations for a given project assuming a set of commitments and distributions. You can get started by working through the notebook called 'example.ipynb'.

### example.ipynb

To get started with the example notebook, upload your custom transactions.csv to the root project directory, possibly in the 'waterfall-engine' folder.

Then in your terminal (at the root project path), install your requirements.

```
pip install -r requirements.txt
```

Finally, run all cells in the examples notebook and see the results. The first cell should output a full list of attributes and uses the defined `WaterfallEngine` class. The remaining cells outline the methodology used.

### waterfall.py

This file contains the `WaterfallEngine` class. You can import this class and generate 'reports' via the following parameters:

```
engine = WaterfallEngine(csv_path='transactions.csv')
report = engine.generate_report(commitment_id=4, date='2024-01-01')
```

You can also enter the following optional parameters, which you can find in `__init__()` with more detailed type documentation:

```
engine = WaterfallEngine(
	csv_path='transactions.csv', 
	irr = 0.08, 
        carried_interest_rate = 0.2, 
        catch_up_rate = 1.0, 
        lp_split_rate = 0.8,
)
```

'Reports' is a dataframe which contains the following attributes, you can learn more at the bottom of waterfall.py.

| Stage of Waterfall                                 |                   |                   |                                        |
| -------------------------------------------------- | ----------------- | ----------------- | -------------------------------------- |
| Configuration Metadata                             | commitment_id     | analysis_date     | total_commitment, total_distributions |
| Return of Capital Stage via ['return_of_capital'] | ['lp_allocation'] | ['gp_allocation'] |                                        |
| Preferred Return via ['return_of_capital']        | ['lp_allocation'] | ['gp_allocation'] |                                        |
| Catch Up via ['catch_up']                        | ['lp_allocation'] | ['gp_allocation'] |                                        |
| Final Split via ['final_split']                   | ['lp_allocation'] | ['gp_allocation'] |                                        |
| Totals                                             | total_lp_profit   | total_gp_profit   | profit_split_percentage                |

### Accessing the API

I've also setup a backend setup which you can access and use directly once you have your server running locally by running the following steps.

1. Go to `docker-compose.yml` and build this file. You can do so via hitting 'Run Services' if you have the VSCode Docker IDE running. Now the backend should be running on port 8000 and frontend on port 80 which you can check via:

   ```
   http://localhost:8000
   ```

   This should display 'API is running' if live.
2. To test the method you can run the following curl from the root directory:

```
curl -X POST http://localhost:8000/api/calculate \
	-H "Content-Type: application/json" \
	-d @backend/test.json
```

If you'd like to update the parameters, adjust them in `backend/test.json`.

### Using the Frontend

Make sure you have Docker installed from the [installation guide](https://docs.docker.com/get-docker/). Clone the repository using the following command: 

```
git clone https://github.com/devin-gupta/waterfall-engine.git
```

Navigate to the project directory and build the docker container from the `docker-compose.yml` file.

```
docker compose up --build
```

Now in your native browser you can go to `http://localhost` for the frontend, and the API will be running at `http://localhost:8000`.

---

Built by Devin for the Maybern team!
