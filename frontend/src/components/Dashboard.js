import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { walletService, transactionService } from '../services/api';
import { formatCurrency, formatDate, formatTransactionType } from '../utils/format';
import LoadingSpinner from './LoadingSpinner';

const Dashboard = () => {
  const { user } = useAuth();
  const [wallet, setWallet] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch wallet balance
        const walletResponse = await walletService.getBalance();
        setWallet(walletResponse.data);
        
        // Fetch recent transactions
        const transactionsResponse = await transactionService.getTransactions({ limit: 5 });
        setTransactions(transactionsResponse.data.transactions);
        
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error('Dashboard error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.full_name}!
        </h1>
        <p className="mt-2 text-gray-600">
          Here's what's happening with your stablecoin wallet today.
        </p>
      </div>

      {/* Balance cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="balance-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="balance-label">JD Balance</p>
              <p className="balance-display">
                {formatCurrency(wallet?.jd_balance || 0, 'JD')}
              </p>
            </div>
            <div className="text-white text-3xl opacity-80">
              💰
            </div>
          </div>
          <div className="quick-actions">
            <Link to="/wallet" className="quick-action-btn">
              Add Funds
            </Link>
            <Link to="/wallet" className="quick-action-btn">
              Transfer
            </Link>
          </div>
        </div>

        <div className="balance-card-secondary">
          <div className="flex items-center justify-between">
            <div>
              <p className="balance-label">Stablecoin Balance</p>
              <p className="balance-display">
                {formatCurrency(wallet?.stablecoin_balance || 0, 'STABLECOIN')}
              </p>
            </div>
            <div className="text-white text-3xl opacity-80">
              🪙
            </div>
          </div>
          <div className="quick-actions">
            <Link to="/wallet" className="quick-action-btn">
              Exchange
            </Link>
            <Link to="/wallet" className="quick-action-btn">
              Send
            </Link>
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Link
          to="/wallet"
          className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
        >
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">💳</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Manage Wallet</h3>
              <p className="text-sm text-gray-600">Add funds, exchange currencies</p>
            </div>
          </div>
        </Link>

        <Link
          to="/open-banking"
          className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
        >
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🏦</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Open Banking</h3>
              <p className="text-sm text-gray-600">Connect bank accounts</p>
            </div>
          </div>
        </Link>

        <Link
          to="/transactions"
          className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
        >
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">📈</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">View Transactions</h3>
              <p className="text-sm text-gray-600">Track your payment history</p>
            </div>
          </div>
        </Link>

        <Link
          to="/hey-dinar"
          className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
        >
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 bg-yellow-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🤖</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Hey Dinar</h3>
              <p className="text-sm text-gray-600">AI financial assistant</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Recent transactions */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Recent Transactions</h2>
          <Link
            to="/transactions"
            className="text-indigo-600 hover:text-indigo-700 font-medium text-sm"
          >
            View all
          </Link>
        </div>

        {transactions.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-6xl mb-4">📭</div>
            <p className="text-gray-500">No transactions yet</p>
            <p className="text-sm text-gray-400">
              Start by adding funds to your wallet
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {transactions.map((transaction) => (
              <div
                key={transaction.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 bg-indigo-100 rounded-full flex items-center justify-center">
                    <span className="text-indigo-600 font-semibold">
                      {transaction.transaction_type === 'deposit' ? '↗' : 
                       transaction.transaction_type === 'withdrawal' ? '↙' : 
                       transaction.transaction_type === 'exchange' ? '⇄' : '↔'}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">
                      {formatTransactionType(transaction.transaction_type)}
                    </p>
                    <p className="text-sm text-gray-500">
                      {formatDate(transaction.created_at)}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-900">
                    {formatCurrency(transaction.amount, transaction.currency)}
                  </p>
                  <p className={`text-sm px-2 py-1 rounded-full ${
                    transaction.status === 'completed' 
                      ? 'bg-green-100 text-green-800' 
                      : transaction.status === 'pending'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {transaction.status}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;