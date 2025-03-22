import React from 'react';

const TransactionDetailPopup = ({ transaction, onClose, onEdit }) => {
    if (!transaction) return null;

    // Format date for display
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    };

    // Format currency
    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    };

    return (
        <div className="popup-overlay" style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
        }}>
            <div className="popup-content" style={{
                backgroundColor: 'white',
                borderRadius: '8px',
                padding: '20px',
                width: '90%',
                maxWidth: '600px',
                maxHeight: '80vh',
                overflowY: 'auto',
                boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                    <h2 style={{ margin: 0 }}>Transaction Details</h2>
                    <button
                        onClick={onClose}
                        style={{
                            background: 'none',
                            border: 'none',
                            fontSize: '24px',
                            cursor: 'pointer'
                        }}
                    >
                        ×
                    </button>
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <div style={{
                        padding: '15px',
                        backgroundColor: '#f8f8f8',
                        borderRadius: '8px',
                        marginBottom: '15px'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h3 style={{ margin: '0 0 10px 0' }}>{transaction.name}</h3>
                            <span style={{
                                fontSize: '24px',
                                fontWeight: 'bold',
                                color: parseFloat(transaction.amount) < 0 ? '#c62828' : '#2e7d32'
                            }}>
                {formatCurrency(transaction.amount)}
              </span>
                        </div>
                        <div style={{ color: '#666' }}>{formatDate(transaction.date)}</div>
                    </div>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
                        gap: '10px'
                    }}>
                        <div>
                            <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Category</div>
                            <div>{Array.isArray(transaction.category) ? transaction.category[0] : transaction.category || "Uncategorized"}</div>
                        </div>

                        <div>
                            <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Transaction ID</div>
                            <div style={{ wordBreak: 'break-all' }}>{transaction.transaction_id}</div>
                        </div>

                        {transaction.account_id && (
                            <div>
                                <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Account</div>
                                <div>{transaction.account_id}</div>
                            </div>
                        )}

                        {transaction.payment_channel && (
                            <div>
                                <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Payment Method</div>
                                <div>{transaction.payment_channel}</div>
                            </div>
                        )}

                        {transaction.pending !== undefined && (
                            <div>
                                <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Status</div>
                                <div>{transaction.pending ? "Pending" : "Completed"}</div>
                            </div>
                        )}
                    </div>

                    {transaction.location && (
                        <div style={{ marginTop: '15px' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Location</div>
                            <div>{JSON.stringify(transaction.location)}</div>
                        </div>
                    )}
                </div>

                <div style={{ textAlign: 'right' }}>
                    <button
                        onClick={() => onEdit(transaction)}
                        style={{
                            padding: '10px 15px',
                            backgroundColor: '#2196F3',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            marginRight: '10px'
                        }}
                    >
                        Edit Transaction
                    </button>
                    <button
                        onClick={onClose}
                        style={{
                            padding: '10px 15px',
                            backgroundColor: '#f5f5f5',
                            color: 'black',
                            border: '1px solid #ddd',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default TransactionDetailPopup;
