// Utility functions for formatting data

export const formatCurrency = (amount, currency = 'JD') => {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency === 'JD' ? 'USD' : 'USD', // Using USD as proxy for JD
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  
  if (currency === 'JD') {
    return formatter.format(amount).replace('$', 'JD ');
  } else if (currency === 'STABLECOIN') {
    return formatter.format(amount).replace('$', 'SC ');
  }
  
  return formatter.format(amount);
};

export const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatDateShort = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
};

export const formatTime = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatTransactionType = (type) => {
  const types = {
    deposit: 'Deposit',
    withdrawal: 'Withdrawal',
    transfer: 'Transfer',
    exchange: 'Exchange',
  };
  return types[type] || type;
};

export const formatTransactionStatus = (status) => {
  const statuses = {
    pending: 'Pending',
    completed: 'Completed',
    failed: 'Failed',
  };
  return statuses[status] || status;
};

export const getTransactionIcon = (type) => {
  const icons = {
    deposit: '↗',
    withdrawal: '↙',
    transfer: '↔',
    exchange: '⇄',
  };
  return icons[type] || '•';
};

export const getTransactionColor = (type) => {
  const colors = {
    deposit: 'text-green-600',
    withdrawal: 'text-red-600',
    transfer: 'text-blue-600',
    exchange: 'text-yellow-600',
  };
  return colors[type] || 'text-gray-600';
};

export const getStatusColor = (status) => {
  const colors = {
    completed: 'bg-green-100 text-green-800',
    pending: 'bg-yellow-100 text-yellow-800',
    failed: 'bg-red-100 text-red-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
};

export const truncateString = (str, length = 20) => {
  if (str.length <= length) return str;
  return str.substring(0, length) + '...';
};

export const formatPhoneNumber = (phoneNumber) => {
  if (!phoneNumber) return '';
  
  // Remove all non-digit characters
  const cleaned = phoneNumber.replace(/\D/g, '');
  
  // Format as +962 XX XXX XXXX for Jordan
  if (cleaned.startsWith('962')) {
    return `+${cleaned.substring(0, 3)} ${cleaned.substring(3, 5)} ${cleaned.substring(5, 8)} ${cleaned.substring(8)}`;
  }
  
  return phoneNumber;
};

export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePhoneNumber = (phoneNumber) => {
  const phoneRegex = /^(\+962|962|0)?[0-9]{9}$/;
  return phoneRegex.test(phoneNumber.replace(/\s/g, ''));
};

export const formatBalance = (balance) => {
  if (balance >= 1000000) {
    return (balance / 1000000).toFixed(1) + 'M';
  } else if (balance >= 1000) {
    return (balance / 1000).toFixed(1) + 'K';
  }
  return balance.toFixed(2);
};

export const calculatePercentageChange = (current, previous) => {
  if (previous === 0) return 0;
  return ((current - previous) / previous) * 100;
};

export const getTimeAgo = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);
  
  if (diffInSeconds < 60) {
    return 'Just now';
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  } else {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days} day${days > 1 ? 's' : ''} ago`;
  }
};

export const generateTransactionId = () => {
  return 'TXN_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
};

export const formatNumber = (number, decimals = 2) => {
  return Number(number).toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};