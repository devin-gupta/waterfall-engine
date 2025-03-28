import { useState, DragEvent } from 'react'
import { TextField, Paper, Typography, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import './App.css'

interface Transaction {
  transaction_date: string;
  transaction_amount: string;
  contribution_or_distribution: string;
  commitment_id: number;
}

interface WaterfallResults {
  status: string;
  data: {
    commitment_id: number;
    analysis_date: string;
    total_commitment: number;
    total_distributions: number;
    return_of_capital: { lp_allocation: number; gp_allocation: number };
    preferred_return: { lp_allocation: number; gp_allocation: number };
    catch_up: { lp_allocation: number; gp_allocation: number };
    final_split: { lp_allocation: number; gp_allocation: number };
    total_lp_profit: number;
    total_gp_profit: number;
    profit_split_percentage: number;
  };
}

function App() {
  // Required inputs
  const [commitmentId, setCommitmentId] = useState('')
  const [date, setDate] = useState('')
  
  // Optional inputs with defaults
  const [pref_irr, setIrr] = useState(0.08)
  const [carried_interest_percentage, setCarriedInterestRate] = useState(20)
  const [catch_up_rate, setCatchupRate] = useState(1)
  
  // File and results state
  const [transactions, setTransactions] = useState<Transaction[] | null>(null)
  const [results, setResults] = useState<WaterfallResults | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      processFile(file)
    }
  }

  const processFile = (file: File) => {
    if (file.type === 'text/csv') {
      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target?.result as string
        console.log('Raw CSV content:', text);
        
        // Split by newlines first
        const rows = text.split('\n')
        
        // Parse each row, handling quoted fields properly
        const parsedRows = rows.map(row => {
          // Match fields that are either:
          // - Quoted (handling internal commas): "(.*?)"
          // - Or unquoted (no commas): [^,]+
          const matches = row.match(/(".*?"|[^,]+)(?=\s*,|\s*$)/g) || [];
          return matches.map(field => field.replace(/^"|"$/g, '').trim());
        });
        
        console.log('Parsed CSV rows:', parsedRows);
        
        const parsedTransactions = parsedRows.slice(1).map(row => {
          return {
            transaction_date: row[0].trim(),
            transaction_amount: row[1].trim(), // Keep the original formatting of the amount
            contribution_or_distribution: row[2].trim(),
            commitment_id: parseFloat(commitmentId)
          };
        });
        
        console.log('Parsed transactions:', parsedTransactions);
        
        setTransactions(parsedTransactions)
      }
      reader.readAsText(file)
    }
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    
    const file = event.dataTransfer.files[0]
    if (file) {
      processFile(file)
    }
  }

  const handleProcessTransactions = () => {
    if (transactions && commitmentId && date) {
      const requestBody = {
        input_commitment_id: commitmentId,
        input_date: date,
        transactions,
        pref_irr,
        carried_interest_percentage: carried_interest_percentage / 100,
        catch_up_rate,
      };
      
      console.log('Request body being sent:', requestBody);  // Debug request body
      
      fetch('http://localhost:8000/api/calculate', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })
      .then(response => {
        console.log('Raw response:', response);  // Debug raw response
        return response.json();
      })
      .then(data => {
        console.log('Parsed response data:', data);  // Debug parsed response
        setResults(data);
        // alert('Successfully uploaded data and received a response: ' + JSON.stringify(data));
      })
      .catch(error => {
        console.error('Detailed error:', error);  // More detailed error logging
        // alert('Error processing request');
      })
    } else {
      alert('Please ensure all fields are filled and transactions are uploaded.');
    }
  }

  return (
    <div className="app-container">
      <header>
        <h1>Waterfall Calculator</h1>
      </header>

      <main>
        <section className="inputs-section">
          <div className="required-inputs">
            <TextField
              required
              variant="filled"
              label="Commitment ID"
              value={commitmentId}
              onChange={(e) => setCommitmentId(e.target.value)}
              className="input-field"
            />
            <TextField
              required
              variant="filled"
              type="date"
              label="Date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="input-field"
              InputLabelProps={{ shrink: true }}
            />
          </div>

          <div className="optional-inputs">
            <TextField
              variant="filled"
              label="Preferred IRR"
              type="number"
              value={pref_irr}
              onChange={(e) => setIrr(parseFloat(e.target.value))}
              className="input-field"
              inputProps={{ step: "0.01" }}
            />
            <TextField
              variant="filled"
              label="Carried Interest (%)"
              type="number"
              value={carried_interest_percentage}
              onChange={(e) => setCarriedInterestRate(parseFloat(e.target.value))}
              className="input-field"
              inputProps={{ 
                step: "1",
                min: "0",
                max: "100"
              }}
            />
            <TextField
              variant="filled"
              label="Catchup Rate"
              type="number"
              value={catch_up_rate}
              onChange={(e) => setCatchupRate(parseFloat(e.target.value))}
              className="input-field"
              inputProps={{ step: "0.01" }}
            />
          </div>

          <Paper
            className={`drop-zone ${isDragging ? 'dragging' : ''}`}
            onDrop={handleDrop}
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <CloudUploadIcon className="upload-icon" />
            <Typography variant="h6" component="div">
              {transactions ? 
                `Loaded ${transactions.length} transactions` : 
                'Drop transactions.csv here or click to upload'
              }
            </Typography>
            <input
              type="file"
              id="file-input"
              accept=".csv"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </Paper>

          <Button
            variant="contained"
            color="primary"
            onClick={handleProcessTransactions}
            style={{ marginTop: '1rem' }}
          >
            Process Transactions
          </Button>
        </section>

        <Paper className="results-box">
          {results ? (
            <div>
              <Typography variant="h5" component="h2" gutterBottom>
                Results for Commitment {results.data.commitment_id} on {results.data.analysis_date}
              </Typography>
              
              {/* <Typography variant="subtitle1" gutterBottom>
                Commitment ID: {results.data.commitment_id}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                Analysis Date: {results.data.analysis_date}
              </Typography> */}
              
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Summary
              </Typography>
              <Typography>
                Total Commitment: ${results.data.total_commitment.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </Typography>
              <Typography>
                Total Distributions: ${results.data.total_distributions.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </Typography>
              
              <TableContainer sx={{ mt: 3 }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Category</TableCell>
                      <TableCell align="right">LP Allocation</TableCell>
                      <TableCell align="right">GP Allocation</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>Return of Capital</TableCell>
                      <TableCell align="right">
                        ${results.data.return_of_capital.lp_allocation.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell align="right">
                        ${results.data.return_of_capital.gp_allocation.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Preferred Return</TableCell>
                      <TableCell align="right">
                        ${results.data.preferred_return.lp_allocation.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell align="right">
                        ${results.data.preferred_return.gp_allocation.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Catch Up</TableCell>
                      <TableCell align="right">
                        ${results.data.catch_up.lp_allocation.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell align="right">
                        ${results.data.catch_up.gp_allocation.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Final Split</TableCell>
                      <TableCell align="right">
                        ${results.data.final_split.lp_allocation.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell align="right">
                        ${results.data.final_split.gp_allocation.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>

              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Total Profits
              </Typography>
              <Typography>
                LP Total Profit: ${results.data.total_lp_profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Typography>
              <Typography>
                GP Total Profit: ${results.data.total_gp_profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Typography>
              <Typography>
                Profit Split Percentage: {(results.data.profit_split_percentage * 100).toFixed(1)}%
              </Typography>
            </div>
          ) : (
            <Typography>Upload transactions and fill required fields to see results</Typography>
          )}
        </Paper>
      </main>
    </div>
  )
}

export default App