export const formatCurrency = (amount, currency = 'JOD') => {
  if (typeof amount !== 'number') {
    amount = parseFloat(amount) || 0;
  }
  
  if (currency === 'JOD') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'JOD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } else if (currency === 'DINARX') {
    return `${amount.toFixed(2)} DinarX`;
  } else {
    return `${amount.toFixed(2)} ${currency}`;
  }
};

export const formatDate = (date) => {
  if (!date) return '';
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const formatDateTime = (date) => {
  if (!date) return '';
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};