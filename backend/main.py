from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from io import StringIO
from datetime import datetime
from waterfall import WaterfallEngine
import tempfile
import logging

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:80", "http://localhost:3000", "http://localhost:5173"],  # Add Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)

class Transaction(BaseModel):
    transaction_date: str
    transaction_amount: str
    contribution_or_distribution: str
    commitment_id: float

class WaterfallRequest(BaseModel):
    input_commitment_id: float
    input_date: str
    transactions: List[Transaction]
    irr: Optional[float] = 0.08
    carried_interest_rate: Optional[float] = 0.2
    catchup_rate: Optional[float] = 1.0
    lp_split_rate: Optional[float] = 0.8

@app.get("/api/health")  # Updated path to match healthcheck
async def health_check():
    return {"status": "healthy"}

@app.get("/")  # Add root endpoint
async def read_root():
    return {"message": "API is running"}

@app.get("/api/hello")
async def hello_world():
    return {"message": "Hello from FastAPI!"}

@app.post("/api/calculate")
async def calculate_waterfall(request: WaterfallRequest):
    try:
        logging.info(f"Received request: {request}")
        # Convert transactions to DataFrame and save to temporary CSV
        transactions_data = [
            {
                'commitment_id': t.commitment_id,
                'transaction_date': t.transaction_date,
                'transaction_amount': t.transaction_amount,
                'contribution_or_distribution': t.contribution_or_distribution,
            }
            for t in request.transactions
        ]
        
        df = pd.DataFrame(transactions_data)
        
        # Create a temporary file to store the CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            df.to_csv(tmp_file.name, index=False)
            
            # Initialize WaterfallEngine with the temporary CSV file
            engine = WaterfallEngine(
                tmp_file.name,
                irr=request.irr,
                carried_interest_rate=request.carried_interest_rate,
                catch_up_rate=request.catchup_rate,
                lp_split_rate=request.lp_split_rate
            )
            
            # Analyze the commitment
            results = engine.analyze_commitment(
                commitment_id=request.input_commitment_id,
                analysis_date=request.input_date
            )
            
            return {
                "status": "success",
                "data": {
                    "commitment_id": results["commitment_id"],
                    "analysis_date": results["analysis_date"],
                    "total_commitment": float(results["total_commitment"]),
                    "total_distributions": float(results["total_distributions"]),
                    "return_of_capital": {
                        "lp_allocation": float(results["return_of_capital"]["lp_allocation"]),
                        "gp_allocation": float(results["return_of_capital"]["gp_allocation"])
                    },
                    "preferred_return": {
                        "lp_allocation": float(results["preferred_return"]["lp_allocation"]),
                        "gp_allocation": float(results["preferred_return"]["gp_allocation"])
                    },
                    "catch_up": {
                        "lp_allocation": float(results["catch_up"]["lp_allocation"]),
                        "gp_allocation": float(results["catch_up"]["gp_allocation"])
                    },
                    "final_split": {
                        "lp_allocation": float(results["final_split"]["lp_allocation"]),
                        "gp_allocation": float(results["final_split"]["gp_allocation"])
                    },
                    "total_lp_profit": float(results["total_lp_profit"]),
                    "total_gp_profit": float(results["total_gp_profit"]),
                    "profit_split_percentage": float(results["profit_split_percentage"])
                }
            }

    except Exception as e:
        logging.error(f"Error processing request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
