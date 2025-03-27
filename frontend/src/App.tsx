import { useState, DragEvent } from 'react'
import { TextField, Paper, Typography, Button } from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import './App.css'

interface Transaction {
  // Add your transaction interface here
  date: string;
  amount: number;
  type: string;
}

function App() {
  // Required inputs
  const [commitmentId, setCommitmentId] = useState('')
  const [date, setDate] = useState('')
  
  // Optional inputs with defaults
  const [irr, setIrr] = useState(0.08)
  const [carriedInterestRate, setCarriedInterestRate] = useState(0.2)
  const [catchupRate, setCatchupRate] = useState(1)
  const [lpSplitRate, setLpSplitRate] = useState(0.8)
  
  // File and results state
  const [transactions, setTransactions] = useState<Transaction[] | null>(null)
  const [results, setResults] = useState<any>(null)
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
        const rows = text.split('\n').map(row => row.split(','))
        // Assuming CSV has headers: date,amount,type
        const parsedTransactions = rows.slice(1).map(row => ({
          date: row[0],
          amount: parseFloat(row[1]),
          type: row[2]
        })).filter(t => !isNaN(t.amount))
        
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
      fetch('http://localhost:8000/api/calculate', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          input_commitment_id: commitmentId,
          input_date: date,
          transactions,
          irr,
          carried_interest_rate: carriedInterestRate,
          catchup_rate: catchupRate,
          lp_split_rate: lpSplitRate,
        }),
      })
      .then(response => response.json())
      .then(data => {
        setResults(data.data);
        alert('Successfully uploaded data and recieved a response');
      })
      .catch(error => {
        console.error('Error:', error);
        alert('Error processing request');
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
              label="IRR Rate"
              type="number"
              value={irr}
              onChange={(e) => setIrr(parseFloat(e.target.value))}
              className="input-field"
              inputProps={{ step: "0.01" }}
              helperText="Default: 0.08"
            />
            <TextField
              variant="filled"
              label="Carried Interest Rate"
              type="number"
              value={carriedInterestRate}
              onChange={(e) => setCarriedInterestRate(parseFloat(e.target.value))}
              className="input-field"
              inputProps={{ step: "0.01" }}
              helperText="Default: 0.2"
            />
            <TextField
              variant="filled"
              label="Catchup Rate"
              type="number"
              value={catchupRate}
              onChange={(e) => setCatchupRate(parseFloat(e.target.value))}
              className="input-field"
              inputProps={{ step: "0.01" }}
              helperText="Default: 1"
            />
            <TextField
              variant="filled"
              label="LP Split Rate"
              type="number"
              value={lpSplitRate}
              onChange={(e) => setLpSplitRate(parseFloat(e.target.value))}
              className="input-field"
              inputProps={{ step: "0.01" }}
              helperText="Default: 0.8"
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
              <Typography variant="h5" component="h2">Results</Typography>
              <pre>{JSON.stringify(results, null, 2)}</pre>
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
