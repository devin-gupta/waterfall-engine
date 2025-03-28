import csv
import numpy as np
import pandas as pd
from math import isclose
from typing import Dict, List, Tuple, Optional, Any

class WaterfallEngine:
    """
    A class to process and analyze investment waterfall calculations 
    for private equity or venture capital fund distributions.
    
    Implements a standard waterfall distribution model with:
    - Return of Capital
    - Preferred Return
    - Catch-Up Provision
    - Carried Interest Split
    """

    def __init__(
            self, 
            csv_path: str, 
            pref_irr: float = 0.08, 
            carried_interest_percentage: float = 0.2, 
            catch_up_rate: float = 1.0, 
        ):
        """
        Initialize the WaterfallEngine with transaction data.
        
        Args:
            csv_path (str): Path to the CSV file with transaction data
            irr (float, optional): Internal Rate of Return. Defaults to 8%.
        """
        # Core configuration parameters
        self.pref_irr = pref_irr
        self.carried_interest_percentage = carried_interest_percentage
        self.catch_up_rate = catch_up_rate

        # Load and preprocess transaction data
        self.transactions_df = self._load_and_process_transactions(csv_path)

    def _load_and_process_transactions(self, csv_path: str) -> pd.DataFrame:
        """
        Load transactions from CSV and preprocess data.
        
        Args:
            csv_path (str): Path to the transactions CSV file
        
        Returns:
            pd.DataFrame: Processed transactions dataframe
        """
        # Read CSV and convert transaction date and amount
        df = pd.read_csv(csv_path)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='%m/%d/%Y')
        df['transaction_amount'] = df['transaction_amount'].apply(self._clean_amount)
        return df

    @staticmethod
    def _clean_amount(amount_str: str) -> float:
        """
        Clean and convert transaction amount string to float.
        
        Args:
            amount_str (str): Raw transaction amount string
        
        Returns:
            float: Cleaned transaction amount (with proper sign)
        """
        # Remove formatting and handle negative amounts in parentheses
        clean_str = amount_str.strip().replace('$', '').replace(' ', '').replace(',', '')
        is_negative = '(' in clean_str and ')' in clean_str
        clean_str = clean_str.replace('(', '').replace(')', '')
        amount = float(clean_str)
        return -amount if is_negative else amount
    
    def _return_of_capital(self, commitment_id: int, analysis_date: str) -> Dict[str, Any]:
        """
        Calculate return of capital for a specific commitment.
        
        Args:
            commitment_id (int): Unique identifier for the commitment
            analysis_date (str): Date to perform the analysis
        
        Returns:
            Dict with return of capital details
        """
        # Filter transactions for this commitment before the analysis date
        subset_df = self.transactions_df[
            (self.transactions_df['commitment_id'] == commitment_id) &
            (self.transactions_df['transaction_date'] < analysis_date)
        ]

        # Calculate total contributions and distributions
        total_contribution = subset_df[
            subset_df['contribution_or_distribution'] == 'contribution'
        ]['transaction_amount'].sum()

        total_distribution = subset_df[
            subset_df['contribution_or_distribution'] == 'distribution'
        ]['transaction_amount'].sum()

        # Calculate maximum distribution and remaining capital
        max_distribution = min(abs(total_contribution), abs(total_distribution))
        is_capital_returned = total_distribution + total_contribution >= 0

        return {
            'is_completed': is_capital_returned,
            'lp_allocation': max_distribution,
            'gp_allocation': 0,
            'next_tier_capital': total_distribution - max_distribution
        }

    def _preferred_return(self, commitment_id: int, analysis_date: str, roc_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate preferred return for a specific commitment.
        
        Args:
            commitment_id (int): Unique identifier for the commitment
            analysis_date (str): Date to perform the analysis
            roc_result (Dict): Results from return of capital calculation
        
        Returns:
            Dict with preferred return details
        """
        # Validate return of capital is completed
        if not roc_result['is_completed']:
            return {
                'is_completed': False,
                'lp_allocation': 0,
                'gp_allocation': 0,
                'next_tier_capital': 0
            }

        # Filter relevant transactions
        subset_df = self.transactions_df[
            (self.transactions_df['commitment_id'] == commitment_id) &
            (self.transactions_df['transaction_date'] < analysis_date)
        ]

        # Find final distribution date
        final_distribution_date = subset_df['transaction_date'].max()

        # Calculate NPV of contributions
        contribution_npv = sum(
            self._calculate_npv(row['transaction_amount'], self.pref_irr, (final_distribution_date - row['transaction_date']).days)
            for _, row in subset_df.iterrows() 
            if row['contribution_or_distribution'] == 'contribution'
        )

        # Calculate LP allocation with remaining capital
        max_lp_allocation = round(min(
            abs(contribution_npv) - abs(roc_result['lp_allocation']), 
            roc_result['next_tier_capital']
        ), 2)
        
        return {
            'is_completed': True,
            'lp_allocation': max_lp_allocation,
            'gp_allocation': 0,
            'next_tier_capital': roc_result['next_tier_capital'] - max_lp_allocation
        }

    def _catch_up(self, commitment_id: int, analysis_date: str, pref_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate catch-up provision for a specific commitment.
        
        Args:
            commitment_id (int): Unique identifier for the commitment
            analysis_date (str): Date to perform the analysis
            pref_result (Dict): Results from preferred return calculation
        
        Returns:
            Dict with catch-up provision details
        """
        # Validate preferred return is completed
        if not pref_result['is_completed']:
            return {
                'is_completed': False,
                'lp_allocation': 0,
                'gp_allocation': 0,
                'next_tier_capital': 0
            }

        # Calculate total catch-up amount
        total_catch_up = self.carried_interest_percentage * abs(pref_result['lp_allocation']) / (self.catch_up_rate - self.carried_interest_percentage)
        
        # Determine effective catch-up
        effective_catch_up = round(min(total_catch_up, pref_result['next_tier_capital']), 2)

        return {
            'is_completed': total_catch_up <= pref_result['next_tier_capital'],
            'lp_allocation': 0,
            'gp_allocation': effective_catch_up,
            'next_tier_capital': pref_result['next_tier_capital'] - effective_catch_up
        }

    def _final_split(self, commitment_id: int, analysis_date: str, catch_up_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform final profit split for a specific commitment.
        
        Args:
            commitment_id (int): Unique identifier for the commitment
            analysis_date (str): Date to perform the analysis
            catch_up_result (Dict): Results from catch-up provision calculation
        
        Returns:
            Dict with final split details
        """
        # Validate catch-up is completed
        if not catch_up_result['is_completed']:
            return {
                'is_completed': False,
                'lp_allocation': 0,
                'gp_allocation': 0,
                'next_tier_capital': 0
            }

        # Calculate final LP and GP allocations
        lp_allocation = round(catch_up_result['next_tier_capital'] * (1 - self.carried_interest_percentage), 2)
        gp_allocation = round(catch_up_result['next_tier_capital'] * self.carried_interest_percentage, 2)

        return {
            'is_completed': True,
            'lp_allocation': lp_allocation,
            'gp_allocation': gp_allocation,
            'next_tier_capital': 0
        }

    def _calculate_npv(self, value: float, rate: float, days: int) -> float:
        """
        Calculate Net Present Value for a transaction.
        
        Args:
            value (float): Transaction amount
            rate (float): Interest/discount rate
            days (int): Number of days since transaction
        
        Returns:
            float: Net Present Value of the transaction
        """
        return value * (1 + rate) ** (days / 365)

    def _get_total_commitment(self, commitment_id: int, analysis_date: str) -> float:
        """Calculate total capital commitment for a given commitment ID."""
        commitment = self.transactions_df[
            (self.transactions_df['commitment_id'] == commitment_id) & 
            (self.transactions_df['contribution_or_distribution'] == 'contribution') & 
            (self.transactions_df['transaction_date'] < analysis_date)
        ]['transaction_amount'].sum()

        if commitment < 0: 
            commitment = commitment * (-1)
        
        return commitment

    def _get_total_distributions(self, commitment_id: int, analysis_date: str) -> float:
        """Calculate total distributions for a given commitment ID."""
        return self.transactions_df[
            (self.transactions_df['commitment_id'] == commitment_id) & 
            (self.transactions_df['contribution_or_distribution'] == 'distribution') & 
            (self.transactions_df['transaction_date'] < analysis_date)
        ]['transaction_amount'].sum()

    def analyze_commitment(self, commitment_id: int, analysis_date: str) -> Dict[str, any]:
        """
        Perform comprehensive waterfall analysis for a specific commitment.
        
        Args:
            commitment_id (int): Unique identifier for the commitment
            analysis_date (str): Date to perform the analysis
        
        Returns:
            Dict containing detailed waterfall distribution analysis
        """
        # Analyze each stage of the waterfall distribution
        roc_result = self._return_of_capital(commitment_id, analysis_date)
        pref_result = self._preferred_return(commitment_id, analysis_date, roc_result)
        catch_up_result = self._catch_up(commitment_id, analysis_date, pref_result)
        final_split_result = self._final_split(commitment_id, analysis_date, catch_up_result)

        total_initial_commitment = self._get_total_commitment(commitment_id, analysis_date)

        total_lp_profit = roc_result['lp_allocation'] + pref_result['lp_allocation'] + catch_up_result['lp_allocation'] + final_split_result['lp_allocation']
        total_gp_profit = roc_result['gp_allocation'] + pref_result['gp_allocation'] + catch_up_result['gp_allocation'] + final_split_result['gp_allocation']

        profit_split_percentage = (total_lp_profit - total_initial_commitment) / (total_lp_profit + total_gp_profit - total_initial_commitment)

        # Compile comprehensive results
        return {
            'commitment_id': commitment_id,
            'analysis_date': analysis_date,
            'total_commitment': total_initial_commitment,
            'total_distributions': self._get_total_distributions(commitment_id, analysis_date),
            
            # Stage-wise allocations
            'return_of_capital': {
                'lp_allocation': roc_result['lp_allocation'],
                'gp_allocation': roc_result['gp_allocation']
            },
            'preferred_return': {
                'lp_allocation': pref_result['lp_allocation'],
                'gp_allocation': pref_result['gp_allocation']
            },
            'catch_up': {
                'lp_allocation': catch_up_result['lp_allocation'],
                'gp_allocation': catch_up_result['gp_allocation']
            },
            'final_split': {
                'lp_allocation': final_split_result['lp_allocation'],
                'gp_allocation': final_split_result['gp_allocation']
            },

            # Aggregate profit calculations
            'total_lp_profit': round(total_lp_profit, 2),
            'total_gp_profit': round(total_gp_profit, 2),
            'profit_split_percentage': round(profit_split_percentage * 100, 3) / 100
        }

    def generate_report(self, commitment_id: int, analysis_date: str) -> pd.DataFrame:
        """
        Generate a comprehensive waterfall distribution report.
        
        Args:
            commitment_id (int): Unique identifier for the commitment
            analysis_date (str): Date to perform the analysis
        
        Returns:
            pd.DataFrame: Detailed waterfall distribution report
        """
        analysis_result = self.analyze_commitment(commitment_id, analysis_date)
        
        # Convert analysis result to DataFrame for reporting
        report_df = pd.DataFrame([analysis_result])
        # report_df.to_csv('waterfall_report.csv', index=False)
        
        return report_df

if __name__ == "__main__":
    engine = WaterfallEngine('transactions.csv')
    report = engine.generate_report(4, '2022-01-03')
    for index, row in report.iterrows():
        print(f"Commitment ID: {row['commitment_id']}")
        print(f"Analysis Date: {row['analysis_date']}")
        print(f"Total Commitment: {row['total_commitment']}")
        print(f"Total Distributions: {row['total_distributions']}")
        print(f"Return of Capital LP Allocation: {row['return_of_capital']['lp_allocation']}")
        print(f"Return of Capital GP Allocation: {row['return_of_capital']['gp_allocation']}")
        print(f"Preferred Return LP Allocation: {row['preferred_return']['lp_allocation']}")
        print(f"Preferred Return GP Allocation: {row['preferred_return']['gp_allocation']}")
        print(f"Catch-up LP Allocation: {row['catch_up']['lp_allocation']}")
        print(f"Catch-up GP Allocation: {row['catch_up']['gp_allocation']}")
        print(f"Final Split LP Allocation: {row['final_split']['lp_allocation']}")
        print(f"Final Split GP Allocation: {row['final_split']['gp_allocation']}")
        print(f"Total LP Profit: {row['total_lp_profit']}")
        print(f"Total GP Profit: {row['total_gp_profit']}")
        print(f"Profit Split Percentage: {row['profit_split_percentage']}")